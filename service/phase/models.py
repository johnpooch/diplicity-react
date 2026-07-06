import json
import logging
from functools import cached_property

import sentry_sdk
from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q, Exists, OuterRef, Count, Prefetch
from django.utils import timezone
from opentelemetry import trace
from common.models import BaseModel
from datetime import timedelta
from common.constants import PhaseStatus, PhaseType, GameStatus, DeadlineMode, OrderType
from adjudication.service import resolve
from member.models import Member
from order.models import OrderResolution, Order
from phase.utils import transform_options, format_time_remaining, format_deadline, build_notification_body
from province.models import Province
from supply_center.models import SupplyCenter
from unit.models import Unit
from victory.utils import check_for_solo_winner
from victory.models import Victory
from email_service.tasks import send_email_notification
from email_service.templates import notification_email
from notification import utils as notification_utils
from notification.tasks import send_notification

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class PhaseQuerySet(models.QuerySet):
    def with_detail_data(self):
        return self.select_related("variant").prefetch_related(
            "units__nation__flag",
            "units__province__parent",
            "units__province__named_coasts",
            "supply_centers__nation__flag",
            "supply_centers__province__parent",
            "supply_centers__province__named_coasts",
            "variant__provinces__parent",
            "variant__nations",
        )

    def with_adjudication_data(self):
        return self.select_related("variant", "game").prefetch_related(
            "supply_centers__province",
            "supply_centers__nation__flag",
            "units__province",
            "units__nation__flag",
            "units__dislodged_by__province",
            "phase_states__member__nation__flag",
            "phase_states__orders__source",
            "phase_states__orders__target",
            "phase_states__orders__aux",
            "phase_states__orders__named_coast",
            "phase_states__orders__resolution",
        )

    def with_canonical_state_data(self):
        return self.prefetch_related(
            "units__nation__flag",
            "units__province",
            "units__dislodged_by__province__parent",
            "supply_centers__nation__flag",
            "supply_centers__province",
            "phase_states__member__nation__flag",
            "phase_states__orders__source",
            "phase_states__orders__target",
            "phase_states__orders__aux",
            "phase_states__orders__named_coast",
        )

    def filter_due_phases(self):
        deadline_passed = (
            Q(scheduled_resolution__isnull=False)
            & Q(scheduled_resolution__lte=timezone.now())
        )
        all_confirmed = ~Exists(
            PhaseState.objects.filter(phase=OuterRef("pk"), has_possible_orders=True, orders_confirmed=False)
        )
        return self.filter(
            Q(status=PhaseStatus.ACTIVE)
            & Q(game__sandbox=False)
            & Q(game__paused_at__isnull=True)
            & ~Q(game__status=GameStatus.COMPLETED)
            & ~Q(game__status=GameStatus.ABANDONED)
            & (deadline_passed | all_confirmed)
        )


class PhaseManager(models.Manager):
    def get_queryset(self):
        return PhaseQuerySet(self.model, using=self._db)

    def with_detail_data(self):
        return self.get_queryset().with_detail_data()

    def with_adjudication_data(self):
        return self.get_queryset().with_adjudication_data()

    def with_canonical_state_data(self):
        return self.get_queryset().with_canonical_state_data()

    def filter_due_phases(self):
        return self.get_queryset().filter_due_phases()

    def resolve_phase(self, phase):
        with tracer.start_as_current_span("phase.manager.resolve_phase") as span:
            span.set_attribute("phase.id", phase.id)
            span.set_attribute("game.id", str(phase.game.id))
            logger.info(f"Manually resolving phase {phase.id} ({phase.name}) for game {phase.game.id}")
            new_phase = self.resolve(phase)
            logger.info(f"Successfully resolved phase {phase.id}")
            return new_phase

    def get_phases_to_resolve(self):
        with tracer.start_as_current_span("phase.manager.get_phases_to_resolve") as span:
            logger.info("Querying phases to resolve")

            with tracer.start_as_current_span("phase.query_due_phases") as query_span:
                phases_to_resolve = list(self.filter_due_phases().with_adjudication_data())
                query_span.set_attribute("phases.found", len(phases_to_resolve))
                logger.info(f"Found {len(phases_to_resolve)} phases to resolve")

            span.set_attribute("phases.to_resolve", len(phases_to_resolve))
            logger.info(f"Identified {len(phases_to_resolve)} phases to resolve")

            return phases_to_resolve

    def resolve_if_due(self, phase_id):
        with tracer.start_as_current_span("phase.manager.resolve_if_due") as span:
            span.set_attribute("phase.id", phase_id)
            with transaction.atomic():
                locked = self.select_for_update().filter(pk=phase_id).first()
                if locked is None:
                    logger.info(f"Phase {phase_id} no longer exists; skipping resolve")
                    return None
                if not self.filter_due_phases().filter(pk=phase_id).exists():
                    logger.info(f"Phase {phase_id} not due on re-check; skipping resolve")
                    return None
                phase = self.with_adjudication_data().get(pk=phase_id)
                logger.info(f"Resolving due phase {phase.id} ({phase.name}) for game {phase.game_id}")
                return self.resolve(phase)

    def resolve_due_phases(self, canary=False):
        with tracer.start_as_current_span("phase.manager.resolve_due_phases") as span:
            logger.info("Starting resolution of due phases")

            phases_to_resolve = self.get_phases_to_resolve()
            total_phases_to_resolve = len(phases_to_resolve)

            resolved_count = 0
            failed_count = 0

            now = timezone.now()
            grace = timedelta(seconds=getattr(settings, "RESOLUTION_CANARY_GRACE_SECONDS", 300))

            for phase in phases_to_resolve:
                if (
                    canary
                    and phase.scheduled_resolution
                    and phase.scheduled_resolution < now - grace
                ):
                    overdue_seconds = (now - phase.scheduled_resolution).total_seconds()
                    logger.error(
                        f"Phase {phase.id} (game {phase.game_id}) overdue by {overdue_seconds:.0f}s; "
                        f"a primary trigger should have resolved it. Capturing canary."
                    )
                    sentry_sdk.capture_message(
                        f"Phase resolution overdue: phase {phase.id} game {phase.game_id} "
                        f"overdue by {overdue_seconds:.0f}s",
                        level="error",
                    )

                logger.info(f"Resolving phase {phase.id} ({phase.name}) for game {phase.game_id}")
                try:
                    if self.resolve_if_due(phase.id) is not None:
                        resolved_count += 1
                        logger.info(f"Successfully resolved phase {phase.id}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to resolve phase {phase.id} ({phase.name}): {e}", exc_info=True)

            result = {
                "resolved": resolved_count,
                "failed": failed_count,
            }

            span.set_attribute("phases.total", total_phases_to_resolve)
            span.set_attribute("phases.resolved", resolved_count)
            span.set_attribute("phases.failed", failed_count)

            logger.info(
                f"Phase resolution complete: {resolved_count} resolved, {failed_count} failed out of {total_phases_to_resolve} phases"
            )
            return result

    def sweep_due_phases(self):
        return self.resolve_due_phases(canary=True)

    def _check_and_apply_nmr_extensions(self, phase):
        not_submitted = phase.phase_states.filter(
            has_possible_orders=True
        ).exclude(
            member__civil_disorder=True
        ).annotate(order_count=Count("orders")).filter(order_count=0).select_related('member')

        members_with_extensions = [
            ps.member for ps in not_submitted
            if ps.member.nmr_extensions_remaining > 0
        ]

        if not members_with_extensions:
            return None

        new_resolution = phase.game.get_scheduled_resolution(phase.type)
        if not new_resolution:
            return None

        phase.scheduled_resolution = new_resolution
        phase.save()

        for member in members_with_extensions:
            member.nmr_extensions_remaining -= 1
        Member.objects.bulk_update(members_with_extensions, ['nmr_extensions_remaining'])

        logger.info(
            f"Applied NMR extensions for {len(members_with_extensions)} members in phase {phase.id}"
        )

        deadline_str = format_deadline(phase.scheduled_resolution, phase.game.fixed_deadline_timezone)

        def send_notifications():
            for member in members_with_extensions:
                if member.user_id is None:
                    continue
                notification_utils.send_notification_to_users(
                    user_ids=[member.user_id],
                    title=phase.game.name,
                    body=f"You did not submit orders and used an automatic extension ({member.nmr_extensions_remaining} remaining). The current phase is extended until {deadline_str}.",
                    notification_type="nmr_extension_used",
                    data={"game_id": str(phase.game.id), "link": f"{settings.FRONTEND_URL}/game/{phase.game.id}"},
                )

            extension_ids = {m.user_id for m in members_with_extensions if m.user_id is not None}
            other_ids = [
                user_id for user_id in phase.game.notification_user_ids()
                if user_id not in extension_ids
            ]
            if other_ids:
                notification_utils.send_notification_to_users(
                    user_ids=other_ids,
                    title=phase.game.name,
                    body=f"Some player(s) did not submit orders and used an extension. The current phase is extended until {deadline_str}.",
                    notification_type="nmr_extension_applied",
                    data={"game_id": str(phase.game.id), "link": f"{settings.FRONTEND_URL}/game/{phase.game.id}"},
                )

        transaction.on_commit(send_notifications)

        return members_with_extensions

    def send_deadline_warnings(self):
        WARNING_THRESHOLDS = {
            3600: 900,
            12 * 3600: 3600,
            24 * 3600: 3600,
            48 * 3600: 7200,
            72 * 3600: 7200,
            96 * 3600: 7200,
            168 * 3600: 14400,
            336 * 3600: 14400,
        }

        def get_warning_threshold(duration_seconds):
            if not duration_seconds:
                return 3600
            for phase_duration, warning in sorted(WARNING_THRESHOLDS.items()):
                if duration_seconds <= phase_duration:
                    return warning
            return 14400

        with tracer.start_as_current_span("phase.manager.send_deadline_warnings") as span:
            now = timezone.now()

            active_phases = self.filter(
                status=PhaseStatus.ACTIVE,
                game__sandbox=False,
                game__paused_at__isnull=True,
                scheduled_resolution__isnull=False,
            ).exclude(
                Q(game__status=GameStatus.COMPLETED) | Q(game__status=GameStatus.ABANDONED)
            ).select_related('game').prefetch_related(
                'phase_states__member__user',
                'phase_states__member__nation',
                'phase_states__orders',
                Prefetch('units', queryset=Unit.objects.select_related('nation'), to_attr='prefetched_units'),
                Prefetch('supply_centers', queryset=SupplyCenter.objects.select_related('nation'), to_attr='prefetched_supply_centers'),
            )

            notifications_sent = 0

            for phase in active_phases:
                duration_seconds = phase.game.get_effective_phase_duration_seconds(phase.type)
                warning_threshold = get_warning_threshold(duration_seconds)
                time_until_deadline = (phase.scheduled_resolution - now).total_seconds()

                if time_until_deadline <= 0 or time_until_deadline > warning_threshold:
                    continue

                is_fixed_time = phase.game.deadline_mode == DeadlineMode.FIXED_TIME
                time_left = format_time_remaining(time_until_deadline)

                units_by_nation = {}
                for unit in phase.prefetched_units:
                    units_by_nation[unit.nation_id] = units_by_nation.get(unit.nation_id, 0) + 1

                sc_by_nation = {}
                for sc in phase.prefetched_supply_centers:
                    sc_by_nation[sc.nation_id] = sc_by_nation.get(sc.nation_id, 0) + 1

                warned_states = []

                for ps in phase.phase_states.all():
                    if not ps.has_possible_orders:
                        continue
                    if ps.deadline_warning_sent_for == phase.scheduled_resolution:
                        continue

                    nation_id = ps.member.nation_id
                    unit_count = units_by_nation.get(nation_id, 0)

                    if phase.type == PhaseType.ADJUSTMENT:
                        sc_count = sc_by_nation.get(nation_id, 0)
                        total_units = abs(sc_count - unit_count)
                    else:
                        total_units = unit_count

                    if total_units == 0:
                        continue

                    body = build_notification_body(
                        ps.orders_confirmed, is_fixed_time, len(ps.orders.all()), total_units, time_left,
                        ps.member.nmr_extensions_remaining,
                    )
                    if body is None:
                        continue

                    if ps.member.user_id is None:
                        continue

                    link = f"{settings.FRONTEND_URL}/game/{phase.game.id}"

                    notification_utils.send_notification_to_users(
                        user_ids=[ps.member.user_id],
                        title=phase.game.name,
                        body=body,
                        notification_type="deadline_warning",
                        data={"game_id": str(phase.game.id), "link": link},
                    )
                    send_email_notification.defer(
                        user_ids=[ps.member.user_id],
                        subject=f"{phase.game.name} — Deadline Approaching",
                        html=notification_email(
                            title=phase.game.name,
                            body=body,
                            link=link,
                            link_text="Submit Orders",
                        ),
                    )
                    ps.deadline_warning_sent_for = phase.scheduled_resolution
                    warned_states.append(ps)
                    notifications_sent += 1
                    logger.info(f"Sent deadline warning to user {ps.member.user_id} for game {phase.game.name}")

                if warned_states:
                    PhaseState.objects.bulk_update(warned_states, ["deadline_warning_sent_for"])

            span.set_attribute("notifications.sent", notifications_sent)
            logger.info(f"Sent {notifications_sent} deadline warning notification(s)")

            return {"notifications_sent": notifications_sent}

    def _set_orders_outcome(self, phase):
        base_qs = phase.phase_states.filter(
            has_possible_orders=True
        ).annotate(order_count=Count("orders"))

        received_ids = list(base_qs.filter(order_count__gt=0).values_list("id", flat=True))
        nmr_ids = list(base_qs.filter(order_count=0).values_list("id", flat=True))

        if received_ids:
            PhaseState.objects.filter(id__in=received_ids).update(
                orders_outcome=PhaseState.OrdersOutcome.RECEIVED
            )
        if nmr_ids:
            PhaseState.objects.filter(id__in=nmr_ids).update(
                orders_outcome=PhaseState.OrdersOutcome.NMR
            )

    def _check_civil_disorder(self, phase):
        if phase.game.sandbox:
            return []
        if phase.type != PhaseType.MOVEMENT:
            return []

        current_nmr_members = []
        for phase_state in phase.phase_states.select_related("member").all():
            if phase_state.orders_outcome != PhaseState.OrdersOutcome.NMR:
                continue
            member = phase_state.member
            if member.civil_disorder or member.eliminated or member.kicked:
                continue
            current_nmr_members.append(member)

        if not current_nmr_members:
            return []

        prev_movement_states = (
            PhaseState.objects.filter(
                member__in=current_nmr_members,
                phase__game=phase.game,
                phase__type=PhaseType.MOVEMENT,
                phase__status=PhaseStatus.COMPLETED,
                phase__ordinal__lt=phase.ordinal,
                has_possible_orders=True,
            )
            .order_by("member_id", "-phase__ordinal")
        )

        latest_prev_by_member = {}
        for ps in prev_movement_states:
            if ps.member_id not in latest_prev_by_member:
                latest_prev_by_member[ps.member_id] = ps

        newly_cd_members = [
            m for m in current_nmr_members
            if m.id in latest_prev_by_member
            and latest_prev_by_member[m.id].orders_outcome == PhaseState.OrdersOutcome.NMR
        ]

        if not newly_cd_members:
            return []

        for m in newly_cd_members:
            m.civil_disorder = True
        Member.objects.bulk_update(newly_cd_members, ["civil_disorder"])

        cd_user_ids = [m.user_id for m in newly_cd_members if m.user_id is not None]
        self._remove_from_staging_games(cd_user_ids)

        user_ids = phase.game.notification_user_ids()
        nation_names = ", ".join(
            m.nation.name for m in newly_cd_members if m.nation is not None
        )

        def send_notifications():
            if user_ids:
                link = f"{settings.FRONTEND_URL}/game/{phase.game.id}"
                body = f"{nation_names} entered civil disorder."

                notification_utils.send_notification_to_users(
                    user_ids=user_ids,
                    title="Civil Disorder",
                    body=body,
                    notification_type="civil_disorder",
                    data={"game_id": str(phase.game.id)},
                )
                send_email_notification.defer(
                    user_ids=user_ids,
                    subject=f"{phase.game.name} — Civil Disorder",
                    html=notification_email(
                        title="Civil Disorder",
                        body=body,
                        link=link,
                    ),
                )

        transaction.on_commit(send_notifications)

        return newly_cd_members

    def _remove_from_staging_games(self, user_ids):
        if not user_ids:
            return

        staging_members = list(
            Member.objects.filter(
                user_id__in=user_ids,
                game__status=GameStatus.PENDING,
            )
            .exclude(game__created_by_id=F("user_id"))
            .select_related("game")
        )

        if not staging_members:
            return

        games_by_user = {}
        game_ids = set()
        for m in staging_members:
            games_by_user.setdefault(m.user_id, []).append(m.game)
            game_ids.add(m.game_id)

        Member.objects.filter(id__in=[m.id for m in staging_members]).delete()

        for user_id, games in games_by_user.items():
            game_names = ", ".join(g.name for g in games)
            send_notification.defer(
                user_ids=[user_id],
                title="Removed from staging games",
                body=f"You were removed from {game_names} because you entered civil disorder in an active game.",
                notification_type="removed_from_staging",
            )

        from game.models import Game
        for game in Game.objects.filter(id__in=game_ids, status=GameStatus.PENDING):
            game.delete_if_empty_pending()

    def _check_eliminations(self, previous_phase, new_phase):
        units_by_nation = {}
        for unit in new_phase.units.all():
            units_by_nation[unit.nation_id] = units_by_nation.get(unit.nation_id, 0) + 1

        sc_by_nation = {}
        for sc in new_phase.supply_centers.all():
            sc_by_nation[sc.nation_id] = sc_by_nation.get(sc.nation_id, 0) + 1

        candidates = list(
            previous_phase.game.members.filter(
                eliminated=False, kicked=False, nation__isnull=False
            ).select_related("user", "nation")
        )

        newly_eliminated = [
            m for m in candidates
            if units_by_nation.get(m.nation_id, 0) == 0
            and sc_by_nation.get(m.nation_id, 0) == 0
        ]

        if not newly_eliminated:
            return

        for m in newly_eliminated:
            m.eliminated = True
        Member.objects.bulk_update(newly_eliminated, ["eliminated"])

        game = previous_phase.game

        for member in newly_eliminated:
            if member.user_id is None:
                continue
            send_notification.defer(
                user_ids=[member.user_id],
                title=game.name,
                body="You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!",
                notification_type="elimination",
                data={"game_id": str(game.id), "link": f"{settings.FRONTEND_URL}/game/{game.id}"},
            )

    def _check_abandonment(self, game):
        if game.sandbox:
            return False

        active_members = list(game.members.filter(eliminated=False, kicked=False))
        if not active_members:
            return False

        return all(m.civil_disorder for m in active_members)

    def resolve(self, phase):
        with tracer.start_as_current_span("phase.manager.resolve") as span:
            span.set_attribute("phase.id", phase.id)
            span.set_attribute("game.id", str(phase.game.id))

            extension_members = self._check_and_apply_nmr_extensions(phase)
            if extension_members:
                return phase

            self._check_civil_disorder(phase)
            adjudication_data = resolve(phase)

            with tracer.start_as_current_span("phase.transaction_atomic"):
                with transaction.atomic():
                    self._set_orders_outcome(phase)
                    self._check_civil_disorder(phase)
                    new_phase = self.create_from_adjudication_data(phase, adjudication_data)
                    self._check_eliminations(phase, new_phase)

                    victory = Victory.objects.try_create_victory(new_phase)

                    if victory:
                        new_phase.game.status = GameStatus.COMPLETED
                        new_phase.game.finished_at = timezone.now()
                        new_phase.game.save()

                        new_phase.status = PhaseStatus.COMPLETED
                        new_phase.scheduled_resolution = None
                        new_phase.save()
                    elif self._check_abandonment(new_phase.game):
                        new_phase.game.status = GameStatus.ABANDONED
                        new_phase.game.finished_at = timezone.now()
                        new_phase.game.save()

                        new_phase.status = PhaseStatus.COMPLETED
                        new_phase.scheduled_resolution = None
                        new_phase.save()

                    return new_phase

    def create_from_adjudication_data(self, previous_phase, adjudication_data):
        with tracer.start_as_current_span("phase.create_from_adjudication_data") as span:
            span.set_attribute("previous_phase.id", previous_phase.id)
            span.set_attribute("new_phase.ordinal", previous_phase.ordinal + 1)

            if previous_phase.game.status in (GameStatus.COMPLETED, GameStatus.ABANDONED):
                logger.warning(f"Skipping phase creation - game {previous_phase.game.id} is {previous_phase.game.status}")
                return previous_phase

            logger.info(
                f"Creating new phase from adjudication data for previous phase {previous_phase.id} ({previous_phase.name})"
            )
            logger.debug(f"Adjudication data keys: {list(adjudication_data.keys())}")

            try:
                # Build lookup dictionaries once to avoid N+1 queries
                variant = previous_phase.variant
                province_lookup = {p.province_id: p for p in variant.provinces.all()}
                nation_lookup = {n.name: n for n in variant.nations.all()}

                # Process order resolutions
                with tracer.start_as_current_span("phase.create_order_resolutions") as resolutions_span:
                    existing_orders = list(previous_phase.all_orders)
                    order_count = len(existing_orders)

                    order_ids = [order.id for order in existing_orders]
                    OrderResolution.objects.filter(order_id__in=order_ids).delete()

                    unit_nation_by_province = {
                        unit.province.province_id: unit.nation
                        for unit in previous_phase.units.all()
                    }
                    phase_state_by_nation_name = {
                        ps.member.nation.name: ps
                        for ps in previous_phase.phase_states.all()
                    }
                    existing_order_provinces = {order.source.province_id for order in existing_orders}

                    implicit_orders_to_create = []
                    implicit_resolution_pairs = []
                    for resolution_data in adjudication_data["resolutions"]:
                        if resolution_data["result"] != "OK" and resolution_data["province"] not in existing_order_provinces:
                            source_province = province_lookup.get(resolution_data["province"])
                            nation = unit_nation_by_province.get(resolution_data["province"])
                            if source_province and nation:
                                phase_state = phase_state_by_nation_name.get(nation.name)
                                if phase_state:
                                    implicit_orders_to_create.append(
                                        Order(
                                            phase_state=phase_state,
                                            source=source_province,
                                            order_type=OrderType.HOLD,
                                            is_implicit=True,
                                        )
                                    )
                                    implicit_resolution_pairs.append(resolution_data)

                    resolutions_to_create = []

                    if implicit_orders_to_create:
                        created_implicit_orders = Order.objects.bulk_create(implicit_orders_to_create)
                        logger.info(f"Created {len(created_implicit_orders)} implicit Hold orders for failed resolutions")
                        for implicit_order, resolution_data in zip(created_implicit_orders, implicit_resolution_pairs):
                            by_province = province_lookup.get(resolution_data["by"]) if resolution_data["by"] else None
                            resolutions_to_create.append(
                                OrderResolution(
                                    order=implicit_order,
                                    status=resolution_data["result"],
                                    by=by_province,
                                )
                            )

                    for order in existing_orders:
                        resolution_data = next(
                            (r for r in adjudication_data["resolutions"] if r["province"] == order.source.province_id),
                            None,
                        )
                        if resolution_data:
                            by_province = province_lookup.get(resolution_data["by"]) if resolution_data["by"] else None
                            resolutions_to_create.append(
                                OrderResolution(
                                    order=order,
                                    status=resolution_data["result"],
                                    by=by_province,
                                )
                            )
                            logger.debug(f"Prepared resolution for order {order.id}: {resolution_data['result']}")
                        else:
                            logger.warning(
                                f"No resolution found for order {order.id} in province {order.source.province_id}"
                            )

                    OrderResolution.objects.bulk_create(resolutions_to_create)
                    resolutions_count = len(resolutions_to_create)

                    resolutions_span.set_attribute("order_count", order_count)
                    resolutions_span.set_attribute("resolutions_created", resolutions_count)
                    logger.info(f"Created {resolutions_count} order resolutions")

                # Calculate next phase details
                scheduled_resolution = previous_phase.game.get_scheduled_resolution(
                    adjudication_data["type"],
                    reference_time=previous_phase.scheduled_resolution,
                )
                new_ordinal = previous_phase.ordinal + 1

                logger.info(
                    f"Creating new phase {new_ordinal} ({adjudication_data['season']} {adjudication_data['year']}, {adjudication_data['type']})"
                )

                # Create the new phase
                with tracer.start_as_current_span("phase.create_new_phase") as new_phase_span:
                    new_phase = self.create(
                        game=previous_phase.game,
                        variant=previous_phase.variant,
                        ordinal=new_ordinal,
                        season=adjudication_data["season"],
                        year=adjudication_data["year"],
                        type=adjudication_data["type"],
                        options=adjudication_data["options"],
                        status=PhaseStatus.ACTIVE,
                        scheduled_resolution=scheduled_resolution,
                    )
                    new_phase_span.set_attribute("phase.id", new_phase.id)
                    new_phase_span.set_attribute("phase.ordinal", new_ordinal)
                    new_phase_span.set_attribute("phase.season", adjudication_data["season"])
                    new_phase_span.set_attribute("phase.year", adjudication_data["year"])
                    new_phase_span.set_attribute("phase.type", adjudication_data["type"])

                logger.info(f"Created new phase {new_phase.id} scheduled for resolution at {scheduled_resolution}")

                # Create supply centers
                with tracer.start_as_current_span("phase.create_supply_centers") as sc_span:
                    supply_centers_to_create = []
                    for supply_center in adjudication_data["supply_centers"]:
                        province = province_lookup.get(supply_center["province"])
                        nation = nation_lookup.get(supply_center["nation"])
                        if province and nation:
                            supply_centers_to_create.append(
                                SupplyCenter(
                                    province=province,
                                    nation=nation,
                                    phase=new_phase,
                                )
                            )
                        else:
                            logger.error(
                                f"Failed to find province {supply_center['province']} or nation {supply_center['nation']}"
                            )

                    # Bulk create all supply centers
                    SupplyCenter.objects.bulk_create(supply_centers_to_create)
                    supply_centers_count = len(supply_centers_to_create)

                    sc_span.set_attribute("supply_centers_count", supply_centers_count)
                    logger.info(f"Created {supply_centers_count} supply centers")

                # Create units
                with tracer.start_as_current_span("phase.create_units") as units_span:
                    # Build a lookup for previous phase units by province_id to avoid N+1 queries
                    previous_units_by_province = {
                        u.province.province_id: u for u in previous_phase.units.select_related("province").all()
                    }

                    units_to_create = []
                    for unit in adjudication_data["units"]:
                        logger.info(
                            f"Preparing unit {unit['type']} for nation {unit['nation']} in province {unit['province']}"
                        )

                        is_dislodged = unit.get("dislodged", False)

                        dislodged_by_id = unit.get("dislodged_by", None)
                        dislodged_by_unit = None

                        if is_dislodged and dislodged_by_id:
                            dislodged_by_unit = previous_units_by_province.get(dislodged_by_id)
                            if not dislodged_by_unit:
                                logger.warning(
                                    f"Unit {unit['province']} is dislodged but dislodger {dislodged_by_id} not found in previous phase"
                                )
                        elif is_dislodged:
                            logger.info(
                                f"Unit {unit['province']} is dislodged but no dislodger information available (convoy case)"
                            )

                        province = province_lookup.get(unit["province"])
                        nation = nation_lookup.get(unit["nation"])
                        if province and nation:
                            units_to_create.append(
                                Unit(
                                    type=unit["type"],
                                    nation=nation,
                                    province=province,
                                    phase=new_phase,
                                    dislodged=is_dislodged,
                                    dislodged_by=dislodged_by_unit,
                                )
                            )
                        else:
                            logger.error(f"Failed to find province {unit['province']} or nation {unit['nation']}")

                    # Bulk create all units
                    Unit.objects.bulk_create(units_to_create)
                    units_count = len(units_to_create)

                    units_span.set_attribute("units_count", units_count)
                    logger.info(f"Created {units_count} units")

                # Create phase states
                with tracer.start_as_current_span("phase.create_phase_states") as ps_span:
                    nations_with_orders = new_phase.nations_with_possible_orders

                    # Prefetch member nations to avoid N+1
                    members = list(new_phase.game.members.select_related("nation").all())

                    phase_states_to_create = []
                    for member in members:
                        phase_states_to_create.append(
                            new_phase.phase_states.model(
                                member=member,
                                phase=new_phase,
                                has_possible_orders=member.nation.name in nations_with_orders,
                                orders_confirmed=member.civil_disorder,
                            )
                        )

                    # Bulk create all phase states
                    new_phase.phase_states.model.objects.bulk_create(phase_states_to_create)
                    phase_states_count = len(phase_states_to_create)

                    ps_span.set_attribute("phase_states_count", phase_states_count)
                    logger.info(f"Created {phase_states_count} phase states for game members")

                # Mark previous phase as completed
                with tracer.start_as_current_span("phase.mark_previous_complete") as complete_span:
                    complete_span.set_attribute("previous_phase.id", previous_phase.id)
                    previous_phase.status = PhaseStatus.COMPLETED
                    previous_phase.save()
                    logger.info(f"Marked previous phase {previous_phase.id} as completed")

                logger.info(f"Successfully created new phase {new_phase.id} from adjudication data")
                return new_phase

            except Exception as e:
                logger.error(
                    f"Failed to create phase from adjudication data for phase {previous_phase.id}: {e}", exc_info=True
                )
                raise


class Phase(BaseModel):

    objects = PhaseManager()

    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="phases", null=True, blank=True)
    variant = models.ForeignKey(
        "variant.Variant", on_delete=models.CASCADE, related_name="phases", null=True, blank=True
    )
    ordinal = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=20, choices=PhaseStatus.STATUS_CHOICES, default=PhaseStatus.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    type = models.CharField(max_length=10)
    scheduled_resolution = models.DateTimeField(null=True, blank=True)
    resolution_job_id = models.BigIntegerField(null=True, blank=True, editable=False)
    options = models.JSONField(default=dict)

    class Meta:
        ordering = ["ordinal"]

    def __str__(self):
        return f"{self.name} ({self.game.name if self.game else '-'})"

    @property
    def name(self):
        return f"{self.season} {self.year}, {self.type}"

    @property
    def remaining_time(self):
        if self.scheduled_resolution and self.status == PhaseStatus.ACTIVE:
            delta = self.scheduled_resolution - timezone.now()
            return max(delta, timedelta(seconds=0))
        return None

    @property
    def remaining_time_seconds(self):
        if self.remaining_time:
            return self.remaining_time.total_seconds()
        return None

    @property
    def all_orders(self):
        return [order for phase_state in self.phase_states.all() for order in phase_state.orders.all()]

    @cached_property
    def transformed_options(self):
        return transform_options(self.options or {})

    @property
    def nations_with_possible_orders(self):
        nations = set()
        for nation, options in (self.transformed_options or {}).items():
            if any(province_data for province_data in options.values()):
                nations.add(nation)
        return nations

    @property
    def phase_states_with_possible_orders(self):
        nations = self.nations_with_possible_orders
        logger.info(f"Nations with possible orders: {nations}")
        return [phase_state for phase_state in self.phase_states.all() if phase_state.member.nation.name in nations]

    @property
    def should_resolve_immediately(self):
        logger.info(f"Checking if phase {self.id} should resolve immediately")
        return all(phase_state.orders_confirmed for phase_state in self.phase_states_with_possible_orders)

    @property
    def previous_phase_id(self):
        if not self.game:
            return None
        return (
            Phase.objects.filter(game=self.game, ordinal__lt=self.ordinal)
            .order_by("-ordinal")
            .values_list("id", flat=True)
            .first()
        )

    @property
    def next_phase_id(self):
        if not self.game:
            return None
        return (
            Phase.objects.filter(game=self.game, ordinal__gt=self.ordinal)
            .order_by("ordinal")
            .values_list("id", flat=True)
            .first()
        )

    def revert_to_this_phase(self):

        logger.info(f"Reverting game {self.game.id} to phase {self.id} ({self.name})")

        if self.game.status == GameStatus.COMPLETED:
            logger.error(f"Cannot revert phase {self.id} - game {self.game.id} has ended")
            raise ValueError("Cannot revert phases in an ended game")

        later_phases = self.game.phases.filter(ordinal__gt=self.ordinal)
        later_phases_count = later_phases.count()
        logger.info(f"Deleting {later_phases_count} phases after phase {self.ordinal}")
        later_phases.delete()

        orders_count = Order.objects.filter(phase_state__phase=self).count()
        logger.info(f"Deleting {orders_count} orders for phase {self.id}")
        Order.objects.filter(phase_state__phase=self).delete()

        logger.info(f"Reactivating phase {self.id} with new scheduled resolution")
        self.status = PhaseStatus.ACTIVE
        self.scheduled_resolution = self.game.get_scheduled_resolution(self.type)
        self.save()

        phase_states_count = self.phase_states.count()
        logger.info(f"Resetting orders_confirmed to False for {phase_states_count} phase states")
        self.phase_states.update(orders_confirmed=False)

        logger.info(f"Successfully reverted game {self.game.id} to phase {self.id}")


class PhaseState(BaseModel):
    class OrdersOutcome(models.TextChoices):
        RECEIVED = "received"
        NMR = "nmr"

    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="phase_states")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_states")
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    has_possible_orders = models.BooleanField(default=False)
    deadline_warning_sent_for = models.DateTimeField(null=True, blank=True)
    orders_outcome = models.CharField(
        max_length=8, choices=OrdersOutcome, null=True, blank=True, default=None
    )

    def __str__(self):
        username = self.member.user.username if self.member.user else "Deleted User"
        return f"{username} - {self.phase.name}"

    def max_allowed_adjustment_orders(self):
        if self.phase.type != PhaseType.ADJUSTMENT:
            return float("inf")

        nation = self.member.nation
        supply_centers_count = self.phase.supply_centers.filter(nation=nation).count()
        units_count = self.phase.units.filter(nation=nation).count()
        return abs(supply_centers_count - units_count)

    def get_orderable_provinces(self, provinces):

        options = self.phase.transformed_options
        nation = self.member.nation
        orderable_ids = list(options[nation.name].keys())

        if isinstance(provinces, dict):
            province_ids = [p.id for p in provinces.values() if p.province_id in orderable_ids]
            base_provinces = Province.objects.filter(id__in=province_ids)
        else:
            base_provinces = provinces.filter(province_id__in=orderable_ids)

        base_provinces = base_provinces.select_related("parent").prefetch_related("named_coasts")

        if self.phase.type == PhaseType.ADJUSTMENT:
            max_orders = self.max_allowed_adjustment_orders()
            current_orders = self.orders.count()

            if current_orders >= max_orders:
                provinces_with_orders = self.orders.values_list("source__province_id", flat=True)
                return base_provinces.filter(province_id__in=provinces_with_orders)

        return base_provinces

    @property
    def orderable_provinces(self):
        provinces = self.phase.variant.provinces.all()
        return self.get_orderable_provinces(provinces)
