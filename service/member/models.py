from django.db import models
from django.contrib.auth import get_user_model
from common.models import BaseModel

User = get_user_model()


class Member(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="members")
    game = models.ForeignKey("game.Game", on_delete=models.CASCADE, related_name="members")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="members", null=True, blank=True)
    won = models.BooleanField(default=False)
    drew = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    kicked = models.BooleanField(default=False)
    is_game_master = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["game", "user"]),
            models.Index(fields=["user"]),
            models.Index(fields=["game"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["game"],
                condition=models.Q(is_game_master=True),
                name="unique_game_master_per_game",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.game.name} - {self.nation.name if self.nation else '-'}"
