from django.conf import settings
from django.db import models

from common.models import BaseModel

from .constants import ReportDecision, ReportReason, ReportStatus
from .managers import MarkManager, ReportManager


class Report(BaseModel):
    objects = ReportManager()

    reporter = models.ForeignKey(
        "member.Member",
        related_name="reports_made",
        on_delete=models.CASCADE,
    )
    reported = models.ForeignKey(
        "member.Member",
        related_name="reports_received",
        on_delete=models.CASCADE,
    )
    reason = models.CharField(max_length=32, choices=ReportReason.REASON_CHOICES)
    note = models.CharField(max_length=1000)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assigned_reports",
        on_delete=models.SET_NULL,
        null=True,
        db_index=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "reported"],
                name="report_unique_per_reporter_per_reported",
            ),
        ]
        indexes = [
            models.Index(fields=["assigned_to"], name="report_assigned_to_idx"),
        ]

    @property
    def game(self):
        return self.reporter.game

    @property
    def status(self):
        review = getattr(self, "review", None)
        if review is None:
            return ReportStatus.PENDING
        return review.decision

    def assign(self, user):
        self.assigned_to = user
        self.save(update_fields=["assigned_to", "updated_at"])

    def unassign(self):
        self.assigned_to = None
        self.save(update_fields=["assigned_to", "updated_at"])

    def decide(self, decision, user, note):
        self.review = ReportReview.objects.create(
            report=self, decision=decision, reviewed_by=user, note=note
        )


class ReportReview(BaseModel):
    report = models.OneToOneField(
        Report,
        related_name="review",
        on_delete=models.CASCADE,
    )
    decision = models.CharField(max_length=16, choices=ReportDecision.DECISION_CHOICES)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="report_reviews",
        on_delete=models.CASCADE,
    )
    note = models.CharField(max_length=1000, db_default="")


class Mark(BaseModel):
    objects = MarkManager()

    member = models.ForeignKey(
        "member.Member",
        related_name="marks",
        on_delete=models.CASCADE,
    )
    reason = models.CharField(max_length=32, choices=ReportReason.REASON_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["member", "reason"],
                name="mark_unique_per_member_per_reason",
            ),
        ]
