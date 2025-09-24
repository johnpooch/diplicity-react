from django.db import models
from .base import BaseModel


class SupplyCenter(BaseModel):
    province = models.CharField(max_length=50)
    nation = models.CharField(max_length=50)
    phase = models.ForeignKey(
        "Phase", on_delete=models.CASCADE, related_name="supply_centers"
    )

    def province_data(self):
        variant = self.phase.variant
        return next((p for p in variant.provinces if p["id"] == self.province), None)

    def nation_data(self):
        variant = self.phase.variant
        return next((n for n in variant.nations if n["name"] == self.nation), None)
