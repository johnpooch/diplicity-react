from django.db import models
from django.contrib.auth.models import User

from common.models import BaseModel


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
    picture = models.URLField()

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email
