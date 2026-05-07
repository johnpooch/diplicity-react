import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from adjudication import service as adjudication_service
from common.constants import (
    GameStatus,
    MemberOutcomeState,
    ReliabilityTier,
)
from game.models import Game
from user_profile.models import UserProfile
from user_profile.utils import backfill_reliability_data, recompute_reliability_counters
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


class TestReliabilityTierProperty:

    @pytest.mark.django_db
    def test_under_min_games_returns_new_player(self, primary_user):
        primary_user.profile.games_finished = 2
        primary_user.profile.games_abandoned_recent = 0
        assert primary_user.profile.reliability_tier == ReliabilityTier.NEW_PLAYER

    @pytest.mark.django_db
    def test_at_or_above_threshold_returns_unreliable(self, primary_user):
        primary_user.profile.games_finished = 5
        primary_user.profile.games_abandoned_recent = 2
        assert primary_user.profile.reliability_tier == ReliabilityTier.UNRELIABLE

    @pytest.mark.django_db
    def test_at_min_games_with_one_abandoned_returns_reliable(self, primary_user):
        primary_user.profile.games_finished = 3
        primary_user.profile.games_abandoned_recent = 1
        assert primary_user.profile.reliability_tier == ReliabilityTier.RELIABLE

    @pytest.mark.django_db
    def test_zero_abandoned_returns_reliable(self, primary_user):
        primary_user.profile.games_finished = 10
        primary_user.profile.games_abandoned_recent = 0
        assert primary_user.profile.reliability_tier == ReliabilityTier.RELIABLE


class TestRecomputeReliabilityCounters:

    def _make_finished_game(
        self,
        variant,
        status=GameStatus.COMPLETED,
        private=False,
        sandbox=False,
    ):
        return Game.objects.create(
            name="Tier Test Game",
            variant=variant,
            status=status,
            private=private,
            sandbox=sandbox,
        )

    @pytest.mark.django_db
    def test_counts_only_public_non_sandbox_finished_games(
        self, primary_user, classical_variant, classical_england_nation
    ):
        public_game = self._make_finished_game(classical_variant)
        public_game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            outcome_state=MemberOutcomeState.COMPLETED,
        )

        private_game = self._make_finished_game(classical_variant, private=True)
        private_game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            outcome_state=MemberOutcomeState.ABANDONED,
        )

        sandbox_game = self._make_finished_game(classical_variant, sandbox=True)
        sandbox_game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            outcome_state=MemberOutcomeState.ABANDONED,
        )

        recompute_reliability_counters(primary_user.id)
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 1
        assert primary_user.profile.games_abandoned_recent == 0

    @pytest.mark.django_db
    def test_counts_only_classified_members(
        self, primary_user, classical_variant, classical_england_nation
    ):
        finished_game = self._make_finished_game(classical_variant)
        finished_game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            outcome_state=MemberOutcomeState.COMPLETED,
        )

        unclassified_game = Game.objects.create(
            name="Active Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        unclassified_game.members.create(
            user=primary_user,
            nation=classical_england_nation,
        )

        recompute_reliability_counters(primary_user.id)
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 1

    @pytest.mark.django_db
    def test_window_caps_abandoned_count_at_last_ten(
        self, primary_user, classical_variant, classical_england_nation
    ):
        # 12 finished games — 6 oldest abandoned, 6 newest completed.
        # Window is last 10, so abandoned_recent should be 4 (the 4 abandoned games still in window).
        from django.utils import timezone as tz
        from datetime import timedelta

        base = tz.now()
        for i in range(12):
            game = Game.objects.create(
                name=f"Window Test {i}",
                variant=classical_variant,
                status=GameStatus.COMPLETED,
            )
            outcome = (
                MemberOutcomeState.ABANDONED if i < 6 else MemberOutcomeState.COMPLETED
            )
            game.members.create(
                user=primary_user,
                nation=classical_england_nation,
                outcome_state=outcome,
            )
            Game.objects.filter(pk=game.pk).update(updated_at=base + timedelta(minutes=i))

        recompute_reliability_counters(primary_user.id)
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 12
        assert primary_user.profile.games_abandoned_recent == 4


class TestUserProfileSerializerReliabilityFields:

    @pytest.mark.django_db
    def test_serializer_includes_tier_and_counters(self, authenticated_client, primary_user):
        primary_user.profile.games_finished = 7
        primary_user.profile.games_abandoned_recent = 1
        primary_user.profile.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["reliability_tier"] == ReliabilityTier.RELIABLE
        assert response.data["reliability_games_finished"] == 7
        assert response.data["reliability_games_abandoned_recent"] == 1

    @pytest.mark.django_db
    def test_serializer_defaults_to_new_player(self, authenticated_client, primary_user):
        primary_user.profile.games_finished = 0
        primary_user.profile.games_abandoned_recent = 0
        primary_user.profile.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.data["reliability_tier"] == ReliabilityTier.NEW_PLAYER


class TestClassifyOutcomesUpdatesCounters:

    @pytest.mark.django_db
    def test_classification_updates_user_counters(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from common.constants import PhaseStatus, PhaseType
        from member.utils import classify_outcomes_for_finished_game

        game = Game.objects.create(
            name="Counter Update Test",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
        )
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Three movement phases all NMR with units present → Abandoned
        from province.models import Province
        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)
        for ordinal in range(1, 4):
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1900 + ordinal,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.units.create(type="Fleet", nation=classical_england_nation, province=edinburgh)
            phase.phase_states.create(member=member, has_possible_orders=True)

        classify_outcomes_for_finished_game(game)
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 1
        assert primary_user.profile.games_abandoned_recent == 1

    @pytest.mark.django_db
    def test_private_game_does_not_update_counters(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from common.constants import PhaseStatus, PhaseType
        from member.utils import classify_outcomes_for_finished_game

        game = Game.objects.create(
            name="Private Counter Test",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            private=True,
        )
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        from province.models import Province
        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)
        for ordinal in range(1, 4):
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1900 + ordinal,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.units.create(type="Fleet", nation=classical_england_nation, province=edinburgh)
            phase.phase_states.create(member=member, has_possible_orders=True)

        classify_outcomes_for_finished_game(game)
        primary_user.profile.refresh_from_db()
        # Outcome state is still set on the member, but private games don't count toward counters
        assert primary_user.profile.games_finished == 0
        assert primary_user.profile.games_abandoned_recent == 0
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.ABANDONED


class TestBackfillReliabilityData:

    def _add_movement_phases(
        self, game, member, province, ordinals_with_orders
    ):
        from common.constants import PhaseStatus, PhaseType

        for ordinal, has_order in ordinals_with_orders:
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1900 + ordinal,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.units.create(type="Fleet", nation=member.nation, province=province)
            phase_state = phase.phase_states.create(member=member, has_possible_orders=True)
            if has_order:
                phase_state.orders.create(source=province, order_type="Hold")

    @pytest.mark.django_db
    def test_classifies_members_across_finished_public_games(
        self,
        primary_user,
        secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
    ):
        from province.models import Province

        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)
        paris = Province.objects.get(province_id="par", variant=classical_variant)

        # Game 1 — primary completes, secondary abandons
        game1 = Game.objects.create(
            name="Backfill Game 1", variant=classical_variant, status=GameStatus.COMPLETED
        )
        member1a = game1.members.create(user=primary_user, nation=classical_england_nation)
        member1b = game1.members.create(user=secondary_user, nation=classical_france_nation)
        self._add_movement_phases(
            game1, member1a, edinburgh, [(1, True), (2, True), (3, True)]
        )
        for ordinal in range(1, 4):
            phase = game1.phases.get(ordinal=ordinal)
            phase.units.create(type="Army", nation=classical_france_nation, province=paris)
            ps = phase.phase_states.create(member=member1b, has_possible_orders=True)

        # Game 2 — primary abandons (3 NMRs)
        game2 = Game.objects.create(
            name="Backfill Game 2", variant=classical_variant, status=GameStatus.COMPLETED
        )
        member2 = game2.members.create(user=primary_user, nation=classical_england_nation)
        self._add_movement_phases(
            game2, member2, edinburgh, [(1, False), (2, False), (3, False)]
        )

        backfill_reliability_data()

        member1a.refresh_from_db()
        member1b.refresh_from_db()
        member2.refresh_from_db()
        assert member1a.outcome_state == MemberOutcomeState.COMPLETED
        assert member1b.outcome_state == MemberOutcomeState.ABANDONED
        assert member2.outcome_state == MemberOutcomeState.ABANDONED

        primary_user.profile.refresh_from_db()
        secondary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 2
        assert primary_user.profile.games_abandoned_recent == 1
        assert secondary_user.profile.games_finished == 1
        assert secondary_user.profile.games_abandoned_recent == 1

    @pytest.mark.django_db
    def test_skips_sandbox_games(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from province.models import Province

        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)

        sandbox = Game.objects.create(
            name="Sandbox Backfill",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            sandbox=True,
        )
        member = sandbox.members.create(user=primary_user, nation=classical_england_nation)
        self._add_movement_phases(
            sandbox, member, edinburgh, [(1, False), (2, False), (3, False)]
        )

        backfill_reliability_data()
        member.refresh_from_db()
        assert member.outcome_state is None
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 0

    @pytest.mark.django_db
    def test_classifies_private_games_but_excludes_from_counters(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from province.models import Province

        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)

        private = Game.objects.create(
            name="Private Backfill",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            private=True,
        )
        member = private.members.create(user=primary_user, nation=classical_england_nation)
        self._add_movement_phases(
            private, member, edinburgh, [(1, False), (2, False), (3, False)]
        )

        backfill_reliability_data()
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.ABANDONED
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 0
        assert primary_user.profile.games_abandoned_recent == 0

    @pytest.mark.django_db
    def test_skips_in_progress_games(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from province.models import Province

        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)

        active = Game.objects.create(
            name="Active Backfill", variant=classical_variant, status=GameStatus.ACTIVE
        )
        member = active.members.create(user=primary_user, nation=classical_england_nation)
        self._add_movement_phases(
            active, member, edinburgh, [(1, False), (2, False), (3, False)]
        )

        backfill_reliability_data()
        member.refresh_from_db()
        assert member.outcome_state is None

    @pytest.mark.django_db
    def test_idempotent(
        self, primary_user, classical_variant, classical_england_nation
    ):
        from province.models import Province

        edinburgh = Province.objects.get(province_id="edi", variant=classical_variant)

        game = Game.objects.create(
            name="Idempotent Backfill",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
        )
        member = game.members.create(user=primary_user, nation=classical_england_nation)
        self._add_movement_phases(
            game, member, edinburgh, [(1, False), (2, False), (3, False)]
        )

        backfill_reliability_data()
        backfill_reliability_data()

        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.ABANDONED
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.games_finished == 1
        assert primary_user.profile.games_abandoned_recent == 1
