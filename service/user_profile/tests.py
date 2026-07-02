import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from adjudication import service as adjudication_service
from common.constants import GameStatus, PhaseStatus, PhaseType
from game.models import Game
from phase.models import PhaseState
from user_profile.models import UserProfile
from member.models import Member
from victory.models import Victory

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
        assert response.data["email_notifications_enabled"] is False

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
    def test_enable_email_notifications(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"email_notifications_enabled": True}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email_notifications_enabled"] is True
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.email_notifications_enabled is True

    @pytest.mark.django_db
    def test_disable_email_notifications(self, authenticated_client, primary_user):
        primary_user.profile.email_notifications_enabled = True
        primary_user.profile.save()

        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"email_notifications_enabled": False}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email_notifications_enabled"] is False
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.email_notifications_enabled is False

    @pytest.mark.django_db
    def test_retrieve_colorblind_mode_defaults_to_null(self, authenticated_client):
        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["colorblind_mode"] is None

    @pytest.mark.django_db
    def test_set_colorblind_mode(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"colorblind_mode": "deuteranopia"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["colorblind_mode"] == "deuteranopia"
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.colorblind_mode == "deuteranopia"

    @pytest.mark.django_db
    def test_clear_colorblind_mode(self, authenticated_client, primary_user):
        primary_user.profile.colorblind_mode = "protanopia"
        primary_user.profile.save()

        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"colorblind_mode": None}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["colorblind_mode"] is None
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.colorblind_mode is None

    @pytest.mark.django_db
    def test_invalid_colorblind_mode(self, authenticated_client):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(
            url, {"colorblind_mode": "invalid_mode"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "colorblind_mode" in response.data


class TestUserAccountDelete:

    @pytest.mark.django_db
    def test_delete_account_with_confirmation(self, user_factory, authenticated_client_factory):
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
        self, user_factory, authenticated_client_factory, base_pending_game_for_primary_user
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_pending_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        assert not Member.objects.filter(id=member.id).exists()

    @pytest.mark.django_db
    def test_active_game_member_preserved_with_kicked_and_null_user(
        self, user_factory, authenticated_client_factory, base_active_game_for_primary_user
    ):
        user = user_factory()
        client = authenticated_client_factory(user)
        game = base_active_game_for_primary_user
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        assert member.kicked is True
        assert member.user is None

    @pytest.mark.django_db
    def test_creator_of_active_game_cleared_on_delete(
        self, user_factory, authenticated_client_factory, classical_variant
    ):
        from game.models import Game
        from common.constants import GameStatus as GS

        user = user_factory()
        client = authenticated_client_factory(user)
        game = Game.objects.create(
            name="GM Delete Test", variant=classical_variant, status=GS.ACTIVE, created_by=user
        )
        member = game.members.create(user=user)

        url = reverse("user-delete")
        client.delete(url)

        member.refresh_from_db()
        game.refresh_from_db()
        assert game.created_by is None
        assert member.kicked is True
        assert member.user is None

    @pytest.mark.django_db
    def test_pending_game_with_sole_user_is_deleted(
        self, user_factory, authenticated_client_factory, base_pending_game_for_primary_user
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
    def test_pending_game_with_other_members_is_preserved(
        self, user_factory, authenticated_client_factory, base_pending_game_for_primary_user, secondary_user
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
    def test_retrieve_public_profile_unauthenticated(self, unauthenticated_client, primary_user):
        url = reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_public_profile_not_found(self, authenticated_client):
        url = reverse("public-user-profile", kwargs={"user_id": 99999})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_new_player_reliability_tier(self, authenticated_client, primary_user):
        url = reverse("public-user-profile", kwargs={"user_id": primary_user.id})
        response = authenticated_client.get(url)

        assert response.data["reliability_tier"] == "new"
        assert response.data["total_games"] == 0
        assert response.data["solo_wins"] == 0
        assert response.data["draws"] == 0
        assert response.data["losses"] == 0
        assert response.data["nmr_rate"] == 0.0
        assert response.data["cd_rate"] == 0.0

    @pytest.mark.django_db
    def test_stats_with_completed_games(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="statsuser", email="stats@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Stats User")

        for i in range(10):
            game = Game.objects.create(
                name=f"Completed Game {i}",
                variant=classical_variant,
                status=GameStatus.COMPLETED,
                finished_at=timezone.now(),
            )
            member = game.members.create(
                user=user,
                nation=classical_england_nation,
                drew=(i in [1, 2]),
            )
            phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=1,
            )
            phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=PhaseState.OrdersOutcome.RECEIVED,
            )
            if i == 0:
                victory = Victory.objects.create(game=game, winning_phase=phase)
                victory.members.add(member)

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 10
        assert response.data["solo_wins"] == 1
        assert response.data["draws"] == 2
        assert response.data["losses"] == 7
        assert response.data["nmr_rate"] == 0.0
        assert response.data["cd_rate"] == 0.0
        assert response.data["reliability_tier"] == "reliable"

    @pytest.mark.django_db
    def test_nmr_rate_calculation(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="nmruser", email="nmr@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="NMR User")

        for i in range(10):
            game = Game.objects.create(
                name=f"NMR Game {i}",
                variant=classical_variant,
                status=GameStatus.COMPLETED,
                finished_at=timezone.now(),
            )
            member = game.members.create(user=user, nation=classical_england_nation)
            phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=1,
            )
            outcome = (
                PhaseState.OrdersOutcome.NMR if i < 3
                else PhaseState.OrdersOutcome.RECEIVED
            )
            phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=outcome,
            )

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["nmr_rate"] == 0.3
        assert response.data["reliability_tier"] is None

    @pytest.mark.django_db
    def test_cd_rate_calculation(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="cduser", email="cd@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="CD User")

        for i in range(10):
            game = Game.objects.create(
                name=f"CD Game {i}",
                variant=classical_variant,
                status=GameStatus.COMPLETED,
                finished_at=timezone.now(),
            )
            member = game.members.create(
                user=user,
                nation=classical_england_nation,
                civil_disorder=(i < 2),
            )
            phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=1,
            )
            phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=PhaseState.OrdersOutcome.RECEIVED,
            )

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["cd_rate"] == 0.2
        assert response.data["reliability_tier"] is None

    @pytest.mark.django_db
    def test_sandbox_games_excluded_from_stats(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="sandboxuser", email="sandbox@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Sandbox User")

        game = Game.objects.create(
            name="Sandbox Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
            sandbox=True,
        )
        member = game.members.create(user=user, nation=classical_england_nation)
        phase = game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=1,
        )
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(member)

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 0
        assert response.data["solo_wins"] == 0

    @pytest.mark.django_db
    def test_draw_with_solo_victory_counted_as_draw_not_solo_win(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="drawsolouser", email="drawsolo@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Draw Solo User")

        game = Game.objects.create(
            name="Draw With Solo Victory",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
        )
        member = game.members.create(
            user=user,
            nation=classical_england_nation,
            drew=True,
        )
        phase = game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=1,
        )
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(member)

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 1
        assert response.data["solo_wins"] == 0
        assert response.data["draws"] == 1
        assert response.data["losses"] == 0

    @pytest.mark.django_db
    def test_kicked_members_excluded_from_stats(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="kickeduser", email="kicked@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Kicked User")

        game = Game.objects.create(
            name="Kicked Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
        )
        game.members.create(
            user=user, nation=classical_england_nation, kicked=True
        )

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["total_games"] == 0

    @pytest.mark.django_db
    def test_retreat_phase_nmrs_count_toward_nmr_rate(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
    ):
        user = User.objects.create_user(
            username="movementuser", email="movement@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Movement User")

        for i in range(10):
            game = Game.objects.create(
                name=f"Movement Game {i}",
                variant=classical_variant,
                status=GameStatus.COMPLETED,
                finished_at=timezone.now(),
            )
            member = game.members.create(user=user, nation=classical_england_nation)
            movement_phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=1,
            )
            movement_phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=PhaseState.OrdersOutcome.RECEIVED,
            )
            retreat_phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.RETREAT,
                status=PhaseStatus.COMPLETED,
                ordinal=2,
            )
            retreat_phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=PhaseState.OrdersOutcome.NMR,
            )

        url = reverse("public-user-profile", kwargs={"user_id": user.id})
        response = authenticated_client.get(url)

        assert response.data["nmr_rate"] == 0.5
        assert response.data["reliability_tier"] is None

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


class TestTierAllowsMinReliability:

    @pytest.mark.parametrize(
        "tier,min_reliability,expected",
        [
            ("reliable", "open", True),
            ("reliable", "reliable_and_new", True),
            ("reliable", "reliable_only", True),
            ("new", "open", True),
            ("new", "reliable_and_new", True),
            ("new", "reliable_only", False),
            (None, "open", True),
            (None, "reliable_and_new", False),
            (None, "reliable_only", False),
        ],
    )
    def test_tier_allows_min_reliability(self, tier, min_reliability, expected):
        from user_profile.utils import tier_allows_min_reliability

        assert tier_allows_min_reliability(tier, min_reliability) is expected

    def test_unknown_min_reliability_fails_open(self):
        from user_profile.utils import tier_allows_min_reliability

        assert tier_allows_min_reliability(None, "something_else") is True


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
