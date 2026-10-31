import io
from datetime import timedelta

import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from PIL import Image
from adjudicator import service as adjudication_service
from common.constants import (
    Commitment,
    CommitmentBand,
    CommitmentEvent,
    CommitmentShade,
    GameStatus,
    MemberKind,
    PhaseStatus,
    PhaseType,
)
from game.models import Game
from phase.models import Phase, PhaseState
from user_profile.commitment import (
    clamp_post_civil_disorder,
    get_rated_outcomes,
    recompute_commitment,
    score_commitment,
)
from user_profile.models import UserProfile, UserProfilePicture
from user_profile.utils import PICTURE_MAX_BYTES, PICTURE_MAX_DIMENSION, PICTURE_SIZE
from member.models import CommitmentEntry, Member
from victory.models import Victory

User = get_user_model()

EXIF_ORIENTATION_TAG = 0x0112
EXIF_GPS_IFD_TAG = 0x8825


class TestUserProfileRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_user_profile_success(self, authenticated_client, primary_user):
        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == primary_user.profile.name
        assert response.data["picture"] == primary_user.profile.picture
        assert response.data["email"] == primary_user.email

    @pytest.mark.django_db
    def test_retrieve_user_profile_unauthenticated(self, unauthenticated_client):
        url = reverse("user-profile")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_user_profile_with_null_picture(
        self, authenticated_client, primary_user
    ):
        primary_user.profile.picture = None
        primary_user.profile.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["picture"] is None
        assert response.data["name"] == primary_user.profile.name
        assert response.data["email"] == primary_user.email


class TestPublicUserProfileCommitment:

    def _retrieve(self, client, user):
        return client.get(reverse("public-user-profile", kwargs={"user_id": user.id}))

    def _member(self, user, variant, **game_fields):
        game = Game.objects.create(
            variant=variant,
            name="Commitment Game",
            status=GameStatus.ACTIVE,
            **game_fields,
        )
        return game.members.create(user=user)

    def _record(self, member, *kinds):
        CommitmentEntry.objects.bulk_create(
            [CommitmentEntry(member=member, kind=kind) for kind in kinds]
        )

    @pytest.mark.django_db
    def test_player_without_games_has_no_squares(
        self, authenticated_client, secondary_user
    ):
        response = self._retrieve(authenticated_client, secondary_user)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["commitment_total"] == 0
        assert response.data["commitment_band"] == CommitmentBand.NEUTRAL
        assert response.data["commitment_squares"] == []

    @pytest.mark.django_db
    def test_reports_a_square_per_game_and_their_total(
        self, authenticated_client, secondary_user, classical_variant
    ):
        played = self._member(secondary_user, classical_variant)
        self._record(played, *[CommitmentEvent.SUBMITTED] * 6, CommitmentEvent.NMR)
        abandoned = self._member(secondary_user, classical_variant)
        self._record(
            abandoned,
            CommitmentEvent.SUBMITTED,
            CommitmentEvent.NMR,
            CommitmentEvent.NMR,
            CommitmentEvent.CIVIL_DISORDER,
        )
        self._member(secondary_user, classical_variant)

        response = self._retrieve(authenticated_client, secondary_user)

        assert response.data["commitment_total"] == -9
        assert response.data["commitment_band"] == CommitmentBand.RED
        assert response.data["commitment_squares"] == [
            {
                "anonymous": False,
                "game_name": "Commitment Game",
                "submitted": 6,
                "missed": 1,
                "breakdown": [
                    {"kind": CommitmentEvent.SUBMITTED, "count": 6, "points": 6},
                    {"kind": CommitmentEvent.NMR, "count": 1, "points": -2},
                ],
                "points": 4,
                "shade": CommitmentShade.LIGHT_GREEN,
            },
            {
                "anonymous": False,
                "game_name": "Commitment Game",
                "submitted": 1,
                "missed": 2,
                "breakdown": [
                    {"kind": CommitmentEvent.SUBMITTED, "count": 1, "points": 1},
                    {"kind": CommitmentEvent.NMR, "count": 2, "points": -4},
                    {
                        "kind": CommitmentEvent.CIVIL_DISORDER,
                        "count": 1,
                        "points": -10,
                    },
                ],
                "points": -13,
                "shade": CommitmentShade.RED,
            },
            {
                "anonymous": False,
                "game_name": "Commitment Game",
                "submitted": 0,
                "missed": 0,
                "breakdown": [],
                "points": 0,
                "shade": CommitmentShade.GREY,
            },
        ]

    @pytest.mark.django_db
    def test_breakdown_lists_events_in_the_order_they_happen_in_a_game(
        self, authenticated_client, secondary_user, classical_variant
    ):
        member = self._member(secondary_user, classical_variant)
        self._record(
            member,
            CommitmentEvent.EARLY_WITHDRAWAL,
            CommitmentEvent.NMR,
            CommitmentEvent.SUBMITTED,
            CommitmentEvent.MUSTER_NO_SHOW,
        )

        response = self._retrieve(authenticated_client, secondary_user)

        assert [
            row["kind"] for row in response.data["commitment_squares"][0]["breakdown"]
        ] == [
            CommitmentEvent.MUSTER_NO_SHOW,
            CommitmentEvent.SUBMITTED,
            CommitmentEvent.NMR,
            CommitmentEvent.EARLY_WITHDRAWAL,
        ]

    @pytest.mark.django_db
    def test_anonymous_game_square_hides_the_game_name(
        self, authenticated_client, secondary_user, classical_variant
    ):
        self._member(secondary_user, classical_variant, anonymous=True)

        response = self._retrieve(authenticated_client, secondary_user)

        square = response.data["commitment_squares"][0]
        assert square["anonymous"] is True
        assert square["game_name"] is None

    @pytest.mark.django_db
    def test_finished_anonymous_game_square_shows_the_game_name(
        self, authenticated_client, secondary_user, classical_variant
    ):
        member = self._member(secondary_user, classical_variant, anonymous=True)
        member.game.status = GameStatus.COMPLETED
        member.game.save()

        response = self._retrieve(authenticated_client, secondary_user)

        square = response.data["commitment_squares"][0]
        assert square["anonymous"] is False
        assert square["game_name"] == "Commitment Game"

    @pytest.mark.django_db
    @pytest.mark.parametrize("excluded", ["private", "sandbox"])
    def test_unrated_games_have_no_square(
        self, authenticated_client, secondary_user, classical_variant, excluded
    ):
        self._member(secondary_user, classical_variant, **{excluded: True})

        response = self._retrieve(authenticated_client, secondary_user)

        assert response.data["commitment_squares"] == []


class TestCommitmentBands:

    @pytest.mark.parametrize(
        ("total", "band"),
        [
            (-21, CommitmentBand.DARK_RED),
            (-20, CommitmentBand.RED),
            (-1, CommitmentBand.RED),
            (0, CommitmentBand.NEUTRAL),
            (10, CommitmentBand.NEUTRAL),
            (11, CommitmentBand.LIGHT_GREEN),
            (49, CommitmentBand.LIGHT_GREEN),
            (50, CommitmentBand.GREEN),
            (199, CommitmentBand.GREEN),
            (200, CommitmentBand.DARK_GREEN),
        ],
    )
    def test_band_for_total(self, total, band):
        assert CommitmentBand.for_total(total) == band

    @pytest.mark.parametrize(
        ("points", "shade"),
        [
            (-14, CommitmentShade.DARK_RED),
            (-13, CommitmentShade.RED),
            (-5, CommitmentShade.RED),
            (-4, CommitmentShade.LIGHT_RED),
            (-1, CommitmentShade.LIGHT_RED),
            (0, CommitmentShade.GREY),
            (1, CommitmentShade.LIGHT_GREEN),
            (10, CommitmentShade.LIGHT_GREEN),
            (11, CommitmentShade.GREEN),
            (24, CommitmentShade.GREEN),
            (25, CommitmentShade.DARK_GREEN),
        ],
    )
    def test_shade_for_points(self, points, shade):
        assert CommitmentShade.for_points(points) == shade


class TestUserProfileUpdateView:

    @pytest.mark.django_db
    def test_update_user_profile_name_success(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        new_name = "Updated Name"
        response = authenticated_client.patch(url, {"name": new_name}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == new_name
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.name == new_name

    @pytest.mark.django_db
    def test_update_user_profile_name_too_short(
        self, authenticated_client, primary_user
    ):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "A"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_numbers(
        self, authenticated_client, primary_user
    ):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name123"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_special_chars(
        self, authenticated_client, primary_user
    ):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name@#$"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_valid_chars(
        self, authenticated_client, primary_user
    ):
        url = reverse("user-profile-update")
        valid_names = ["Mary-Jane", "O'Brien", "Jean-Pierre", "María García"]

        for name in valid_names:
            response = authenticated_client.patch(url, {"name": name}, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == name

    @pytest.mark.django_db
    def test_update_user_profile_unauthenticated(self, unauthenticated_client):
        url = reverse("user-profile-update")
        response = unauthenticated_client.patch(
            url, {"name": "New Name"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_update_user_profile_strips_whitespace(
        self, authenticated_client, primary_user
    ):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"name": "  Trimmed Name  "}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Trimmed Name"


class TestUserAccountDelete:

    @pytest.mark.django_db
    def test_delete_account_with_confirmation(
        self, user_factory, authenticated_client_factory
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        user_id = user.id

        url = reverse("user-delete")
        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=user_id).exists()
        assert not UserProfile.objects.filter(user_id=user_id).exists()

    @pytest.mark.django_db
    def test_pending_game_member_fully_removed(
        self,
        user_factory,
        authenticated_client_factory,
        base_pending_game_for_primary_user,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_pending_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        assert not Member.objects.filter(id=member.id).exists()

    @pytest.mark.django_db
    def test_active_game_member_preserved_with_removal_and_null_user(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.removed_at is not None
        assert member.user is None

    @pytest.mark.django_db
    def test_completed_game_member_preserved_with_removal_and_null_user(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        game.status = GameStatus.COMPLETED
        game.save()
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.removed_at is not None
        assert member.user is None

    @pytest.mark.django_db
    def test_member_already_off_the_seat_keeps_its_departure_time_on_delete(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        removed_at = timezone.now() - timedelta(days=1)
        member = game.members.create(user=user, removed_at=removed_at)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.removed_at == removed_at

    @pytest.mark.django_db
    def test_creator_of_active_game_cleared_on_delete(
        self, user_factory, authenticated_client_factory, classical_variant
    ):
        from game.models import Game
        from common.constants import GameStatus as GS

        user = user_factory()
        client = authenticated_client_factory(user)
        game = Game.objects.create(
            name="GM Delete Test",
            variant=classical_variant,
            status=GS.ACTIVE,
            created_by=user,
        )
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        game.refresh_from_db()
        assert game.created_by is None
        assert member.left_seat is True
        assert member.user is None

    @pytest.mark.django_db
    def test_pending_game_with_sole_user_is_deleted(
        self,
        user_factory,
        authenticated_client_factory,
        base_pending_game_for_primary_user,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_pending_game_for_primary_user
        game.members.create(user=user)
        game_id = game.id

        url = reverse("user-delete")
        client.delete(url)

        assert not Game.objects.filter(id=game_id).exists()

    @pytest.mark.django_db
    def test_current_phase_state_no_longer_has_possible_orders(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
        base_active_phase,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        phase = base_active_phase(game)
        member = game.members.create(user=user)
        phase_state = phase.phase_states.create(member=member, has_possible_orders=True)

        url = reverse("user-delete")
        client.delete(url)

        phase_state.refresh_from_db()
        assert phase_state.has_possible_orders is False

    @pytest.mark.django_db
    def test_completed_phase_state_is_untouched(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
        base_active_phase,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        phase = base_active_phase(game)
        phase.status = PhaseStatus.COMPLETED
        phase.save()
        member = game.members.create(user=user)
        phase_state = phase.phase_states.create(member=member, has_possible_orders=True)

        url = reverse("user-delete")
        client.delete(url)

        phase_state.refresh_from_db()
        assert phase_state.has_possible_orders is True

    @pytest.mark.django_db
    def test_deleted_member_no_longer_blocks_early_resolution(
        self,
        user_factory,
        authenticated_client_factory,
        active_game_with_confirmed_phase_state,
        classical_france_nation,
    ):
        game = active_game_with_confirmed_phase_state
        phase = game.current_phase
        user = user_factory()
        client = authenticated_client_factory(user)
        member = game.members.create(user=user, nation=classical_france_nation)
        phase.phase_states.create(member=member, has_possible_orders=True)

        assert not Phase.objects.filter_due_phases().filter(id=phase.id).exists()

        url = reverse("user-delete")
        client.delete(url)

        assert Phase.objects.filter_due_phases().filter(id=phase.id).exists()

    @pytest.mark.django_db
    def test_deleted_member_does_not_consume_nmr_extensions(
        self,
        user_factory,
        authenticated_client_factory,
        base_active_game_for_primary_user,
        base_active_phase,
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        phase = base_active_phase(game)
        phase.scheduled_resolution = timezone.now()
        phase.save()
        member = game.members.create(user=user, nmr_extensions_remaining=1)
        phase.phase_states.create(member=member, has_possible_orders=True)

        url = reverse("user-delete")
        client.delete(url)

        assert Phase.objects._apply_nmr_extensions(phase) is None
        member.refresh_from_db()
        assert member.nmr_extensions_remaining == 1

    @pytest.mark.django_db
    def test_pending_game_with_other_members_is_preserved(
        self,
        user_factory,
        authenticated_client_factory,
        base_pending_game_for_primary_user,
        secondary_user,
    ):
        user = user_factory()
        user_id = user.id
        client = authenticated_client_factory(user)
        game = base_pending_game_for_primary_user
        game.members.create(user=user)
        other_member = game.members.create(user=secondary_user)

        url = reverse("user-delete")
        client.delete(url)

        assert Game.objects.filter(id=game.id).exists()
        assert Member.objects.filter(id=other_member.id).exists()
        assert not Member.objects.filter(game=game, user_id=user_id).exists()


class TestWelcomeSandboxGameCreation:

    @pytest.mark.django_db
    def test_creating_user_profile_creates_sandbox_game(
        self, adjudication_data_classical, mock_immediate_on_commit
    ):
        with patch.object(
            adjudication_service, "start", return_value=adjudication_data_classical
        ):
            user = User.objects.create_user(
                username="newuser", email="new@example.com", password="testpass123"
            )
            UserProfile.objects.create(user=user, name="New User")

        sandbox_games = Game.objects.filter(sandbox=True, members__user=user).distinct()
        assert sandbox_games.count() == 1

        game = sandbox_games.first()
        assert game.name == "Practice Game"
        assert game.variant.id == "classical"

    @pytest.mark.django_db
    def test_does_not_create_duplicate_if_user_has_sandbox_game(
        self, classical_variant, adjudication_data_classical, mock_immediate_on_commit
    ):
        with patch.object(
            adjudication_service, "start", return_value=adjudication_data_classical
        ):
            user = User.objects.create_user(
                username="existingsandbox",
                email="existing@example.com",
                password="testpass123",
            )
            existing_game = Game.objects.create_sandbox(
                user=user,
                name="Existing Sandbox",
                variant=classical_variant,
            )
            UserProfile.objects.create(user=user, name="Existing Sandbox User")

        sandbox_games = Game.objects.filter(sandbox=True, members__user=user).distinct()
        assert sandbox_games.count() == 1
        assert sandbox_games.first().id == existing_game.id

    @pytest.mark.django_db
    def test_user_creation_succeeds_when_variant_missing(
        self, mock_immediate_on_commit
    ):
        from variant.models import Variant

        with patch.object(Variant.objects, "with_game_creation_data") as mock_qs:
            mock_qs.return_value = Variant.objects.none()
            user = User.objects.create_user(
                username="novariant",
                email="novariant@example.com",
                password="testpass123",
            )
            UserProfile.objects.create(user=user, name="No Variant User")

        assert UserProfile.objects.filter(user=user).exists()
        sandbox_games = Game.objects.filter(sandbox=True, members__user=user).distinct()
        assert sandbox_games.count() == 0

    @pytest.mark.django_db
    def test_user_creation_succeeds_when_game_creation_fails(
        self, mock_immediate_on_commit
    ):
        with patch.object(
            Game.objects, "create_sandbox", side_effect=Exception("boom")
        ):
            user = User.objects.create_user(
                username="failedgame", email="fail@example.com", password="testpass123"
            )
            UserProfile.objects.create(user=user, name="Failed Game User")

        assert UserProfile.objects.filter(user=user).exists()


class TestUserProfilePictureView:

    @pytest.mark.django_db
    def test_upload_picture_requires_authentication(
        self, unauthenticated_client, make_upload
    ):
        response = unauthenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_delete_picture_requires_authentication(self, unauthenticated_client):
        response = unauthenticated_client.delete(reverse("user-picture"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_upload_picture_returns_profile_with_picture_url(
        self, authenticated_client, primary_user, make_upload
    ):
        response = authenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )

        assert response.status_code == status.HTTP_200_OK
        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        assert response.data["picture"].endswith(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": picture.content_hash,
                },
            )
        )
        assert response.data["picture"].startswith("http://")

    @pytest.mark.django_db
    def test_uploaded_picture_replaces_google_url_on_public_profile(
        self, authenticated_client, primary_user, make_upload
    ):
        primary_user.profile.picture = "http://example.com/google.jpg"
        primary_user.profile.save()

        authenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )
        response = authenticated_client.get(
            reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["picture"].endswith(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": picture.content_hash,
                },
            )
        )

    @pytest.mark.django_db
    def test_upload_picture_normalises_to_square(
        self, authenticated_client, primary_user, make_upload
    ):
        authenticated_client.put(
            reverse("user-picture"), make_upload(image_format="PNG"), format="multipart"
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        stored = Image.open(io.BytesIO(picture.content.data))
        assert stored.size == (PICTURE_SIZE, PICTURE_SIZE)

    @pytest.mark.django_db
    def test_upload_picture_centre_crops(
        self, authenticated_client, primary_user, make_upload
    ):
        authenticated_client.put(
            reverse("user-picture"), make_upload(image_format="PNG"), format="multipart"
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        stored = Image.open(io.BytesIO(picture.content.data)).convert("RGB")
        assert stored.getpixel((PICTURE_SIZE // 4, PICTURE_SIZE // 2)) == (255, 0, 0)
        assert stored.getpixel((3 * PICTURE_SIZE // 4, PICTURE_SIZE // 2)) == (
            0,
            0,
            255,
        )

    @pytest.mark.django_db
    def test_upload_picture_honours_exif_orientation(
        self, authenticated_client, primary_user, make_image, make_upload
    ):
        exif = Image.Exif()
        exif[EXIF_ORIENTATION_TAG] = 6
        rotated = make_image().transpose(Image.Transpose.ROTATE_90)

        authenticated_client.put(
            reverse("user-picture"),
            make_upload(image_format="JPEG", image=rotated, exif=exif.tobytes()),
            format="multipart",
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        stored = Image.open(io.BytesIO(picture.content.data)).convert("RGB")
        left = stored.getpixel((PICTURE_SIZE // 4, PICTURE_SIZE // 2))
        right = stored.getpixel((3 * PICTURE_SIZE // 4, PICTURE_SIZE // 2))
        assert left[0] > 200 and left[2] < 60
        assert right[2] > 200 and right[0] < 60

    @pytest.mark.django_db
    def test_upload_picture_strips_metadata(
        self, authenticated_client, primary_user, make_image, make_upload
    ):
        exif = Image.Exif()
        exif[EXIF_ORIENTATION_TAG] = 1
        exif[EXIF_GPS_IFD_TAG] = {1: "N"}

        authenticated_client.put(
            reverse("user-picture"),
            make_upload(image_format="JPEG", exif=exif.tobytes()),
            format="multipart",
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        stored = Image.open(io.BytesIO(picture.content.data))
        assert stored.getexif() == {}

    @pytest.mark.django_db
    def test_upload_picture_replaces_existing_picture(
        self, authenticated_client, primary_user, make_image, make_upload
    ):
        first = authenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )
        second = authenticated_client.put(
            reverse("user-picture"),
            make_upload(image=make_image(left="#00ff00", right="#00ff00")),
            format="multipart",
        )

        assert second.status_code == status.HTTP_200_OK
        assert first.data["picture"] != second.data["picture"]
        assert (
            UserProfilePicture.objects.filter(profile=primary_user.profile).count() == 1
        )

    @pytest.mark.django_db
    def test_upload_picture_stops_serving_replaced_image(
        self, authenticated_client, make_image, make_upload
    ):
        first = authenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )
        second = authenticated_client.put(
            reverse("user-picture"),
            make_upload(image=make_image(left="#00ff00", right="#00ff00")),
            format="multipart",
        )

        assert (
            authenticated_client.get(first.data["picture"]).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            authenticated_client.get(second.data["picture"]).status_code
            == status.HTTP_200_OK
        )

    @pytest.mark.django_db
    def test_upload_picture_preserves_png_transparency(
        self, authenticated_client, primary_user, make_upload
    ):
        transparent = Image.new("RGBA", (512, 256), (255, 0, 0, 0))

        authenticated_client.put(
            reverse("user-picture"),
            make_upload(image_format="PNG", image=transparent),
            format="multipart",
        )

        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        assert picture.content_type == "image/png"
        assert Image.open(io.BytesIO(picture.content.data)).mode == "RGBA"

    @pytest.mark.django_db
    def test_upload_webp_picture(self, authenticated_client, primary_user, make_upload):
        response = authenticated_client.put(
            reverse("user-picture"),
            make_upload(image_format="WEBP"),
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        picture = UserProfilePicture.objects.get(profile=primary_user.profile)
        assert picture.content_type == "image/webp"

    @pytest.mark.django_db
    def test_upload_svg_rejected(self, authenticated_client, primary_user):
        upload = SimpleUploadedFile(
            "picture.svg",
            b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>',
            "image/svg+xml",
        )

        response = authenticated_client.put(
            reverse("user-picture"), {"picture": upload}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not UserProfilePicture.objects.filter(
            profile=primary_user.profile
        ).exists()

    @pytest.mark.django_db
    def test_upload_gif_rejected(self, authenticated_client, make_upload):
        response = authenticated_client.put(
            reverse("user-picture"), make_upload(image_format="GIF"), format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "JPEG, PNG or WebP" in str(response.data["picture"])

    @pytest.mark.django_db
    def test_upload_non_image_rejected(self, authenticated_client):
        upload = SimpleUploadedFile("picture.png", b"not an image at all", "image/png")

        response = authenticated_client.put(
            reverse("user-picture"), {"picture": upload}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_upload_over_size_limit_rejected(self, authenticated_client):
        upload = SimpleUploadedFile(
            "picture.png", b"0" * (PICTURE_MAX_BYTES + 1), "image/png"
        )

        response = authenticated_client.put(
            reverse("user-picture"), {"picture": upload}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too large" in str(response.data["picture"])

    @pytest.mark.django_db
    def test_upload_over_dimension_limit_rejected(
        self, authenticated_client, make_upload
    ):
        oversized = Image.new("RGB", (PICTURE_MAX_DIMENSION + 1, 10), "#ff0000")

        response = authenticated_client.put(
            reverse("user-picture"),
            make_upload(image_format="PNG", image=oversized),
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(PICTURE_MAX_DIMENSION) in str(response.data["picture"])

    @pytest.mark.django_db
    def test_upload_without_a_file_rejected(self, authenticated_client):
        response = authenticated_client.put(
            reverse("user-picture"), {}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_delete_picture_falls_back_to_google_url(
        self, authenticated_client, primary_user, make_upload
    ):
        primary_user.profile.picture = "http://example.com/google.jpg"
        primary_user.profile.save()
        authenticated_client.put(
            reverse("user-picture"), make_upload(), format="multipart"
        )

        response = authenticated_client.delete(reverse("user-picture"))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserProfilePicture.objects.filter(
            profile=primary_user.profile
        ).exists()
        profile_response = authenticated_client.get(reverse("user-profile"))
        assert profile_response.data["picture"] == "http://example.com/google.jpg"

    @pytest.mark.django_db
    def test_delete_picture_when_none_set(self, authenticated_client, primary_user):
        response = authenticated_client.delete(reverse("user-picture"))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserProfilePicture.objects.filter(
            profile=primary_user.profile
        ).exists()


class TestUserProfilePictureImageView:

    @pytest.mark.django_db
    def test_serves_picture_for_a_valid_hash(
        self, unauthenticated_client, primary_user, stored_picture
    ):
        response = unauthenticated_client.get(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": stored_picture.content_hash,
                },
            )
        )

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "image/png"
        assert response.content == bytes(stored_picture.content.data)

    @pytest.mark.django_db
    def test_sets_immutable_cache_control(
        self, unauthenticated_client, primary_user, stored_picture
    ):
        response = unauthenticated_client.get(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": stored_picture.content_hash,
                },
            )
        )

        assert "immutable" in response["Cache-Control"]
        assert "max-age=31536000" in response["Cache-Control"]

    @pytest.mark.django_db
    def test_sets_locked_down_content_security_policy(
        self, unauthenticated_client, primary_user, stored_picture
    ):
        response = unauthenticated_client.get(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": stored_picture.content_hash,
                },
            )
        )

        assert response["Content-Security-Policy"] == (
            "default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:"
        )

    @pytest.mark.django_db
    def test_unknown_hash_returns_404(
        self, unauthenticated_client, primary_user, stored_picture
    ):
        response = unauthenticated_client.get(
            reverse(
                "user-picture-image",
                kwargs={"user_id": primary_user.id, "content_hash": "x" * 64},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_hash_of_another_user_returns_404(
        self, unauthenticated_client, secondary_user, stored_picture
    ):
        response = unauthenticated_client.get(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": secondary_user.id,
                    "content_hash": stored_picture.content_hash,
                },
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


def _clear_uploaded_picture(client, profile, follow=True):
    return client.post(
        reverse("admin:user_profile_userprofile_changelist"),
        {
            "action": "clear_uploaded_picture",
            "_selected_action": [str(profile.pk)],
        },
        follow=follow,
    )


class TestUserProfileAdmin:

    @pytest.mark.django_db
    def test_clear_uploaded_picture_falls_back_to_google_url(
        self, admin_client, primary_user, stored_picture
    ):
        primary_user.profile.picture = "http://example.com/google.jpg"
        primary_user.profile.save()

        response = _clear_uploaded_picture(admin_client, primary_user.profile)

        assert response.status_code == status.HTTP_200_OK
        assert not UserProfilePicture.objects.filter(
            profile=primary_user.profile
        ).exists()
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.picture_url() == "http://example.com/google.jpg"

    @pytest.mark.django_db
    def test_clear_uploaded_picture_stops_serving_image(
        self, admin_client, primary_user, stored_picture
    ):
        url = reverse(
            "user-picture-image",
            kwargs={
                "user_id": primary_user.id,
                "content_hash": stored_picture.content_hash,
            },
        )
        assert admin_client.get(url).status_code == status.HTTP_200_OK

        _clear_uploaded_picture(admin_client, primary_user.profile)

        assert admin_client.get(url).status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_clear_uploaded_picture_leaves_other_profiles_untouched(
        self, admin_client, primary_user, secondary_user, stored_picture
    ):
        _clear_uploaded_picture(admin_client, secondary_user.profile)

        assert UserProfilePicture.objects.filter(profile=primary_user.profile).exists()

    @pytest.mark.django_db
    def test_clear_uploaded_picture_when_no_picture_uploaded(
        self, admin_client, secondary_user
    ):
        response = _clear_uploaded_picture(admin_client, secondary_user.profile)

        assert response.status_code == status.HTTP_200_OK
        assert not UserProfilePicture.objects.filter(
            profile=secondary_user.profile
        ).exists()

    @pytest.mark.django_db
    def test_clear_uploaded_picture_requires_staff(
        self, client, primary_user, stored_picture
    ):
        client.force_login(primary_user)

        response = _clear_uploaded_picture(client, primary_user.profile, follow=False)

        assert response.status_code == status.HTTP_302_FOUND
        assert UserProfilePicture.objects.filter(profile=primary_user.profile).exists()


class TestPublicUserProfileRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_public_profile_success(self, authenticated_client, primary_user):
        url = reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        response = authenticated_client.get(url)

        primary_user.profile.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == primary_user.id
        assert response.data["name"] == primary_user.profile.name
        assert response.data["picture"] == primary_user.profile.picture
        assert "created_at" in response.data
        assert "email" not in response.data

    @pytest.mark.django_db
    def test_retrieve_public_profile_unauthenticated(
        self, unauthenticated_client, primary_user
    ):
        url = reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_public_profile_not_found(self, authenticated_client):
        url = reverse("public-user-profile", kwargs={"user_id": 99999})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_new_player_stats(self, authenticated_client, primary_user):
        url = reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 0
        assert response.data["active_games"] == 0
        for removed in ["solo_wins", "draws", "losses", "nmr_rate", "cd_rate"]:
            assert removed not in response.data

    @pytest.mark.django_db
    def test_counts_finished_and_active_games(
        self, authenticated_client, secondary_user, classical_variant
    ):
        def join(game_status, **member_fields):
            game = Game.objects.create(
                name="Stats Game", variant=classical_variant, status=game_status
            )
            return game.members.create(user=secondary_user, **member_fields)

        join(GameStatus.COMPLETED)
        join(GameStatus.COMPLETED, drew=True)
        join(GameStatus.COMPLETED, kind=MemberKind.GAME_MASTER)
        join(GameStatus.ACTIVE)
        join(GameStatus.ACTIVE, civil_disorder_at=timezone.now())
        join(GameStatus.ACTIVE, withdrawn_at=timezone.now())
        join(GameStatus.ACTIVE, removed_at=timezone.now())
        join(GameStatus.PENDING)

        url = reverse("public-user-profile", kwargs={"user_id": secondary_user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 2
        assert response.data["active_games"] == 1

    @pytest.mark.django_db
    @pytest.mark.parametrize("game_status", [GameStatus.ACTIVE, GameStatus.COMPLETED])
    def test_sandbox_games_excluded_from_stats(
        self, authenticated_client, secondary_user, classical_variant, game_status
    ):
        game = Game.objects.create(
            name="Sandbox Game",
            variant=classical_variant,
            status=game_status,
            sandbox=True,
        )
        game.members.create(user=secondary_user)

        url = reverse("public-user-profile", kwargs={"user_id": secondary_user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 0
        assert response.data["active_games"] == 0

    @pytest.mark.django_db
    def test_kicked_members_excluded_from_stats(
        self, authenticated_client, secondary_user, classical_variant
    ):
        game = Game.objects.create(
            name="Kicked Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
        )
        game.members.create(user=secondary_user, removed_at=timezone.now())

        url = reverse("public-user-profile", kwargs={"user_id": secondary_user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 0

    @pytest.mark.django_db
    def test_withdrawn_game_counts_as_finished(
        self, authenticated_client, secondary_user, classical_variant
    ):
        game = Game.objects.create(
            name="Withdrawn Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
        )
        game.members.create(
            user=secondary_user,
            removed_at=timezone.now(),
            withdrawn_at=timezone.now(),
        )

        url = reverse("public-user-profile", kwargs={"user_id": secondary_user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 1

    @pytest.mark.django_db
    def test_can_view_other_users_profile(
        self,
        authenticated_client,
        secondary_user,
    ):
        url = reverse("public-user-profile", kwargs={"user_id": secondary_user.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == secondary_user.profile.name


RECEIVED = PhaseState.OrdersOutcome.RECEIVED
NMR = PhaseState.OrdersOutcome.NMR


class TestScoreCommitment:

    @pytest.mark.parametrize(
        "outcomes,expected",
        [
            ([], Commitment.UNDEFINED),
            ([RECEIVED] * 9, Commitment.UNDEFINED),
            ([RECEIVED] * 10, Commitment.HIGH),
            ([NMR] + [RECEIVED] * 9, Commitment.HIGH),
            ([NMR] * 2 + [RECEIVED] * 8, Commitment.MEDIUM),
            ([NMR] * 4 + [RECEIVED] * 6, Commitment.MEDIUM),
            ([NMR] * 5 + [RECEIVED] * 5, Commitment.LOW),
            ([NMR], Commitment.UNDEFINED),
            ([NMR] * 2, Commitment.LOW),
            ([NMR, RECEIVED, NMR], Commitment.LOW),
            ([RECEIVED] * 10 + [NMR] * 5, Commitment.HIGH),
        ],
    )
    def test_score_commitment(self, outcomes, expected):
        assert score_commitment(outcomes) == expected


class TestCanCreateCommittedGame:

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "total,expected", [(-3, False), (0, False), (9, False), (10, True), (11, True)]
    )
    def test_profile_reports_whether_user_can_create_committed_game(
        self, authenticated_client, primary_user, set_commitment_total, total, expected
    ):
        set_commitment_total(primary_user, total)

        response = authenticated_client.get(reverse("user-profile"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["commitment_total"] == total
        assert response.data["can_create_committed_game"] is expected


class TestRecomputeCommitment:

    def _build_history(
        self,
        user,
        variant,
        nation,
        outcomes,
        private=False,
        sandbox=False,
        removed=False,
        withdrawn_at=None,
        phase_type=PhaseType.MOVEMENT,
    ):
        game = Game.objects.create(
            name=f"History Game {Game.objects.count()}",
            variant=variant,
            status=GameStatus.ACTIVE,
            private=private,
            sandbox=sandbox,
        )
        member = game.members.create(
            user=user,
            nation=nation,
            removed_at=timezone.now() if removed else None,
            withdrawn_at=withdrawn_at,
        )
        for ordinal, outcome in enumerate(outcomes, start=1):
            phase = game.phases.create(
                variant=variant,
                season="Spring",
                year=1900 + ordinal,
                type=phase_type,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=outcome,
            )
        return game

    @pytest.mark.django_db
    def test_writes_stored_commitment(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED] * 10
        )
        assert recompute_commitment(user) == Commitment.HIGH
        user.profile.refresh_from_db()
        assert user.profile.commitment == Commitment.HIGH

    @pytest.mark.django_db
    def test_first_game_abandoner_scores_low(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED, NMR, NMR]
        )
        assert recompute_commitment(user) == Commitment.LOW

    @pytest.mark.django_db
    @pytest.mark.parametrize("exclusion", ["private", "sandbox", "removed"])
    def test_excluded_phases_not_rated(
        self, user_factory, classical_variant, classical_england_nation, exclusion
    ):
        user = user_factory()
        self._build_history(
            user,
            classical_variant,
            classical_england_nation,
            [NMR] * 5,
            **{exclusion: True},
        )
        assert recompute_commitment(user) == Commitment.UNDEFINED

    @pytest.mark.django_db
    def test_post_civil_disorder_phases_leave_rated_set(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user,
            classical_variant,
            classical_england_nation,
            [RECEIVED, NMR, NMR, NMR, NMR, NMR, NMR, NMR],
        )
        assert get_rated_outcomes(user) == [NMR, NMR, RECEIVED]

    @pytest.mark.django_db
    def test_withdrawn_member_keeps_outcomes_from_before_the_seat_was_taken_over(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user,
            classical_variant,
            classical_england_nation,
            [RECEIVED, NMR],
            removed=True,
            withdrawn_at=timezone.now(),
        )
        assert get_rated_outcomes(user) == [NMR, RECEIVED]

    @pytest.mark.django_db
    def test_non_movement_nmrs_do_not_trigger_clamp(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user,
            classical_variant,
            classical_england_nation,
            [NMR] * 4,
            phase_type=PhaseType.RETREAT,
        )
        assert len(get_rated_outcomes(user)) == 4

    @pytest.mark.django_db
    def test_rated_history_does_not_load_phase_options(
        self,
        user_factory,
        classical_variant,
        classical_england_nation,
        django_assert_num_queries,
    ):
        user = user_factory()
        self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED, NMR, NMR]
        )
        with patch(
            "user_profile.commitment.clamp_post_civil_disorder",
            wraps=clamp_post_civil_disorder,
        ) as clamp:
            with django_assert_num_queries(1):
                assert get_rated_outcomes(user) == [NMR, NMR, RECEIVED]
        states = clamp.call_args.args[0]
        assert len(states) == 3
        assert all("options" in state.phase.get_deferred_fields() for state in states)

    @pytest.mark.django_db
    def test_window_spans_multiple_games(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED] * 6
        )
        self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED] * 4
        )
        assert recompute_commitment(user) == Commitment.HIGH

    @pytest.mark.django_db
    def test_resolution_hook_writes_stored_commitment(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        game = self._build_history(
            user, classical_variant, classical_england_nation, [RECEIVED, NMR, NMR]
        )
        Phase.objects._recompute_commitment(game.phases.last())
        user.profile.refresh_from_db()
        assert user.profile.commitment == Commitment.LOW

    @pytest.mark.django_db
    def test_resolution_hook_skips_private_games(
        self, user_factory, classical_variant, classical_england_nation
    ):
        user = user_factory()
        game = self._build_history(
            user, classical_variant, classical_england_nation, [NMR, NMR], private=True
        )
        Phase.objects._recompute_commitment(game.phases.last())
        user.profile.refresh_from_db()
        assert user.profile.commitment == Commitment.UNDEFINED

    @pytest.mark.django_db
    def test_profile_serializes_commitment(
        self, authenticated_client, primary_user, set_commitment
    ):
        set_commitment(primary_user, Commitment.MEDIUM)

        response = authenticated_client.get(reverse("user-profile"))
        assert response.data["commitment"] == Commitment.MEDIUM

        response = authenticated_client.get(
            reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        )
        assert response.data["commitment"] == Commitment.MEDIUM


class TestCanCreateBotGamesFlag:

    @pytest.mark.django_db
    def test_profile_reports_allowed_user(self, authenticated_client, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        response = authenticated_client.get(reverse("user-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_create_bot_games"] is True

    @pytest.mark.django_db
    def test_profile_reports_disallowed_user(self, authenticated_client, settings):
        settings.BOT_OPPONENT_ALLOWLIST = []
        response = authenticated_client.get(reverse("user-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_create_bot_games"] is False


def _create_bot_seat_game(client, variant_id):
    response = client.post(
        reverse("game-create"),
        {
            "name": "Bot Seat Game",
            "variant_id": variant_id,
            "private": False,
            "deadline_mode": "duration",
            "movement_phase_duration": "24 hours",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


class TestAddableUserList:

    @pytest.mark.django_db
    def test_lists_bots_sorted_by_name(
        self, authenticated_client, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_bot_seat_game(authenticated_client, classical_variant.id)

        response = authenticated_client.get(
            reverse("game-addable-user-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        names = [user["name"] for user in response.data]
        assert names == sorted(names)
        assert all(user["user_id"] for user in response.data)

    @pytest.mark.django_db
    def test_excludes_humans(
        self, authenticated_client, classical_variant, secondary_user, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_bot_seat_game(authenticated_client, classical_variant.id)

        response = authenticated_client.get(
            reverse("game-addable-user-list", args=[game.id])
        )

        assert secondary_user.id not in [user["user_id"] for user in response.data]

    @pytest.mark.django_db
    def test_excludes_bots_already_in_the_game(
        self, authenticated_client, classical_variant, bot_user, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_bot_seat_game(authenticated_client, classical_variant.id)
        game.members.create(user=bot_user)

        response = authenticated_client.get(
            reverse("game-addable-user-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert bot_user.id not in [user["user_id"] for user in response.data]

    @pytest.mark.django_db
    def test_non_manager_forbidden(
        self,
        authenticated_client,
        authenticated_client_for_secondary_user,
        classical_variant,
        settings,
    ):
        settings.BOT_OPPONENT_ALLOWLIST = [
            "primary@example.com",
            "secondary@example.com",
        ]
        game = _create_bot_seat_game(authenticated_client, classical_variant.id)

        response = authenticated_client_for_secondary_user.get(
            reverse("game-addable-user-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_user_off_the_allowlist_forbidden(
        self, authenticated_client, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_bot_seat_game(authenticated_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.get(
            reverse("game-addable-user-list", args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_non_pending_game_forbidden(
        self, authenticated_client, active_game_created_by_primary_user, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]

        response = authenticated_client.get(
            reverse(
                "game-addable-user-list", args=[active_game_created_by_primary_user.id]
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
