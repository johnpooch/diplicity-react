from django.conf import settings
from django.db import models

from common.models import BaseModel

from .managers import RatingResultManager
from .querysets import RatingQuerySet


class Rating(BaseModel):
    objects = RatingQuerySet.as_manager()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="rating",
        on_delete=models.CASCADE,
    )
    rating = models.FloatField()
    deviation = models.FloatField()
    rated_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["rating"], name="rating_rating_idx"),
        ]

    def record(self, result):
        self.rating = result.rating_after
        self.deviation = result.deviation_after
        self.rated_at = result.created_at
        self.save(update_fields=["rating", "deviation", "rated_at", "updated_at"])


class RatingResult(BaseModel):
    objects = RatingResultManager()

    member = models.OneToOneField(
        "member.Member",
        related_name="rating_result",
        on_delete=models.CASCADE,
    )
    rating_before = models.FloatField()
    deviation_before = models.FloatField()
    rating_after = models.FloatField()
    deviation_after = models.FloatField()
    handicap = models.IntegerField()
    protected = models.BooleanField(default=False)

    def record_pairings(self, pairings):
        self.pairings.bulk_create(
            [
                RatingPairing(
                    result=self,
                    opponent_id=pairing.opponent_id,
                    opponent_rating=pairing.opponent_rating,
                    opponent_deviation=pairing.opponent_deviation,
                    opponent_handicap=pairing.opponent_handicap,
                    score=pairing.score,
                    change=pairing.change,
                )
                for pairing in pairings
            ]
        )


class RatingPairing(BaseModel):
    result = models.ForeignKey(
        RatingResult,
        related_name="pairings",
        on_delete=models.CASCADE,
    )
    opponent = models.ForeignKey(
        "member.Member",
        related_name="rating_pairings_against",
        on_delete=models.CASCADE,
    )
    opponent_rating = models.FloatField()
    opponent_deviation = models.FloatField()
    opponent_handicap = models.IntegerField()
    score = models.FloatField()
    change = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["result", "opponent"],
                name="rating_pairing_unique_per_result_per_opponent",
            ),
        ]
        indexes = [
            models.Index(fields=["opponent"], name="rating_pairing_opponent_idx"),
        ]


class NationHandicap(BaseModel):
    nation = models.OneToOneField(
        "nation.Nation",
        related_name="handicap",
        on_delete=models.CASCADE,
    )
    offset = models.IntegerField()

    def __str__(self):
        return f"{self.nation} ({self.offset:+d})"
