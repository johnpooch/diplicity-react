from django.db import models
from .base import BaseModel


class Task(BaseModel):

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    )

    id = models.CharField(primary_key=True, editable=False, max_length=36)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    result = models.TextField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
