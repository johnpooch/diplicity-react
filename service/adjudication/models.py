from django.db import models


class ShadowAdjudicationDiff(models.Model):
    """A persisted mismatch between the godip and Python adjudicators,
    captured during shadow-mode resolution. Written only when the two
    disagree; matches are counted via telemetry and not stored."""

    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_CHOICES = [
        (TIER_1, "Tier 1"),
        (TIER_2, "Tier 2"),
        (TIER_3, "Tier 3"),
    ]

    phase = models.ForeignKey(
        "phase.Phase",
        on_delete=models.CASCADE,
        related_name="shadow_adjudication_diffs",
    )
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    pre_state = models.JSONField()
    godip_response = models.JSONField()
    python_response = models.JSONField()
    diff_summary = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ShadowAdjudicationDiff(phase={self.phase_id}, tier={self.tier})"
