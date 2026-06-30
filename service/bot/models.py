from django.db import models

from common.models import BaseModel
from bot.constants import LLMCallStage, LLMCallStatus


class LLMCall(BaseModel):
    phase = models.ForeignKey("phase.Phase", on_delete=models.CASCADE, related_name="llm_calls")
    member = models.ForeignKey(
        "member.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_calls",
    )
    stage = models.CharField(max_length=20, choices=LLMCallStage.STAGE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=LLMCallStatus.STATUS_CHOICES,
        default=LLMCallStatus.SUCCESS,
    )
    model = models.CharField(max_length=255)
    system = models.TextField(blank=True)
    user_content = models.TextField(blank=True)
    response = models.TextField(blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cache_read_tokens = models.PositiveIntegerField(default=0)
    cache_write_tokens = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.stage} call ({self.status}) for phase {self.phase_id}"
