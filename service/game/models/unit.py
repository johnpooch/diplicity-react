from django.db import models
from .base import BaseModel
from .phase import Phase


class Unit(BaseModel):
    FLEET = "fleet"
    ARMY = "army"

    UNIT_TYPE_CHOICES = (
        (FLEET, "Fleet"),
        (ARMY, "Army"),
    )

    unit_type = models.CharField(max_length=10, choices=UNIT_TYPE_CHOICES)
    nation = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name="units")
    dislodged = models.BooleanField(default=False)
