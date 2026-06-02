from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel


def default_colour_profile():
    return [
        "#E63946", "#F4A261", "#E9C46A", "#2A9D8F", "#264653",
        "#457B9D", "#A8DADC", "#90BE6D", "#43AA8B", "#F94144",
        "#F3722C", "#F8961E", "#F9C74F", "#4D908E", "#277DA1",
        "#9D0208", "#3A0CA3", "#7B2D8B", "#C77DFF", "#48CAE4",
        "#023E8A", "#606C38", "#DDA15E", "#BC6C25", "#8B2FC9",
        "#5C4033", "#B5E48C", "#FF6B6B", "#4ECDC4", "#45B7D1",
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
