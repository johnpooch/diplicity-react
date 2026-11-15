import hashlib

from django.contrib.auth.models import User
from django.db import models, transaction
from django.urls import reverse
from django.utils.functional import cached_property

from common.constants import CommitmentBand, UserKind
from common.models import BaseModel
from member.models import Member, commitment_points

from .utils import user_can_use_bot_opponent


class UserProfileQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self

    def with_related_data(self):
        return self.select_related("user__bot", "uploaded_picture")

    def addable_to_game(self, game):
        return (
            self.filter(user__bot__isnull=False)
            .select_related("user", "uploaded_picture")
            .exclude(user__members__game=game)
            .order_by("name")
        )

    def with_commitment_total(self):
        return self.annotate(
            commitment_total=commitment_points(
                "user__members__commitment_entries__kind"
            )
        )


class UserProfileManager(models.Manager):
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def addable_to_game(self, game):
        return self.get_queryset().addable_to_game(game)

    def with_commitment_total(self):
        return self.get_queryset().with_commitment_total()


class UserProfile(BaseModel):
    objects = UserProfileManager()
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=255)
    picture = models.URLField(null=True, blank=True)
    kind = models.CharField(
        max_length=20,
        choices=UserKind.KIND_CHOICES,
        default=UserKind.HUMAN,
    )
    is_moderator = models.BooleanField(default=False, db_default=False)

    @property
    def is_bot(self):
        return hasattr(self.user, "bot")

    @property
    def public_created_at(self):
        if self.is_bot:
            return None
        return self.created_at

    @property
    def can_create_bot_games(self) -> bool:
        return user_can_use_bot_opponent(self.user)

    @cached_property
    def commitment_total(self):
        return Member.objects.commitment_totals([self.user_id]).get(self.user_id, 0)

    @property
    def commitment_band(self) -> str:
        return CommitmentBand.for_total(self.commitment_total)

    @property
    def has_uploaded_picture(self) -> bool:
        return UserProfilePicture.objects.filter(profile=self).exists()

    @property
    def picture_path(self) -> str | None:
        try:
            picture = self.uploaded_picture
        except UserProfilePicture.DoesNotExist:
            return self.picture
        return reverse(
            "user-picture-image",
            kwargs={"user_id": self.user_id, "content_hash": picture.content_hash},
        )

    def picture_url(self, request=None) -> str | None:
        path = self.picture_path
        if path is None or request is None:
            return path
        return request.build_absolute_uri(path)


class UserProfilePictureManager(models.Manager):
    def store(self, profile, data, content_type):
        with transaction.atomic():
            self.filter(profile=profile).delete()
            picture = self.create(
                profile=profile,
                content_type=content_type,
                content_hash=hashlib.sha256(data).hexdigest(),
            )
            UserProfilePictureContent.objects.create(picture=picture, data=data)
        return picture


class UserProfilePicture(BaseModel):
    objects = UserProfilePictureManager()
    profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="uploaded_picture"
    )
    content_type = models.CharField(max_length=20)
    content_hash = models.CharField(max_length=64, editable=False)

    def __str__(self):
        return f"{self.profile.name} picture"


class UserProfilePictureContent(BaseModel):
    picture = models.OneToOneField(
        UserProfilePicture, on_delete=models.CASCADE, related_name="content"
    )
    data = models.BinaryField()

    def __str__(self):
        return f"{self.picture} content"
