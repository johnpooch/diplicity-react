import hashlib

from django.apps import apps
from django.contrib.auth.models import User
from django.db import models, transaction
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone

from common.constants import GameStatus, PhaseStatus, UserKind
from common.models import BaseModel
from member.models import Member, commitment_points


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

    def with_commitment_total(self):
        return self.annotate(
            commitment_total=commitment_points(
                "user__members__commitment_entries__kind"
            )
        )


class UserProfileManager(models.Manager):

    def delete_profiles(self, profiles):
        user_ids = tuple(profiles.values_list("user_id", flat=True))
        result = profiles.delete()
        apps.get_model("game", "Game").objects.bump_versions_for_users(user_ids)
        return result

    def save_profile(self, profile, **kwargs):
        profile.save(**kwargs)
        apps.get_model("game", "Game").objects.bump_versions_for_users(
            [profile.user_id]
        )
        return profile

    def delete_account(self, user):
        Game = apps.get_model("game", "Game")
        PhaseState = apps.get_model("phase", "PhaseState")
        with transaction.atomic():
            Game.objects.bump_versions_for_users([user.pk])
            user_members = Member.objects.filter(user=user)
            unstarted_statuses = [GameStatus.PENDING, GameStatus.MUSTERING]
            pending_game_ids = list(
                user_members.filter(game__status__in=unstarted_statuses).values_list(
                    "game_id", flat=True
                )
            )
            Member.objects.delete_members(
                user_members.filter(game__status__in=unstarted_statuses)
            )
            ongoing_members = user_members.filter(
                game__status__in=[GameStatus.ACTIVE, GameStatus.COMPLETED]
            )
            ongoing_members.holding_seat().update(removed_at=timezone.now())
            PhaseState.objects.filter(
                member__in=ongoing_members, phase__status=PhaseStatus.ACTIVE
            ).update(has_possible_orders=False)
            for game in Game.objects.filter(id__in=pending_game_ids):
                game.return_to_pending()
                game.delete_if_empty_pending()
            user.delete()

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
        return self.kind != UserKind.HUMAN

    @cached_property
    def commitment_total(self):
        return Member.objects.commitment_totals([self.user_id]).get(self.user_id, 0)

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

    def remove_for_profiles(self, profiles):
        user_ids = tuple(profiles.values_list("user_id", flat=True))
        self.filter(profile__in=profiles).delete()
        apps.get_model("game", "Game").objects.bump_versions_for_users(user_ids)

    def store(self, profile, data, content_type):
        with transaction.atomic():
            self.filter(profile=profile).delete()
            picture = self.create(
                profile=profile,
                content_type=content_type,
                content_hash=hashlib.sha256(data).hexdigest(),
            )
            UserProfilePictureContent.objects.create(picture=picture, data=data)
            apps.get_model("game", "Game").objects.bump_versions_for_users(
                [profile.user_id]
            )
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
