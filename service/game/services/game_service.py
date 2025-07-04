import random
import json
import logging
import time
from django.db import connection, reset_queries
from functools import wraps

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import exceptions

from .. import models, tasks
from .base_service import BaseService

logger = logging.getLogger("game")


def log_performance(func_name):
    """Decorator to log performance metrics for game service methods."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Reset query count and start timing
            reset_queries()
            start_time = time.time()

            # Execute the function
            result = func(self, *args, **kwargs)

            # Log performance metrics
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            query_count = len(connection.queries)
            total_query_time = sum(float(q["time"]) for q in connection.queries) * 1000

            logger.info(
                f"{func_name} performance: {response_time:.2f}ms, {query_count} queries, {total_query_time:.2f}ms query time"
            )

            # Log each query for analysis
            for i, query in enumerate(connection.queries):
                query_time = float(query["time"]) * 1000
                logger.info(
                    f"Query {i + 1}: {query_time:.2f}ms - {query['sql'][:100]}..."
                )

            return result

        return wrapper

    return decorator


class GameService(BaseService):
    def __init__(self, user, adjudication_service=None):
        self.user = user
        self.adjudication_service = adjudication_service

    @log_performance("Game list")
    def list(self, filters=None):
        logger.info("GameService.list() called with filters: %s", filters)
        filters = filters or {}

        game_queryset = models.Game.objects.get_queryset()

        if filters.get("mine"):
            game_queryset = game_queryset.includes_user(self.user)
        elif filters.get("can_join"):
            game_queryset = game_queryset.joinable(self.user)

        game_queryset = game_queryset.with_variant().with_members().with_phases()

        result = []
        for game in game_queryset:
            game_data = self._build_game_data(game, is_list_view=True)
            result.append(game_data)

        return result

    @log_performance("Game retrieve")
    def retrieve(self, game_id):
        logger.info("GameService.retrieve() called with game_id: %s", game_id)

        game_queryset = (
            models.Game.objects.filter(id=game_id)
            .with_variant()
            .with_members()
            .with_phases()
        )
        game = game_queryset.first()

        if not game:
            raise exceptions.NotFound(detail="Game not found.")

        return self._build_game_data(game, is_list_view=False)

    def _build_game_data(self, game, is_list_view=False):
        """Build game data dictionary with common logic for both list and retrieve."""
        phases = game.phases.all()
        members = game.members.all()
        current_phase = max(phases, key=lambda p: p.ordinal)
        current_phase_states = current_phase.phase_states.all()

        user_member = next(
            (m for m in members if m.user.username == self.user.username), None
        )

        user_current_phase_state = next(
            (ps for ps in current_phase_states if ps.member == user_member), None
        )

        phase_confirmed = (
            user_current_phase_state.orders_confirmed
            if user_current_phase_state
            else False
        )

        can_confirm_phase = (
            game.status == models.Game.ACTIVE
            and current_phase is not None
            and current_phase.status == models.Phase.ACTIVE
            and user_member is not None
            and not user_member.eliminated
            and not user_member.kicked
        )

        # Build base game data
        game_data = {
            "id": game.id,
            "name": game.name,
            "status": game.status,
            "movement_phase_duration": game.movement_phase_duration,
            "nation_assignment": game.nation_assignment,
            "phases": [self._get_phase_data(phase, game.variant) for phase in phases],
            "members": self._build_members_data(members),
            "variant": game.variant,
            "phase_confirmed": phase_confirmed,
            "can_confirm_phase": can_confirm_phase,
        }

        # Add list-specific or retrieve-specific fields
        if is_list_view:
            game_data.update(
                {
                    "can_join": True,
                    "can_leave": False,
                }
            )
        else:
            game_data.update(
                {
                    "can_join": (
                        game.status == models.Game.PENDING
                        and game.members.count() < len(game.variant.nations)
                        and not user_member
                    ),
                    "can_leave": game.status == models.Game.PENDING and user_member,
                }
            )

        return game_data

    def _build_members_data(self, members):
        """Build members data array with common logic."""
        return [
            {
                "id": member.id,
                "username": member.user.username,
                "name": member.user.profile.name,
                "picture": member.user.profile.picture,
                "nation": member.nation,
                "is_current_user": member.user.username == self.user.username,
            }
            for member in members
        ]

    def _get_phase_data(self, phase, variant):
        units = phase.units.all()
        units_data = []
        for unit in units:
            province = next(
                (p for p in variant.provinces if p["id"] == unit.province), None
            )
            if not province:
                raise Exception(
                    f"Province {unit.province} not found in variant {variant.id}"
                )
            units_data.append(
                {
                    "type": unit.type,
                    "nation": {"name": unit.nation},
                    "province": province,
                }
            )

        supply_centers = phase.supply_centers.all()
        supply_centers_data = []
        for sc in supply_centers:
            province = next(
                (p for p in variant.provinces if p["id"] == sc.province), None
            )
            if not province:
                raise Exception(
                    f"Province {sc.province} not found in variant {variant.id}"
                )
            supply_centers_data.append(
                {
                    "province": province,
                    "nation": {"name": sc.nation},
                }
            )

        return {
            "id": phase.id,
            "ordinal": phase.ordinal,
            "season": phase.season,
            "year": phase.year,
            "name": f"{phase.season} {phase.year}",
            "type": phase.type,
            "remaining_time": phase.remaining_time,
            "units": units_data,
            "supply_centers": supply_centers_data,
            "options": phase.options_dict,
        }

    @transaction.atomic
    def create(self, data):
        logger.info("GameService.create() called with data: %s", data)

        variant = models.Variant.objects.filter(id=data["variant"]).first()
        if not variant:
            logger.error("GameService.create() variant not found: %s", data["variant"])
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

        logger.info("GameService.create() returning game: %s", game)
        return game

    def join(self, game_id):
        logger.info("GameService.join() called with game_id: %s", game_id)

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(
                f"GameService.join() called when game is not pending. This shouldn't happen."
            )
            raise exceptions.PermissionDenied(detail="Cannot join a non-pending game.")

        if game.members.filter(user=self.user).exists():
            logger.warning(
                f"GameService.join() called when user is already a member of the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(
                detail="User is already a member of the game."
            )

        if game.members.count() >= len(game.variant.nations):
            logger.warning(
                f"GameService.join() called when game already has the maximum number of players. This shouldn't happen."
            )
            raise exceptions.ValidationError(
                detail="Game already has the maximum number of players."
            )

        game.members.create(user=self.user)

        logger.info("GameService.join() returning game: %s", game)
        return game

    def leave(self, game_id):
        logger.info("GameService.leave() called with game_id: %s", game_id)
        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(
                f"GameService.leave() called when game is not pending. This shouldn't happen."
            )
            raise exceptions.PermissionDenied(detail="Cannot leave a non-pending game.")

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(
                f"GameService.leave() called when user is not a member of the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(detail="User is not a member of the game.")

        member.delete()

        logger.info("GameService.leave() returning game: %s", game)
        return game

    def start(self, game_id):
        logger.info("GameService.start() called with game_id: %s", game_id)

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            logger.warning(
                "GameService.start() called when game is not pending. This shouldn't happen."
            )
            raise exceptions.PermissionDenied(detail="Cannot start a non-pending game.")

        try:
            adjudication_response = self.adjudication_service.start(game)
        except Exception as e:
            logger.error("GameService.start() adjudication service failed: %s", str(e))
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        logger.info("GameService.start() starting game: %s", game)
        with transaction.atomic():
            self._set_nations(game)
            self._create_phase_states(game)

            options_data = adjudication_response["options"]

            current_phase = game.phases.last()
            current_phase.status = models.Phase.ACTIVE
            current_phase.options = json.dumps(options_data)
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

        logger.info("GameService.start() adding task to notify users: %s", user_ids)
        tasks.notify_task.apply_async(args=[user_ids, data], kwargs={})

        logger.info("GameService.start() returning game: %s", game)
        return game

    def resolve(self, game_id):
        logger.info("GameService.resolve() called with game_id: %s", game_id)

        game = get_object_or_404(models.Game, id=game_id)

        try:
            adjudication_response = self.adjudication_service.resolve(game)
        except Exception as e:
            logger.error(
                "GameService.resolve() adjudication service failed: %s", str(e)
            )
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        phase_data = adjudication_response["phase"]
        options_data = adjudication_response["options"]

        logger.info("GameService.resolve() resolving phase: %s", phase_data)

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
                    phase_state__phase=current_phase, source=province
                ).first()

                if order:
                    # Create or update resolution
                    models.OrderResolution.objects.update_or_create(
                        order=order, defaults={"status": result, "by": by}
                    )

            new_phase = self._create_phase(game, phase_data, options_data)

            self._create_phase_states(game)

            # Create a resolution task
            self._create_resolution_task(game)

        user_ids = [member.user.id for member in game.members.all()]
        data = {
            "title": "Phase Resolved",
            "body": f"Phase '{new_phase.name}' has been resolved!",
            "game_id": game.id,
            "type": "game_resolve",
        }

        logger.info("GameService.resolve() adding task to notify users: %s", user_ids)
        tasks.notify_task.apply_async(args=[user_ids, data], kwargs={})

        logger.info("GameService.resolve() returning game: %s", game)
        return game

    def _create_phase(self, game, phase_data, options_data):
        variant = game.variant
        phase = game.phases.create(
            game=game,
            season=phase_data["season"],
            year=phase_data["year"],
            type=phase_data["type"],
            options=json.dumps(options_data),
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
        members = game.members.all().order_by("created_at")

        if game.nation_assignment == models.Game.RANDOM:
            # Shuffle nations for random assignment
            nations = list(nations)
            random.shuffle(nations)

        # Assign nations to members in either random or ordered fashion
        for member, nation in zip(members, nations):
            member.nation = nation["name"]
            member.save()

    def _create_phase_states(self, game):
        # Create phase states for each member
        for member in game.members.all():
            models.PhaseState.objects.create(
                phase=game.current_phase,
                member=member,
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
            member__in=active_members, orders_confirmed=True
        ).count()

        return confirmed_count == active_members.count()

    def confirm_phase(self, game_id):
        logger.info("GameService.confirm_phase() called with game_id: %s", game_id)

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.ACTIVE:
            logger.warning(
                "GameService.confirm_phase() called when game is not active. This shouldn't happen."
            )
            raise exceptions.ValidationError(detail="Game is not active.")

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(
                "GameService.confirm_phase() called when user is not a member of the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(detail="User is not a member of the game.")

        if member.eliminated:
            logger.warning(
                "GameService.confirm_phase() called when user is eliminated from the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(detail="User is eliminated from the game.")

        if member.kicked:
            logger.warning(
                "GameService.confirm_phase() called when user is kicked from the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(detail="User is kicked from the game.")

        current_phase = game.phases.last()
        if not current_phase:
            logger.warning(
                "GameService.confirm_phase() called when no current phase found for the game. This shouldn't happen."
            )
            raise exceptions.ValidationError(
                detail="No current phase found for the game."
            )

        phase_state = current_phase.phase_states.filter(member=member).first()
        if not phase_state:
            logger.warning(
                "GameService.confirm_phase() called when no phase state found for the user. This shouldn't happen."
            )
            raise exceptions.ValidationError(
                detail="No phase state found for the user."
            )

        phase_state.orders_confirmed = not phase_state.orders_confirmed
        phase_state.save()

        logger.info("GameService.confirm_phase() phase confirmed: %s", phase_state)

        # Check if all active members have confirmed their orders
        if phase_state.orders_confirmed and self._should_resolve_phase(game):
            logger.info(
                "GameService.confirm_phase() all orders confirmed, resolving phase: %s",
                game,
            )
            # Execute the resolution task immediately if it exists
            if game.resolution_task:
                tasks.resolve_task.apply_async(
                    args=[game.id],
                    kwargs={},
                    task_id=game.resolution_task.id,
                    countdown=0,  # Execute immediately
                )

        return phase_state
