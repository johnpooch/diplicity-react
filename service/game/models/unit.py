from django.db import models
from .base import BaseModel
from .phase import Phase


class Unit(BaseModel):
    FLEET = "Fleet"
    ARMY = "Army"

    UNIT_TYPE_CHOICES = (
        (FLEET, "Fleet"),
        (ARMY, "Army"),
    )

    type = models.CharField(max_length=10, choices=UNIT_TYPE_CHOICES)
    nation = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="units")
    dislodged = models.BooleanField(default=False)
    dislodged_by = models.CharField(max_length=50, null=True, blank=True)

    def province_data(self):
        variant = self.phase.variant
        return next((p for p in variant.provinces if p["id"] == self.province), None)

    def nation_data(self):
        variant = self.phase.variant
        return next((n for n in variant.nations if n["name"] == self.nation), None)
