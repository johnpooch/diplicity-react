import json

from django.db import models
from django.utils import timezone
from common.models import BaseModel
from datetime import timedelta
from common.constants import PhaseStatus
from adjudication.service import resolve
from order.models import OrderResolution


class PhaseManager(models.Manager):

    def resolve_due_phases(self):
        phases = self.get_queryset().filter(
            scheduled_resolution__lte=timezone.now(),
            status=PhaseStatus.ACTIVE,
        )
        resolved_count = 0
        failed_count = 0
        for phase in phases:
            try:
                phase.resolve()
                resolved_count += 1
            except Exception as e:
                failed_count += 1
        return {
            "resolved": resolved_count,
            "failed": failed_count,
        }

    def resolve(self, phase):
        adjudication_data = resolve(phase)
        self.create_from_adjudication_data(phase, adjudication_data)

    def create_from_adjudication_data(self, previous_phase, adjudication_data):

        for order in previous_phase.all_orders:
            resolution = next(
                (r for r in adjudication_data["resolutions"] if r["province"] == order.source.province_id), None
            )
            OrderResolution.objects.create(
                order=order,
                status=resolution["result"],
                by=resolution["by"],
            )

        if self._has_no_valid_moves(adjudication_data["options"]):
            scheduled_resolution = timezone.now()
        else:
            phase_duration_seconds = previous_phase.game.get_phase_duration_seconds()
            scheduled_resolution = timezone.now() + timedelta(seconds=phase_duration_seconds)

        new_phase = self.create(
            game=previous_phase.game,
            variant=previous_phase.variant,
            ordinal=previous_phase.ordinal + 1,
            season=adjudication_data["season"],
            year=adjudication_data["year"],
            type=adjudication_data["type"],
            options=json.dumps(adjudication_data["options"]),
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=scheduled_resolution,
        )

        for supply_center in adjudication_data["supply_centers"]:
            new_phase.supply_centers.create(
                province=new_phase.variant.provinces.get(province_id=supply_center["province"]),
                nation=new_phase.variant.nations.get(name=supply_center["nation"]),
            )

        for unit in adjudication_data["units"]:
            new_phase.units.create(
                type=unit["type"],
                nation=new_phase.variant.nations.get(name=unit["nation"]),
                province=new_phase.variant.provinces.get(province_id=unit["province"]),
            )

        for member in new_phase.game.members.all():
            new_phase.phase_states.create(
                member=member,
            )

        previous_phase.status = PhaseStatus.COMPLETED
        previous_phase.save()

        return new_phase

    def _has_no_valid_moves(self, options_data):
        if not options_data or not isinstance(options_data, dict):
            return True
        for nation, nation_options in options_data.items():
            if nation_options and isinstance(nation_options, dict):
                if any(province_data for province_data in nation_options.values()):
                    return False
        return True


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
    options = models.JSONField(default=dict)

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


class PhaseState(BaseModel):
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="phase_states")
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="phase_states")
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)

    @property
    def orderable_provinces(self):
        options = self.phase.options
        nation = self.member.nation
        orderable_provinces = list(options[nation.name].keys())
        return self.phase.variant.provinces.filter(province_id__in=orderable_provinces)
