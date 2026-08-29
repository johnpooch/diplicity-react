import hashlib

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse

from common.constants import Commitment, UserKind
from common.models import BaseModel


class UserProfileQuerySet(models.QuerySet):
    def with_related_data(self):
        return self.select_related("user", "uploaded_picture")

    def addable_to_game(self, game):
        return (
            self.filter(kind__in=UserKind.BOT_KINDS)
            .select_related("user", "uploaded_picture")
            .exclude(user__members__game=game)
            .order_by("name")
        )


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def addable_to_game(self, game):
        return self.get_queryset().addable_to_game(game)


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
    kind = models.CharField(
        max_length=20,
        choices=UserKind.KIND_CHOICES,
        default=UserKind.HUMAN,
    )

    @property
    def is_bot(self):
        return self.kind != UserKind.HUMAN

    @property
    def has_uploaded_picture(self) -> bool:
        return UserProfilePicture.objects.filter(profile=self).exists()

    def picture_url(self, request=None) -> str | None:
        try:
            picture = self.uploaded_picture
        except UserProfilePicture.DoesNotExist:
            return self.picture
        path = reverse(
            "user-picture-image",
            kwargs={"user_id": self.user_id, "content_hash": picture.content_hash},
        )
        return request.build_absolute_uri(path) if request else path


class UserProfilePictureManager(models.Manager):
    def store(self, profile, data, content_type):
        self.filter(profile=profile).delete()
        content_hash = hashlib.sha256(data).hexdigest()
        extension = content_type.rsplit("/", 1)[-1]
        picture = self.model(profile=profile, content_type=content_type, content_hash=content_hash)
        picture.image.save(f"{content_hash}.{extension}", ContentFile(data), save=True)
        return picture


class UserProfilePicture(BaseModel):
    objects = UserProfilePictureManager()
    profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="uploaded_picture"
    )
    image = models.ImageField(upload_to="profile_pictures/")
    content_type = models.CharField(max_length=20)
    content_hash = models.CharField(max_length=64, editable=False)

    def __str__(self):
        return f"{self.profile.name} picture"
