from django.db import models
from .base import BaseModel


class SupplyCenter(BaseModel):
    province = models.CharField(max_length=50)
    nation = models.CharField(max_length=50)
    phase = models.ForeignKey(
        "Phase", on_delete=models.CASCADE, related_name="supply_centers"
    )
