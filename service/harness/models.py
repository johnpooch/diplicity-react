from django.db import models

from common.models import BaseModel
from harness.constants import EvalRunKind


class EvalRun(BaseModel):
    kind = models.CharField(max_length=20, choices=EvalRunKind.KIND_CHOICES, default=EvalRunKind.EVAL)
    model = models.CharField(max_length=255)
    commit = models.CharField(max_length=40)
    dataset = models.CharField(max_length=12, blank=True)
    epochs = models.PositiveIntegerField(null=True, blank=True)
    eval_id = models.CharField(max_length=64, blank=True)
    ran_at = models.DateTimeField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.kind} {self.model} {self.commit}"


class EvalScore(BaseModel):
    run = models.ForeignKey(EvalRun, on_delete=models.CASCADE, related_name="scores")
    scorer = models.CharField(max_length=100)
    metric = models.CharField(max_length=100)
    value = models.FloatField()
    stderr = models.FloatField(null=True, blank=True)
    sample_count = models.PositiveIntegerField()

    class Meta:
        ordering = ["run_id", "scorer", "metric"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "scorer", "metric"],
                name="unique_run_scorer_metric",
            ),
        ]

    def __str__(self):
        return f"{self.scorer} {self.metric} {self.value}"
