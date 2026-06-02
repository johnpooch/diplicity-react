import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from adjudication import service as adjudication_service
from game.models import Game
from user_profile.models import UserProfile
from member.models import Member

User = get_user_model()


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
    def test_retrieve_user_profile_with_null_picture(self, authenticated_client, primary_user):
        primary_user.profile.picture = None
        primary_user.profile.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["picture"] is None
        assert response.data["name"] == primary_user.profile.name
        assert response.data["email"] == primary_user.email


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
    def test_update_user_profile_name_too_short(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "A"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_numbers(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name123"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_special_chars(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name@#$"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_valid_chars(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        valid_names = ["Mary-Jane", "O'Brien", "Jean-Pierre", "María García"]

        for name in valid_names:
            response = authenticated_client.patch(url, {"name": name}, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == name

    @pytest.mark.django_db
    def test_update_user_profile_unauthenticated(self, unauthenticated_client):
        url = reverse("user-profile-update")
        response = unauthenticated_client.patch(url, {"name": "New Name"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_update_user_profile_strips_whitespace(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "  Trimmed Name  "}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Trimmed Name"

    @pytest.mark.django_db
    def test_retrieve_returns_colour_profile_fields(self, authenticated_client, primary_user):
        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["colour_profile_enabled"] is False
        assert isinstance(response.data["custom_colour_profile"], list)
        assert len(response.data["default_colour_profile"]) == 36

    @pytest.mark.django_db
    def test_update_colour_profile_enabled(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"colour_profile_enabled": True}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["colour_profile_enabled"] is True
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.colour_profile_enabled is True

    @pytest.mark.django_db
    def test_update_custom_colour_profile_valid(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        new_profile = ["#AABBCC"] * 36
        response = authenticated_client.patch(url, {"custom_colour_profile": new_profile}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["custom_colour_profile"] == new_profile
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.custom_colour_profile == new_profile

    @pytest.mark.django_db
    def test_update_custom_colour_profile_wrong_count(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"custom_colour_profile": ["#AABBCC"] * 5}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "custom_colour_profile" in response.data

    @pytest.mark.django_db
    def test_update_custom_colour_profile_invalid_hex(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        invalid_profile = ["#GGGGGG"] + ["#AABBCC"] * 35
        response = authenticated_client.patch(url, {"custom_colour_profile": invalid_profile}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "custom_colour_profile" in response.data


class TestUserAccountDelete:

    @pytest.mark.django_db
    def test_delete_account_with_confirmation(self, delete_user, delete_client):
        user = delete_user()
        client = delete_client(user)
        user_id = user.id

        url = reverse("user-delete")
        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=user_id).exists()
        assert not UserProfile.objects.filter(user_id=user_id).exists()

    @pytest.mark.django_db
    def test_pending_game_member_fully_removed(
        self, delete_user, delete_client, base_pending_game_for_primary_user
    ):
        user = delete_user()
        client = delete_client(user)
        game = base_pending_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        assert not Member.objects.filter(id=member.id).exists()

    @pytest.mark.django_db
    def test_active_game_member_preserved_with_kicked_and_null_user(
        self, delete_user, delete_client, base_active_game_for_primary_user
    ):
        user = delete_user()
        client = delete_client(user)
        game = base_active_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.kicked is True
        assert member.user is None

    @pytest.mark.django_db
    def test_game_master_of_active_game_preserved(
        self, delete_user, delete_client, classical_variant
    ):
        from game.models import Game
        from common.constants import GameStatus as GS

        user = delete_user()
        client = delete_client(user)
        game = Game.objects.create(
            name="GM Delete Test", variant=classical_variant, status=GS.ACTIVE
        )
        member = game.members.create(user=user, is_game_master=True)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.is_game_master is True
        assert member.kicked is True
        assert member.user is None

    @pytest.mark.django_db
    def test_pending_game_with_sole_user_is_deleted(
        self, delete_user, delete_client, base_pending_game_for_primary_user
    ):
        user = delete_user()
        client = delete_client(user)
        game = base_pending_game_for_primary_user
        game.members.create(user=user)
        game_id = game.id

        url = reverse("user-delete")
        client.delete(url)

        assert not Game.objects.filter(id=game_id).exists()

    @pytest.mark.django_db
    def test_pending_game_with_other_members_is_preserved(
        self, delete_user, delete_client, base_pending_game_for_primary_user, secondary_user
    ):
        user = delete_user()
        user_id = user.id
        client = delete_client(user)
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
        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
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
        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            user = User.objects.create_user(
                username="existingsandbox", email="existing@example.com", password="testpass123"
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
    def test_user_creation_succeeds_when_variant_missing(self, mock_immediate_on_commit):
        from variant.models import Variant

        with patch.object(Variant.objects, "with_game_creation_data") as mock_qs:
            mock_qs.return_value = Variant.objects.none()
            user = User.objects.create_user(
                username="novariant", email="novariant@example.com", password="testpass123"
            )
            UserProfile.objects.create(user=user, name="No Variant User")

        assert UserProfile.objects.filter(user=user).exists()
        sandbox_games = Game.objects.filter(sandbox=True, members__user=user).distinct()
        assert sandbox_games.count() == 0

    @pytest.mark.django_db
    def test_user_creation_succeeds_when_game_creation_fails(self, mock_immediate_on_commit):
        with patch.object(Game.objects, "create_sandbox", side_effect=Exception("boom")):
            user = User.objects.create_user(
                username="failedgame", email="fail@example.com", password="testpass123"
            )
            UserProfile.objects.create(user=user, name="Failed Game User")

        assert UserProfile.objects.filter(user=user).exists()
