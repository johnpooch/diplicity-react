from django.db import models
from .base import BaseModel
from .phase import Phase


class PhaseState(BaseModel):
    member = models.ForeignKey(
        "Member", on_delete=models.CASCADE, related_name="phase_states"
    )
    phase = models.ForeignKey(
        Phase, on_delete=models.CASCADE, related_name="phase_states"
    )
    orders_confirmed = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
