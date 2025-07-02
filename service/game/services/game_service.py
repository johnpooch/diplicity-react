import random
import json
import logging
import time
from django.db import connection, reset_queries

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
        
        # Reset query count and start timing
        reset_queries()
        start_time = time.time()

        game_queryset = models.Game.objects.select_related('variant')
        
        if filters.get("mine"):
            game_queryset = game_queryset.filter(members__user=self.user)
        elif filters.get("can_join"):
            game_queryset = game_queryset.filter(status=models.Game.PENDING).exclude(
                members__user=self.user
            )

        games_data = game_queryset.only(
            'id', 'name', 'status', 'movement_phase_duration', 
            'nation_assignment', 'variant__id'
        )
        
        if not games_data:
            return []

        game_ids = [game.id for game in games_data]

        all_phases = models.Phase.objects.filter(
            game_id__in=game_ids
        ).order_by('game_id', '-ordinal').distinct('game_id').prefetch_related('units', 'supply_centers')

        # Preload variant data efficiently
        variant_ids = {game.variant.id for game in games_data}
        variants = models.Variant.objects.filter(id__in=variant_ids)
        variant_data = {}
        for variant in variants:
            data = variant.load_data()
            variant_data[variant.id] = {
                "id": variant.id,
                "name": variant.name,
                "nations": data["nations"],
                "start": data["start"],
                "description": data["description"],
                "author": data["author"],
                "provinces": data["provinces"],
            }

        # Build phase lookup more efficiently
        phases_by_game = {}
        for phase in all_phases:
            game_id = phase.game_id
            if game_id not in phases_by_game:
                phases_by_game[game_id] = []

            phases_by_game[game_id].append({
                'id': phase.id,
                'ordinal': phase.ordinal,
                'season': phase.season,
                'year': phase.year,
                'name': f"{phase.season} {phase.year}",
                'type': phase.type,
                'status': phase.status,
                'remaining_time': "24 hours",  # You might want to calculate this
                'options': phase.options_dict,
                'units': [
                    {
                        'type': unit.type,
                        'nation': {'name': unit.nation},
                        'province': {'id': unit.province, 'name': unit.province, 'type': 'TODO', 'supply_center': 'TODO'}
                    }
                    for unit in phase.units.all()
                ],
                'supply_centers': [
                    {
                        'province': {'id': sc.province, 'name': sc.province, 'type': 'TODO', 'supply_center': 'TODO'},
                        'nation': {'name': sc.nation}
                    }
                    for sc in phase.supply_centers.all()
                ]
            })

        # Get members for all games
        members = models.Member.objects.filter(
            game_id__in=game_ids
        ).select_related('user', 'user__profile').values(
            'game_id', 'id', 'nation', 'user__username', 
            'user__profile__name', 'user__profile__picture',
            'eliminated', 'kicked'
        )
        
        # Get phase states for current phases and current user
        current_phase_ids = [phase.id for phase in all_phases]
        user_phase_states = models.PhaseState.objects.filter(
            phase_id__in=current_phase_ids,
            member__user=self.user
        ).values('phase_id', 'orders_confirmed')
        
        # Create lookup for user phase states
        phase_confirmed_lookup = {
            ps['phase_id']: ps['orders_confirmed'] 
            for ps in user_phase_states
        }
        
        # Group members by game_id
        members_by_game = {}
        for member in members:
            game_id = member['game_id']
            if game_id not in members_by_game:
                members_by_game[game_id] = []
            
            members_by_game[game_id].append({
                'id': member['id'],
                'username': member['user__username'],
                'name': member['user__profile__name'],
                'picture': member['user__profile__picture'],
                'nation': member['nation'],
                'is_current_user': member['user__username'] == self.user.username,
            })

        result = []
        for game in games_data:
            game_members = members_by_game.get(game.id, [])
            current_phase = phases_by_game.get(game.id, [])[0] if phases_by_game.get(game.id) else None
            
            # Compute boolean fields
            can_join = game.status == models.Game.PENDING and not any(
                m['username'] == self.user.username for m in game_members
            )
            can_leave = game.status == models.Game.PENDING and any(
                m['username'] == self.user.username for m in game_members
            )
            
            # Can confirm phase is true if:
            # - game is active
            # - current phase exists and is active
            # - user is a member and not eliminated/kicked
            user_member = next(
                (m for m in game_members if m['username'] == self.user.username), 
                None
            )
            can_confirm_phase = (
                game.status == models.Game.ACTIVE and 
                current_phase is not None and 
                current_phase.get('status') == models.Phase.ACTIVE and
                user_member is not None and
                not user_member.get('eliminated', False) and
                not user_member.get('kicked', False)
            )
            
            # Get phase confirmed status
            phase_confirmed = False
            if current_phase and can_confirm_phase:
                phase_confirmed = phase_confirmed_lookup.get(current_phase['id'], False)
            
            result.append({
                "id": game.id,
                "name": game.name,
                "status": game.status,
                "movement_phase_duration": game.movement_phase_duration,
                "nation_assignment": game.nation_assignment,
                "can_join": can_join,
                "can_leave": can_leave,
                "current_phase": current_phase or {
                    "id": 1,
                    "ordinal": 1,
                    "season": "Spring",
                    "year": 1901,
                    "name": "Spring 1901",
                    "type": "movement",
                    "remaining_time": "24 hours",
                    "units": [],
                    "supply_centers": [],
                    "options": {},
                },
                "phases": phases_by_game.get(game.id, []),
                "variant": variant_data[game.variant.id],
                "members": game_members,
                "phase_confirmed": phase_confirmed,
                "can_confirm_phase": can_confirm_phase,
            })
        
        # Log performance metrics
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        query_count = len(connection.queries)
        total_query_time = sum(float(q['time']) for q in connection.queries) * 1000
        
        logger.info(f"Game list performance: {response_time:.2f}ms, {query_count} queries, {total_query_time:.2f}ms query time")
        
        # Log each query for analysis
        for i, query in enumerate(connection.queries):
            query_time = float(query['time']) * 1000
            logger.info(f"Query {i+1}: {query_time:.2f}ms - {query['sql'][:100]}...")
        
        return result

    def retrieve(self, game_id):
        logger.info(f"GameService.retrieve() called with game_id: {game_id}")
        
        reset_queries()
        start_time = time.time()

        # Single game query with variant
        game = models.Game.objects.select_related('variant').only(
            'id', 'name', 'status', 'movement_phase_duration', 
            'nation_assignment', 'variant__id'
        ).filter(id=game_id).first()
        
        if not game:
            raise exceptions.NotFound(detail="Game not found.")

        # Single query for all phases with units and supply centers
        all_phases = list(models.Phase.objects.filter(
            game_id=game_id
        ).order_by('ordinal').prefetch_related(
            'units', 'supply_centers'
        ))

        # Get current phase (most recent) - no additional query
        current_phase = all_phases[-1] if all_phases else None

        # Single query for members
        members = models.Member.objects.filter(
            game_id=game_id
        ).select_related('user', 'user__profile').values(
            'id', 'nation', 'user__username', 
            'user__profile__name', 'user__profile__picture',
            'eliminated', 'kicked'
        )

        # Single query for user's phase state (only current phase)
        user_phase_state = None
        user_member = None
        if current_phase:
            user_phase_state = models.PhaseState.objects.filter(
                phase=current_phase,
                member__user=self.user
            ).select_related('member').first()
            if user_phase_state:
                user_member = user_phase_state.member

        # Load variant data (this is the bottleneck)
        variant = models.Variant.objects.get(id=game.variant.id)
        variant_data = variant.load_data()

        # Build current phase data
        current_phase_data = None
        if current_phase:
            current_phase_data = {
                'id': current_phase.id,
                'ordinal': current_phase.ordinal,
                'season': current_phase.season,
                'year': current_phase.year,
                'name': f"{current_phase.season} {current_phase.year}",
                'type': current_phase.type,
                'remaining_time': current_phase.remaining_time,
                'options': current_phase.options_dict,
                'units': [
                    {
                        'type': unit.type,
                        'nation': {'name': unit.nation},
                        'province': {'id': unit.province, 'name': unit.province}
                    }
                    for unit in current_phase.units.all()
                ],
                'supply_centers': [
                    {
                        'province': {'id': sc.province, 'name': sc.province},
                        'nation': {'name': sc.nation}
                    }
                    for sc in current_phase.supply_centers.all()
                ]
            }

        # Build all phases data
        phases_data = []
        for phase in all_phases:
            phases_data.append({
                'id': phase.id,
                'ordinal': phase.ordinal,
                'season': phase.season,
                'year': phase.year,
                'name': f"{phase.season} {phase.year}",
                'type': phase.type,
                'remaining_time': "24 hours",
                'options': phase.options_dict,
                'units': [
                    {
                        'type': unit.type,
                        'nation': {'name': unit.nation},
                        'province': {'id': unit.province, 'name': unit.province}
                    }
                    for unit in phase.units.all()
                ],
                'supply_centers': [
                    {
                        'province': {'id': sc.province, 'name': sc.province},
                        'nation': {'name': sc.nation}
                    }
                    for sc in phase.supply_centers.all()
                ]
            })

        # Build members data
        members_data = [
            {
                'id': member['id'],
                'username': member['user__username'],
                'name': member['user__profile__name'],
                'picture': member['user__profile__picture'],
                'nation': member['nation'],
                'is_current_user': member['user__username'] == self.user.username,
            }
            for member in members
        ]

        # Build variant data
        variant_result = {
            "id": variant.id,
            "name": variant.name,
            "nations": variant_data["nations"],
            "start": variant_data["start"],
            "description": variant_data["description"],
            "author": variant_data["author"],
            "provinces": variant_data["provinces"],
        }

        # Compute boolean fields
        can_join = game.status == models.Game.PENDING and not any(
            m['user__username'] == self.user.username for m in members
        )
        can_leave = game.status == models.Game.PENDING and any(
            m['user__username'] == self.user.username for m in members
        )
        
        # Can confirm phase is true if:
        # - game is active
        # - current phase exists and is active
        # - user is a member and not eliminated/kicked
        can_confirm_phase = (
            game.status == models.Game.ACTIVE and 
            current_phase is not None and 
            current_phase.status == models.Phase.ACTIVE and
            user_member is not None and
            not user_member.eliminated and
            not user_member.kicked
        )

        result = {
            "id": game.id,
            "name": game.name,
            "status": game.status,
            "movement_phase_duration": game.movement_phase_duration,
            "nation_assignment": game.nation_assignment,
            "can_join": can_join,
            "can_leave": can_leave,
            "current_phase": current_phase_data or {
                "id": 1,
                "ordinal": 1,
                "season": "Spring",
                "year": 1901,
                "name": "Spring 1901",
                "type": "movement",
                "remaining_time": "24 hours",
                "units": [],
                "supply_centers": [],
                "options": {},
            },
            "phases": phases_data,
            "members": members_data,
            "variant": variant_result,
            "phase_confirmed": (
                user_phase_state.orders_confirmed 
                if user_phase_state and can_confirm_phase 
                else False
            ),
            "can_confirm_phase": can_confirm_phase,
        }
        
        # Log performance metrics
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        query_count = len(connection.queries)
        total_query_time = sum(float(q['time']) for q in connection.queries) * 1000
        
        logger.info(f"Game retrieve performance: {response_time:.2f}ms, {query_count} queries, {total_query_time:.2f}ms query time")
        
        return result

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

        logger.info(f"GameService.resolve() adding task to notify users: {user_ids}")
        tasks.notify_task.apply_async(args=[user_ids, data], kwargs={})

        logger.info(f"GameService.resolve() returning game: {game}")
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
        members = game.members.all().order_by('created_at')
        
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
