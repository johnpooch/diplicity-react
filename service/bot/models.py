from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel
from bot.constants import BOT_USER_USERNAME, LLMCallStage, LLMCallStatus


class BotProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")

    def available_for_game(self, game):
        return (
            self.select_related("user__profile")
            .exclude(user__username=BOT_USER_USERNAME)
            .exclude(user__members__game=game)
            .order_by("user__profile__name")
        )


class BotProfileManager(models.Manager):
    def get_queryset(self):
        return BotProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def available_for_game(self, game):
        return self.get_queryset().available_for_game(game)


class BotProfile(BaseModel):
    objects = BotProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bot_profile")
    disposition = models.TextField()
    voice = models.TextField()


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
