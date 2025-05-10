from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    picture = models.URLField()

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email
