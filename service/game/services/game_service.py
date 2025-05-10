import random

from celery import shared_task
from django.db.models import (
    BooleanField,
    Case,
    Value,
    When,
    Prefetch,
    OuterRef,
    Subquery,
    Exists,
    Q,
)
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import exceptions

from .. import models
from ..tasks import BaseTask
from .base_service import BaseService


class GameService(BaseService):
    def __init__(self, user, adjudication_service=None, notification_service=None):
        self.user = user
        self.adjudication_service = adjudication_service
        self.notification_service = notification_service

    def list(self, filters=None):
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
        )

        queryset = queryset.prefetch_related(
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

        return queryset.distinct()

    def retrieve(self, game_id):
        queryset = self.list()
        return get_object_or_404(queryset.distinct(), id=game_id)

    @transaction.atomic
    def create(self, data):
        variant = models.Variant.objects.filter(id=data["variant"]).first()
        if not variant:
            raise exceptions.ValidationError(
                detail=f"Variant with name {data['variant']} does not exist."
            )

        with transaction.atomic():
            game = models.Game.objects.create(
                name=data["name"],
                variant=variant,
            )
            game.members.create(user=self.user)

        return game

    def join(self, game_id):
        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            raise exceptions.PermissionDenied(detail="Cannot join a non-pending game.")

        if game.members.filter(user=self.user).exists():
            raise exceptions.ValidationError(
                detail="User is already a member of the game."
            )

        game.members.create(user=self.user)

        return game

    def leave(self, game_id):
        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            raise exceptions.PermissionDenied(detail="Cannot leave a non-pending game.")

        member = game.members.filter(user=self.user).first()
        if not member:
            raise exceptions.ValidationError(detail="User is not a member of the game.")

        member.delete()

    def start(self, game_id):

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.PENDING:
            raise exceptions.PermissionDenied(detail="Cannot start a non-pending game.")

        try:
            adjudication_response = self.adjudication_service.start(game)
        except Exception as e:
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        with transaction.atomic():
            self._set_nations(game)
            self._set_options(game, adjudication_response["options"])

            current_phase = game.phases.last()
            current_phase.status = models.Phase.ACTIVE
            current_phase.save()

            # Set the game status to active
            game.status = models.Game.ACTIVE
            game.save()

            # Create a resolution task
            self._create_resolution_task(game)

        user_ids = [member.user.id for member in game.members.all()]
        self.notification_service.notify(
            user_ids,
            {
                "title": "Game Started",
                "message": f"Game '{game.name}' has started!",
                "game_id": game.id,
                "type": "game_start",
            },
        )

    @shared_task(base=BaseTask)
    def start_task(game_id):
        service = GameService(user=None)  # Pass `None` or a system user if needed
        service.start(game_id)

    def resolve(self, game_id):
        game = get_object_or_404(models.Game, id=game_id)

        try:
            adjudication_response = self.adjudication_service.resolve(game)
        except Exception as e:
            raise exceptions.ValidationError(
                detail=f"Adjudication service failed: {str(e)}"
            )

        phase_data = adjudication_response["phase"]
        options_data = adjudication_response["options"]

        with transaction.atomic():
            # Set the status of the current phase to completed
            current_phase = game.phases.last()
            current_phase.status = models.Phase.COMPLETED
            current_phase.save()

            new_phase = self._create_phase(game, phase_data)

            self._set_options(game, options_data)

            # Create a resolution task
            self._create_resolution_task(game)

        user_ids = [member.user.id for member in game.members.all()]
        self.notification_service.notify(
            user_ids,
            {
                "title": "Phase Resolved",
                "message": f"Phase '{new_phase.name}' has been resolved!",
                "game_id": game.id,
                "type": "game_resolve",
            },
        )

    @shared_task(base=BaseTask)
    def resolve_task(game_id):
        service = GameService(user=None)  # Pass `None` or a system user if needed
        service.resolve(game_id)

    def _create_phase(self, game, phase_data):
        variant = game.variant
        phase = game.phases.create(
            game=game,
            season=variant.start["season"],
            year=variant.start["year"],
            type=variant.start["type"],
        )

        for unit_data in variant.start["units"]:
            models.Unit.objects.create(
                phase=phase,
                type=unit_data["type"].lower(),
                nation=unit_data["nation"],
                province=unit_data["province"],
            )

        for sc_data in variant.start["supply_centers"]:
            models.SupplyCenter.objects.create(
                phase=phase,
                nation=sc_data["nation"],
                province=sc_data["province"],
            )

    def _set_nations(self, game):
        nations = game.variant.nations
        random.shuffle(nations)
        for member in game.members.all():
            nation = nations.pop()
            member.nation = nation["name"]
            member.save()

    def _set_options(self, game, options_data):
        for member in game.members.all():
            phase_state = models.PhaseState.objects.filter(
                phase=game.current_phase, member=member
            ).first()
            if phase_state:
                phase_state.options = options_data[member.nation]
                phase_state.save()

    def _create_resolution_task(self, game):
        phase_duration_seconds = game.get_phase_duration_seconds()
        scheduled_for = timezone.now() + timedelta(seconds=phase_duration_seconds)
        task_result = self.resolve_task.apply_async(
            args=[game.id],
            kwargs={},
            countdown=phase_duration_seconds,
        )
        task = models.Task.objects.get(id=task_result.task_id)
        task.scheduled_for = scheduled_for
        task.save()

        game.resolution_task = task
        game.save()
