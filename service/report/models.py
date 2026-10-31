from django.conf import settings
from django.db import models

from common.models import BaseModel

from .constants import ReportDecision, ReportReason, ReportStatus
from .managers import ReportManager


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "reported"],
                name="report_unique_per_reporter_per_reported",
            ),
        ]

    @property
    def status(self):
        review = getattr(self, "review", None)
        if review is None:
            return ReportStatus.PENDING
        return review.decision


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
