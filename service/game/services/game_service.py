import random
import json
import logging

from django.db.models import (
    BooleanField,
    Case,
    Value,
    When,
    Prefetch,
    OuterRef,
    Exists,
    Q,
    Subquery,
    JSONField,
    F,
)
from django.db.models.functions import JSONObject
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models.aggregates import Aggregate
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import exceptions

from .. import models, tasks, util
from .base_service import BaseService

logger = logging.getLogger("game")


class GameService(BaseService):
    def __init__(self, user, adjudication_service=None):
        self.user = user
        self.adjudication_service = adjudication_service

    def list(self, filters=None):
        logger.info(f"GameService.list() called with filters: {filters}")
        filters = filters or {}
        if filters.get("mine"):
            queryset = models.Game.objects.filter(members__user=self.user)
        elif filters.get("can_join"):
            queryset = models.Game.objects.filter(status=models.Game.PENDING).exclude(
                members__user=self.user
            )
        else:
            queryset = models.Game.objects.all()

        is_member_subquery = models.Member.objects.filter(
            game=OuterRef("pk"), user=self.user
        )

        current_phase_subquery = models.Phase.objects.filter(
            game=OuterRef("pk")
        ).order_by("-ordinal")

        # Create a subquery to get phase state options grouped by nation
        phase_state_options = models.PhaseState.objects.filter(
            phase=OuterRef("pk")
        ).annotate(
            nation_options=JSONObject(
                nation=F("member__nation"),
                options=F("options")
            )
        ).values("nation_options")

        # Aggregate the options into a JSON array
        options_subquery = phase_state_options.annotate(
            options_list=JSONBAgg("nation_options")
        ).values("options_list")[:1]

        # Updated subquery to correctly find the current user's phase state in the current active phase
        user_phase_state_subquery = models.PhaseState.objects.filter(
            phase__game=OuterRef("pk"),
            phase__status=models.Phase.ACTIVE,
            member__user=self.user,
        )

        # Active phase subquery
        active_phase_subquery = models.Phase.objects.filter(
            game=OuterRef("pk"), 
            status=models.Phase.ACTIVE
        )

        # Member status subquery - ensure we check both membership and status
        member_status_subquery = models.Member.objects.filter(
            game=OuterRef("pk"),
            user=self.user,
            eliminated=False,
            kicked=False,
        )

        # Prefetch phases with options annotation
        phases_prefetch = Prefetch(
            "phases",
            queryset=models.Phase.objects.annotate(
                options_list=Subquery(options_subquery, output_field=JSONField())
            )
        )

        queryset = queryset.annotate(
            can_join=Case(
                When(
                    Exists(is_member_subquery) & Q(status=models.Game.PENDING),
                    then=Value(False),
                ),
                default=Value(True),
                output_field=BooleanField(),
            ),
            can_leave=Case(
                When(
                    Exists(is_member_subquery) & Q(status=models.Game.PENDING),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            phase_confirmed=Case(
                When(
                    Exists(user_phase_state_subquery.filter(orders_confirmed=True)),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            can_confirm_phase=Case(
                When(
                    Q(status=models.Game.ACTIVE) &
                    Exists(member_status_subquery) &
                    Exists(active_phase_subquery),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).prefetch_related(
            phases_prefetch,
            Prefetch(
                "members",
                queryset=models.Member.objects.annotate(
                    is_current_user=Case(
                        When(user=self.user, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                ),
            ),
        )

        logger.info(f"GameService.list() returning queryset: {queryset}")
        return queryset

    def retrieve(self, game_id):
        logger.info(f"GameService.retrieve() called with game_id: {game_id}")
        queryset = self.list()

        logger.info(f"GameService.retrieve() returning queryset: {queryset}")
        return get_object_or_404(queryset.distinct(), id=game_id)

    @transaction.atomic
    def create(self, data):
        logger.info(f"GameService.create() called with data: {data}")

        variant = models.Variant.objects.filter(id=data["variant"]).first()
        if not variant:
            logger.error(f"GameService.create() variant not found: {data['variant']}")
            raise exceptions.ValidationError(
                detail=f"Variant with name {data['variant']} does not exist."
            )

        with transaction.atomic():
            game = models.Game.objects.create(
                name=data["name"],
                variant=variant,
                nation_assignment=data.get("nation_assignment", models.Game.RANDOM),
            )
            game.members.create(user=self.user)

            # Create a pending phase for the game
            phase = game.phases.create(
                game=game,
                season=variant.start["season"],
                year=variant.start["year"],
                type=variant.start["type"],
                status=models.Phase.PENDING,
            )

            # Create Unit instances for the phase
            for unit_data in variant.start["units"]:
                models.Unit.objects.create(
                    phase=phase,
                    type=unit_data["type"].lower(),
                    nation=unit_data["nation"],
                    province=unit_data["province"],
                )

            # Create SupplyCenter instances for the phase
            for sc_data in variant.start["supply_centers"]:
                models.SupplyCenter.objects.create(
                    phase=phase,
                    nation=sc_data["nation"],
                    province=sc_data["province"],
                )

            # Create a public channel for the game
            models.Channel.objects.create(
                game=game,
                name=f"Public Press",
                private=False,
            )

        logger.info(f"GameService.create() returning game: {game}")
        return game

    def join(self, game_id):
        logger.info(f"GameService.join() called with game_id: {game_id}")

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(f"GameService.join() called when game is not pending. This shouldn't happen.")
            raise exceptions.PermissionDenied(detail="Cannot join a non-pending game.")

        if game.members.filter(user=self.user).exists():
            logger.warning(f"GameService.join() called when user is already a member of the game. This shouldn't happen.")
            raise exceptions.ValidationError(
                detail="User is already a member of the game."
            )

        if game.members.count() >= len(game.variant.nations):
            logger.warning(f"GameService.join() called when game already has the maximum number of players. This shouldn't happen.")
            raise exceptions.ValidationError(
                detail="Game already has the maximum number of players."
            )

        game.members.create(user=self.user)

        logger.info(f"GameService.join() returning game: {game}")
        return game

    def leave(self, game_id):
        logger.info(f"GameService.leave() called with game_id: {game_id}")
        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(f"GameService.leave() called when game is not pending. This shouldn't happen.")
            raise exceptions.PermissionDenied(detail="Cannot leave a non-pending game.")

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(f"GameService.leave() called when user is not a member of the game. This shouldn't happen.")
            raise exceptions.ValidationError(detail="User is not a member of the game.")

        member.delete()

        logger.info(f"GameService.leave() returning game: {game}")
        return game

    def start(self, game_id):
        logger.info(f"GameService.start() called with game_id: {game_id}")

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(f"GameService.start() called when game is not pending. This shouldn't happen.")
            raise exceptions.PermissionDenied(detail="Cannot start a non-pending game.")

        try:
            adjudication_response = self.adjudication_service.start(game)
        except Exception as e:
            logger.error(f"GameService.start() adjudication service failed: {str(e)}")
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        logger.info(f"GameService.start() starting game: {game}")
        with transaction.atomic():
            self._set_nations(game)
            self._create_phase_states(game, adjudication_response["options"])

            current_phase = game.phases.last()
            current_phase.status = models.Phase.ACTIVE
            current_phase.save()

            # Set the game status to active
            game.status = models.Game.ACTIVE
            game.save()

            # Create a resolution task
            self._create_resolution_task(game)

        user_ids = [member.user.id for member in game.members.all()]
        data = {
            "title": "Game Started",
            "body": f"Game '{game.name}' has started!",
            "game_id": game.id,
            "type": "game_start",
        }

        logger.info(f"GameService.start() adding task to notify users: {user_ids}")
        tasks.notify_task.apply_async(args=[user_ids, data], kwargs={})

        logger.info(f"GameService.start() returning game: {game}")
        return game

    def resolve(self, game_id):
        logger.info(f"GameService.resolve() called with game_id: {game_id}")

        game = get_object_or_404(models.Game, id=game_id)

        try:
            adjudication_response = self.adjudication_service.resolve(game)
        except Exception as e:
            logger.error(f"GameService.resolve() adjudication service failed: {str(e)}")
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        phase_data = adjudication_response["phase"]
        options_data = adjudication_response["options"]

        logger.info(f"GameService.resolve() resolving phase: {phase_data}")

        with transaction.atomic():
            # Set the status of the current phase to completed
            current_phase = game.phases.last()
            current_phase.status = models.Phase.COMPLETED
            current_phase.save()

            # Create resolutions for each order
            for resolution in phase_data["resolutions"]:
                province = resolution["province"]
                result = resolution["result"]
                by = resolution.get("by")

                # Find the order for this province
                order = models.Order.objects.filter(
                    phase_state__phase=current_phase,
                    source=province
                ).first()

                if order:
                    # Create or update resolution
                    models.OrderResolution.objects.update_or_create(
                        order=order,
                        defaults={
                            "status": result,
                            "by": by
                        }
                    )

            new_phase = self._create_phase(game, phase_data)

            self._create_phase_states(game, options_data)

            # Create a resolution task
            self._create_resolution_task(game)

        user_ids = [member.user.id for member in game.members.all()]
        data = {
            "title": "Phase Resolved",
            "body": f"Phase '{new_phase.name}' has been resolved!",
            "game_id": game.id,
            "type": "game_resolve",
        }

        logger.info(f"GameService.resolve() adding task to notify users: {user_ids}")
        tasks.notify_task.apply_async(args=[user_ids, data], kwargs={})

        logger.info(f"GameService.resolve() returning game: {game}")
        return game

    def _create_phase(self, game, phase_data):
        variant = game.variant
        phase = game.phases.create(
            game=game,
            season=phase_data["season"],
            year=phase_data["year"],
            type=phase_data["type"],
        )

        for unit_data in phase_data["units"]:
            models.Unit.objects.create(
                phase=phase,
                type=unit_data["type"].lower(),
                nation=unit_data["nation"],
                province=unit_data["province"],
            )

        for sc_data in phase_data["supply_centers"]:
            models.SupplyCenter.objects.create(
                phase=phase,
                nation=sc_data["nation"],
                province=sc_data["province"],
            )

        return phase

    def _set_nations(self, game):
        nations = game.variant.nations
        members = game.members.all().order_by('created_at')
        
        if game.nation_assignment == models.Game.RANDOM:
            # Shuffle nations for random assignment
            nations = list(nations)
            random.shuffle(nations)
        
        # Assign nations to members in either random or ordered fashion
        for member, nation in zip(members, nations):
            member.nation = nation["name"]
            member.save()


    def _create_phase_states(self, game, options_data):
        for member in game.members.all():
            models.PhaseState.objects.create(
                phase=game.current_phase,
                member=member,
                options=json.dumps(options_data[member.nation]),
            )

    def _create_resolution_task(self, game):
        phase_duration_seconds = game.get_phase_duration_seconds()
        scheduled_for = timezone.now() + timedelta(seconds=phase_duration_seconds)
        task_result = tasks.resolve_task.apply_async(
            args=[game.id],
            kwargs={},
            countdown=phase_duration_seconds,
        )
        task = models.Task.objects.get(id=task_result.task_id)
        task.scheduled_for = scheduled_for
        task.save()

        game.resolution_task = task
        game.save()

    def _should_resolve_phase(self, game):
        """
        Check if all active members (not eliminated or kicked) have confirmed their orders.
        """
        current_phase = game.current_phase
        if not current_phase or current_phase.status != models.Phase.ACTIVE:
            return False

        # Get all active members (not eliminated or kicked)
        active_members = game.members.filter(eliminated=False, kicked=False)
        if not active_members.exists():
            return False

        # Check if all active members have confirmed their orders
        confirmed_count = current_phase.phase_states.filter(
            member__in=active_members,
            orders_confirmed=True
        ).count()

        return confirmed_count == active_members.count()

    def confirm_phase(self, game_id):
        logger.info(f"GameService.confirm_phase() called with game_id: {game_id}")

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.ACTIVE:
            logger.warning(f"GameService.confirm_phase() called when game is not active. This shouldn't happen.")
            raise exceptions.ValidationError(detail="Game is not active.")

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(f"GameService.confirm_phase() called when user is not a member of the game. This shouldn't happen.")
            raise exceptions.ValidationError(detail="User is not a member of the game.")

        if member.eliminated:
            logger.warning(f"GameService.confirm_phase() called when user is eliminated from the game. This shouldn't happen.")
            raise exceptions.ValidationError(detail="User is eliminated from the game.")

        if member.kicked:
            logger.warning(f"GameService.confirm_phase() called when user is kicked from the game. This shouldn't happen.")
            raise exceptions.ValidationError(detail="User is kicked from the game.")

        current_phase = game.phases.last()
        if not current_phase:
            logger.warning(f"GameService.confirm_phase() called when no current phase found for the game. This shouldn't happen.")
            raise exceptions.ValidationError(
                detail="No current phase found for the game."
            )

        phase_state = current_phase.phase_states.filter(member=member).first()
        if not phase_state:
            logger.warning(f"GameService.confirm_phase() called when no phase state found for the user. This shouldn't happen.")
            raise exceptions.ValidationError(
                detail="No phase state found for the user."
            )

        phase_state.orders_confirmed = not phase_state.orders_confirmed
        phase_state.save()

        logger.info(f"GameService.confirm_phase() phase confirmed: {phase_state}")

        # Check if all active members have confirmed their orders
        if phase_state.orders_confirmed and self._should_resolve_phase(game):
            logger.info(f"GameService.confirm_phase() all orders confirmed, resolving phase: {game}")
            # Execute the resolution task immediately if it exists
            if game.resolution_task:
                tasks.resolve_task.apply_async(
                    args=[game.id],
                    kwargs={},
                    task_id=game.resolution_task.id,
                    countdown=0  # Execute immediately
                )

        return phase_state
