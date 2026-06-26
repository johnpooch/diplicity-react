from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from common.constants import GameStatus
from game.models import Game
from member.models import Member
from user_profile.models import UserProfile

retrieve_viewname = "game-retrieve"
pause_viewname = "game-pause"
kick_viewname = "game-kick"

User = get_user_model()


@pytest.fixture
def player_run_active_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Player Run Game",
            status=GameStatus.ACTIVE,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[2])
        return game, primary_member, secondary_member, tertiary_member

    return _create


@pytest.fixture
def player_run_pending_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Player Run Pending Game",
            status=GameStatus.PENDING,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[2])
        return game, primary_member, secondary_member, tertiary_member

    return _create


@pytest.fixture
def game_master_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="GM Game",
            status=GameStatus.ACTIVE,
            created_by=primary_user,
            game_master=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        secondary_member = game.members.create(user=secondary_user, nation=nations[0])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[1])
        return game, secondary_member, tertiary_member

    return _create


@pytest.fixture
def sandbox_game_factory(db, classical_variant, primary_user, secondary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Sandbox Game",
            status=GameStatus.ACTIVE,
            sandbox=True,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        return game, primary_member, secondary_member

    return _create


class TestTransferManagementNoEligibleReplacement:

    @pytest.mark.django_db
    def test_no_transfer_when_all_other_members_in_civil_disorder(
        self, player_run_active_game_factory, primary_user
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        secondary_member.civil_disorder = True
        secondary_member.save()
        tertiary_member.civil_disorder = True
        tertiary_member.save()

        game.transfer_management_if_needed(primary_user)

        game.refresh_from_db()
        assert game.managing_member is None

    @pytest.mark.django_db
    def test_no_transfer_when_only_remaining_member_is_exiting_user(self, db, classical_variant, primary_user):
        game = Game.objects.create(
            variant=classical_variant,
            name="Solo Game",
            status=GameStatus.ACTIVE,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        game.members.create(user=primary_user, nation=nations[0])

        game.transfer_management_if_needed(primary_user)

        game.refresh_from_db()
        assert game.managing_member is None


class TestTransferManagementOnCivilDisorder:

    @pytest.mark.django_db
    def test_creator_enters_cd_transfers_to_eligible_member(
        self,
        player_run_active_game_factory,
        primary_user,
        secondary_user,
        tertiary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        primary_member.civil_disorder = True
        primary_member.save()

        game.transfer_management_if_needed(primary_user, reason="entered civil disorder")

        game.refresh_from_db()
        assert game.managing_member is not None
        assert game.managing_member.user_id in (secondary_user.id, tertiary_user.id)

    @pytest.mark.django_db
    def test_after_cd_transfer_to_only_eligible_member(
        self,
        player_run_active_game_factory,
        primary_user,
        secondary_user,
        tertiary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        primary_member.civil_disorder = True
        primary_member.save()
        secondary_member.civil_disorder = True
        secondary_member.save()

        game.transfer_management_if_needed(primary_user, reason="entered civil disorder")

        game.refresh_from_db()
        assert game.managing_member == tertiary_member
        assert game.can_manage(tertiary_user) is True

    @pytest.mark.django_db
    def test_after_cd_transfer_original_creator_cannot_manage(
        self,
        player_run_active_game_factory,
        primary_user,
        secondary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(primary_user, reason="entered civil disorder")

        game.refresh_from_db()
        assert game.can_manage(primary_user) is False

    @pytest.mark.django_db
    def test_cd_transfer_sends_notification(
        self,
        player_run_active_game_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(primary_user, reason="entered civil disorder")

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert call_kwargs["notification_type"] == "management_transfer"


class TestTransferManagementOnElimination:

    @pytest.mark.django_db
    def test_creator_eliminated_transfers_management(
        self,
        player_run_active_game_factory,
        primary_user,
        secondary_user,
        tertiary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(primary_user, reason="was eliminated")

        game.refresh_from_db()
        assert game.managing_member is not None
        assert game.managing_member.user_id in (secondary_user.id, tertiary_user.id)

    @pytest.mark.django_db
    def test_after_elimination_transfer_new_manager_can_manage(
        self,
        player_run_active_game_factory,
        primary_user,
        tertiary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        secondary_member.eliminated = True
        secondary_member.save()

        game.transfer_management_if_needed(primary_user, reason="was eliminated")

        game.refresh_from_db()
        assert game.managing_member == tertiary_member
        assert game.can_manage(tertiary_user) is True


class TestTransferManagementNotApplicable:

    @pytest.mark.django_db
    def test_no_transfer_for_game_master_game(
        self,
        game_master_game_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, secondary_member, tertiary_member = game_master_game_factory()

        game.transfer_management_if_needed(primary_user)

        game.refresh_from_db()
        assert game.managing_member is None
        mock_send_notification_to_users.assert_not_called()

    @pytest.mark.django_db
    def test_no_transfer_for_sandbox_game(
        self,
        sandbox_game_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member = sandbox_game_factory()

        game.transfer_management_if_needed(primary_user)

        game.refresh_from_db()
        assert game.managing_member is None
        mock_send_notification_to_users.assert_not_called()

    @pytest.mark.django_db
    def test_no_transfer_when_exiting_user_is_not_current_manager(
        self,
        player_run_active_game_factory,
        secondary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(secondary_user)

        game.refresh_from_db()
        assert game.managing_member is None
        mock_send_notification_to_users.assert_not_called()

    @pytest.mark.django_db
    def test_no_transfer_when_exiting_user_is_none(
        self,
        player_run_active_game_factory,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(None)

        game.refresh_from_db()
        assert game.managing_member is None
        mock_send_notification_to_users.assert_not_called()


class TestTransferManagementChain:

    @pytest.mark.django_db
    def test_managing_member_exits_transfers_again(
        self,
        player_run_active_game_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()

        game.transfer_management_if_needed(primary_user)

        game.refresh_from_db()
        first_manager = game.managing_member

        first_manager.civil_disorder = True
        first_manager.save()

        game.transfer_management_if_needed(first_manager.user)

        game.refresh_from_db()
        assert game.managing_member is not None
        assert game.managing_member != first_manager


class TestCanManageWithManagingMember:

    @pytest.mark.django_db
    def test_managing_member_can_manage_returns_true(
        self, player_run_active_game_factory, secondary_user
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        game.refresh_from_db()
        assert game.can_manage(secondary_user) is True

    @pytest.mark.django_db
    def test_original_creator_cannot_manage_when_managing_member_set(
        self, player_run_active_game_factory, primary_user, secondary_user
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        game.refresh_from_db()
        assert game.can_manage(primary_user) is False


class TestCanManageApiResponse:

    @pytest.mark.django_db
    def test_can_manage_true_for_managing_member_via_api(
        self, player_run_active_game_factory, secondary_user, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        api_client.force_authenticate(user=secondary_user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_manage"] is True

    @pytest.mark.django_db
    def test_can_manage_false_for_original_creator_after_transfer_via_api(
        self, player_run_active_game_factory, primary_user, secondary_user, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        api_client.force_authenticate(user=primary_user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_manage"] is False

    @pytest.mark.django_db
    def test_managing_member_can_pause_via_api(
        self, player_run_active_game_factory, secondary_user, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        api_client.force_authenticate(user=secondary_user)
        url = reverse(pause_viewname, args=[game.id])
        response = api_client.patch(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_original_creator_cannot_pause_after_transfer_via_api(
        self, player_run_active_game_factory, primary_user, secondary_user, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_active_game_factory()
        game.managing_member = secondary_member
        game.save()

        api_client.force_authenticate(user=primary_user)
        url = reverse(pause_viewname, args=[game.id])
        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestIsGameManagerPermissionWithManagingMember:

    @pytest.mark.django_db
    def test_managing_member_can_kick(
        self, player_run_pending_game_factory, secondary_user, user_factory, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_pending_game_factory()
        game.managing_member = secondary_member
        game.save()

        extra_user = user_factory()
        nations = list(game.variant.nations.filter(non_playable=False))
        extra_member = game.members.create(user=extra_user, nation=nations[3])

        api_client.force_authenticate(user=secondary_user)
        url = reverse(kick_viewname, args=[game.id, extra_member.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_original_creator_cannot_kick_after_transfer(
        self, player_run_pending_game_factory, primary_user, secondary_user, user_factory, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_pending_game_factory()
        game.managing_member = secondary_member
        game.save()

        extra_user = user_factory()
        nations = list(game.variant.nations.filter(non_playable=False))
        extra_member = game.members.create(user=extra_user, nation=nations[3])

        api_client.force_authenticate(user=primary_user)
        url = reverse(kick_viewname, args=[game.id, extra_member.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
