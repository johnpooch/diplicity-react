import hashlib

from django.db import models
from django.contrib.auth.models import User

from common.constants import Commitment
from common.models import BaseModel


def hash_email(email):
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


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
    email_notifications_enabled = models.BooleanField(default=False)
    commitment = models.CharField(
        max_length=20,
        choices=Commitment.COMMITMENT_CHOICES,
        default=Commitment.UNDEFINED,
    )


class RetainedCommitmentManager(models.Manager):
    def retain(self, email, commitment):
        if not email:
            return None
        retained, _ = self.update_or_create(
            email_hash=hash_email(email),
            defaults={"commitment": commitment},
        )
        return retained

    def commitment_for(self, email):
        if not email:
            return Commitment.UNDEFINED
        retained = self.filter(email_hash=hash_email(email)).first()
        return retained.commitment if retained else Commitment.UNDEFINED


class RetainedCommitment(BaseModel):
    objects = RetainedCommitmentManager()
    email_hash = models.CharField(max_length=64, unique=True)
    commitment = models.CharField(
        max_length=20,
        choices=Commitment.COMMITMENT_CHOICES,
    )
