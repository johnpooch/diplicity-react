from django.db import models
from django.db.models import Q
from common.models import BaseModel
from common.constants import UnitType


class Unit(BaseModel):
    type = models.CharField(max_length=10, choices=UnitType.UNIT_TYPE_CHOICES)
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="units")
    province = models.ForeignKey("province.Province", on_delete=models.CASCADE, related_name="units")
    phase = models.ForeignKey("phase.Phase", on_delete=models.CASCADE, related_name="units")
    dislodged = models.BooleanField(default=False)
    dislodged_by = models.OneToOneField(
        "unit.Unit", on_delete=models.CASCADE, related_name="dislodges", null=True, blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(dislodged=False, dislodged_by__isnull=True) | Q(dislodged=True),
                name="dislodged_by_requires_dislodged",
            )
        ]
