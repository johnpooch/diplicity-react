from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from bot.constants import BotKind, RunStatus, RunStep
from common.models import BaseModel

from .managers import RunManager


class Bot(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bot")
    kind = models.CharField(max_length=20, choices=BotKind.KIND_CHOICES)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Run(BaseModel):
    objects = RunManager()

    step = models.CharField(max_length=30, choices=RunStep.STEP_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=RunStatus.STATUS_CHOICES,
        default=RunStatus.PENDING,
    )
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="runs")
    member = models.ForeignKey(
        "member.Member", on_delete=models.CASCADE, related_name="bot_runs"
    )
    phase = models.ForeignKey(
        "phase.Phase", on_delete=models.CASCADE, related_name="bot_runs"
    )
    draw_proposal = models.ForeignKey(
        "draw_proposal.DrawProposal",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bot_runs",
    )
    earliest_start_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)
    snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "earliest_start_at"]),
        ]

    def __str__(self):
        return f"{self.step} run ({self.status}) for member {self.member_id}"

    def save_snapshot(self, context):
        self.snapshot = context
        self.save(update_fields=["snapshot", "updated_at"])

    def mark_running(self):
        self.status = RunStatus.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def mark_succeeded(self):
        self.complete(RunStatus.SUCCEEDED)

    def mark_skipped(self):
        self.complete(RunStatus.SKIPPED)

    def mark_timed_out(self):
        self.complete(RunStatus.TIMED_OUT)

    def mark_failed(self, error):
        self.error = str(error)
        self.complete(RunStatus.FAILED)

    def complete(self, status):
        self.status = status
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error", "completed_at", "updated_at"])
