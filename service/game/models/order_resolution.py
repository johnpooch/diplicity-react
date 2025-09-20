from django.db import models
from .base import BaseModel
from .order import Order


class OrderResolution(BaseModel):

    SUCCEEDED = "OK"
    ILLEGAL_MOVE = "ErrIllegalMove"
    ILLEGAL_DESTINATION = "ErrIllegalDestination"
    BOUNCED = "ErrBounce"
    INVALID_SUPPORT_ORDER = "ErrInvalidSupporteeOrder"
    ILLEGAL_SUPPORT_DESTINATION = "ErrIllegalSupportDestination"
    INVALID_DESTINATION = "ErrInvalidDestination"
    MISSING_SUPPORT_UNIT = "ErrMissingSupportUnit"

    STATUS_CHOICES = [
        (SUCCEEDED, "Succeeded"),
        (ILLEGAL_MOVE, "Illegal move"),
        (ILLEGAL_DESTINATION, "Illegal destination"),
        (BOUNCED, "Bounced"),
        (INVALID_SUPPORT_ORDER, "Invalid support order"),
        (ILLEGAL_SUPPORT_DESTINATION, "Illegal support destination"),
        (INVALID_DESTINATION, "Invalid destination"),
        (MISSING_SUPPORT_UNIT, "Missing support unit"),
    ]

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="resolution"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    by = models.CharField(max_length=50, null=True, blank=True, help_text="Province that caused the resolution status (e.g. province that caused a bounce)")
