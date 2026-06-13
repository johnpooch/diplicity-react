from django.db import models
from django.contrib.auth import get_user_model
from common.models import BaseModel

User = get_user_model()


class Member(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="members")
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="members")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="members", null=True, blank=True)
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    kicked = models.BooleanField(default=False)
    nmr_extensions_remaining = models.PositiveSmallIntegerField(default=0)
    civil_disorder = models.BooleanField(default=False)
    seeking_replacement = models.BooleanField(default=False)
    replaced_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replaces",
    )

    class Meta:
        indexes = [
            models.Index(fields=["game", "user"]),
            models.Index(fields=["user"]),
            models.Index(fields=["game"]),
        ]

    @property
    def replaceable(self):
        return (self.civil_disorder or self.seeking_replacement) and not (
            self.eliminated or self.kicked or self.replaced_by_id is not None
        )

    @property
    def name(self):
        if self.user is None:
            return "Deleted User"
        return self.user.profile.name

    @property
    def picture(self):
        if self.user is None:
            return None
        return self.user.profile.picture

    def __str__(self):
        username = self.user.username if self.user else "Deleted User"
        return f"{username} - {self.game.name} - {self.nation.name if self.nation else '-'}"
