from datetime import timedelta

from django.db import models
from django.utils import timezone

from agent.constants import AgentTaskKind, AgentTaskStatus
from common.models import BaseModel

PENDING_RECONCILE_AFTER = timedelta(minutes=2)
RUNNING_RECONCILE_AFTER = timedelta(minutes=10)


class AgentTaskManager(models.Manager):
    def create_from_event(self, event_type, context):
        # Local import: agent.registry imports member/bot_profile models.
        from agent.registry import get_spec

        spec = get_spec(event_type, context)
        if spec is None:
            return []
        return [self.enqueue(**descriptor) for descriptor in spec.get_tasks()]

    def enqueue(self, *, kind, member, phase=None, message=None):
        task, created = self.get_or_create(
            kind=kind,
            member=member,
            phase=phase,
            message=message,
            defaults={"status": AgentTaskStatus.PENDING},
        )
        if created:
            task.defer()
        return task

    def reconcile(self):
        now = timezone.now()
        stalled = self.filter(
            models.Q(status=AgentTaskStatus.PENDING, created_at__lt=now - PENDING_RECONCILE_AFTER)
            | models.Q(status=AgentTaskStatus.RUNNING, started_at__lt=now - RUNNING_RECONCILE_AFTER)
        )
        tasks = list(stalled)
        for task in tasks:
            task.defer()
        return tasks


class AgentTask(BaseModel):
    objects = AgentTaskManager()

    kind = models.CharField(max_length=20, choices=AgentTaskKind.KIND_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=AgentTaskStatus.STATUS_CHOICES,
        default=AgentTaskStatus.PENDING,
    )
    member = models.ForeignKey("member.Member", on_delete=models.CASCADE, related_name="agent_tasks")
    phase = models.ForeignKey(
        "phase.Phase",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="agent_tasks",
    )
    message = models.ForeignKey(
        "channel.ChannelMessage",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="agent_tasks",
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "member", "phase"],
                condition=models.Q(message__isnull=True),
                name="unique_phase_agent_task",
            ),
            models.UniqueConstraint(
                fields=["kind", "member", "message"],
                condition=models.Q(message__isnull=False),
                name="unique_reply_agent_task",
            ),
        ]

    def defer(self):
        # Local import: agent.tasks imports this module at top level.
        from agent.tasks import run

        run.configure(lock=f"agent-task-{self.id}").defer(agent_task_id=self.id)

    def mark_running(self):
        self.status = AgentTaskStatus.RUNNING
        self.attempts += 1
        self.started_at = timezone.now()
        self.save(update_fields=["status", "attempts", "started_at", "updated_at"])

    def mark_succeeded(self):
        self.status = AgentTaskStatus.SUCCEEDED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def mark_failed(self, error):
        self.status = AgentTaskStatus.FAILED
        self.last_error = str(error)
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "last_error", "completed_at", "updated_at"])

    def __str__(self):
        return f"{self.kind} agent task ({self.status}) for member {self.member_id}"
