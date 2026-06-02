from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel


def default_colour_profile():
    return [
        # 1–10: Okabe-Ito + Tol — maximum differentiability for all common colour-blindness types
        "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
        "#56B4E9", "#F0E442", "#332288", "#882255", "#117733",
        # 11–20: Tol Muted — strong perceptual separation, varied luminance
        "#44AA99", "#AA4499", "#DDCC77", "#999933", "#EE6677",
        "#88CCEE", "#EE8866", "#AA3377", "#BBBBBB", "#DDDDDD",
        # 21–30: best remaining differentiation across hue, chroma and lightness
        "#4B0082", "#7B3F00", "#40E0D0", "#FFD700", "#1B4F72",
        "#708090", "#D2691E", "#9B59B6", "#F4A460", "#98D8C8",
    ]


class UserProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user")


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()


class UserProfile(BaseModel):
    objects = UserProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    picture = models.URLField(null=True, blank=True)
    colour_profile_enabled = models.BooleanField(default=False)
    custom_colour_profile = models.JSONField(default=default_colour_profile)
