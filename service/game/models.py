from datetime import timedelta
import re
import uuid

from django.db import models
from django.utils import timezone
from django.db.models import Prefetch
from common.constants import GameStatus, MovementPhaseDuration, NationAssignment, PhaseStatus
from common.models import BaseModel
from phase.models import Phase
from adjudication import service as adjudication_service


class GameQuerySet(models.QuerySet):

    def with_related_data(self):

        template_phase_prefetch = Prefetch(
            "variant__phases",
            queryset=Phase.objects.filter(game=None, status=PhaseStatus.TEMPLATE).prefetch_related(
                "units__nation",
                "units__province__parent",
                "units__province__named_coasts",
                "units__dislodged_by",
                "supply_centers__nation",
                "supply_centers__province__parent",
                "supply_centers__province__named_coasts",
                "phase_states",
            ),
            to_attr="template_phases",
        )

        return self.prefetch_related(
            # Variant data with optimized template phase
            "variant__provinces__parent",
            "variant__provinces__named_coasts",
            "variant__nations",
            template_phase_prefetch,
            # Game phases data
            "phases__units__nation",
            "phases__units__province__parent",
            "phases__units__province__named_coasts",
            "phases__units__dislodged_by",
            "phases__supply_centers__nation",
            "phases__supply_centers__province__parent",
            "phases__supply_centers__province__named_coasts",
            "phases__phase_states",
            # Members data
            "members__nation",
            "members__user__profile",
        )


class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def create_from_template(self, variant, user, **kwargs):
        template_phase = variant.template_phase
        game = self.create(variant=variant, **kwargs)
        game.members.create(user=user)
        game.channels.create(name="Public Press", private=False)

        phase = game.phases.create(
            game=game,
            variant=variant,
            season=template_phase.season,
            year=template_phase.year,
            type=template_phase.type,
            status=PhaseStatus.PENDING,
            ordinal=1,
        )

        for template_unit in template_phase.units.all():
            phase.units.create(
                type=template_unit.type,
                nation=template_unit.nation,
                province=template_unit.province,
                dislodged_by=template_unit.dislodged_by,
            )

        for template_sc in template_phase.supply_centers.all():
            phase.supply_centers.create(
                nation=template_sc.nation,
                province=template_sc.province,
            )

        return game


class Game(BaseModel):

    objects = GameManager()

    id = models.CharField(max_length=150, primary_key=True)
    variant = models.ForeignKey("variant.Variant", on_delete=models.CASCADE, related_name="games")
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=GameStatus.STATUS_CHOICES, default=GameStatus.PENDING)
    sandbox = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    movement_phase_duration = models.CharField(
        max_length=20,
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
        null=True,
        blank=True,
        default=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    nation_assignment = models.CharField(
        max_length=20,
        choices=NationAssignment.NATION_ASSIGNMENT_CHOICES,
        default=NationAssignment.RANDOM,
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        super().save(*args, **kwargs)

    def _generate_id(self):
        base_id = re.sub(r"[^a-z0-9]+", "-", self.name.lower())
        base_id = re.sub(r"^-+|-+$", "", base_id)

        if not Game.objects.filter(id=base_id).exists():
            return base_id

        return f"{base_id}-{str(uuid.uuid4())[:8]}"

    @property
    def current_phase(self):
        phases = list(self.phases.all())
        return phases[-1] if phases else None

    @property
    def movement_phase_duration_seconds(self):
        if self.movement_phase_duration is None:
            return None
        if self.movement_phase_duration == MovementPhaseDuration.TWENTY_FOUR_HOURS:
            return 24 * 60 * 60
        elif self.movement_phase_duration == MovementPhaseDuration.FORTY_EIGHT_HOURS:
            return 48 * 60 * 60
        elif self.movement_phase_duration == MovementPhaseDuration.ONE_WEEK:
            return 7 * 24 * 60 * 60
        return 0

    def can_join(self, user):
        user_is_member = any(member.user.id == user.id for member in self.members.all())
        game_is_pending = self.status == GameStatus.PENDING
        return not user_is_member and game_is_pending

    def can_leave(self, user):
        user_is_member = any(member.user.id == user.id for member in self.members.all())
        game_is_pending = self.status == GameStatus.PENDING
        return user_is_member and game_is_pending

    def phase_confirmed(self, user):
        current_phase = self.current_phase
        for phase_state in current_phase.phase_states.all():
            if phase_state.member.user.id == user.id and phase_state.orders_confirmed:
                return True
        return False

    def start(self):
        if self.status != GameStatus.PENDING:
            raise ValueError("Game is not pending")

        current_phase = self.current_phase
        adjudication_data = adjudication_service.start(self.current_phase)

        current_phase.status = PhaseStatus.ACTIVE
        current_phase.options = adjudication_data["options"]
        if self.movement_phase_duration is not None:
            current_phase.scheduled_resolution = timezone.now() + timedelta(seconds=self.movement_phase_duration_seconds)
        else:
            current_phase.scheduled_resolution = None
        current_phase.save()

        members = self.members.all()
        nations = self.variant.nations.all()

        if self.nation_assignment == NationAssignment.RANDOM:
            members = members.order_by("?")
        elif self.nation_assignment == NationAssignment.ORDERED:
            members = members.order_by("id")

        for member, nation in zip(members, nations):
            member.nation = nation
            member.save()

        for member in members:
            current_phase.phase_states.create(member=member)

        self.status = GameStatus.ACTIVE
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["variant"]),
        ]
