import pytest
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch

from common.constants import GameStatus
from game.models import Game

retrieve_viewname = "game-retrieve"
pause_viewname = "game-pause"
kick_viewname = "game-kick"


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

        Game.objects.transfer_management_if_needed(game, primary_user)

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

        Game.objects.transfer_management_if_needed(game, primary_user)

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="entered civil disorder")

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="entered civil disorder")

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="entered civil disorder")

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="entered civil disorder")

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="was eliminated")

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

        Game.objects.transfer_management_if_needed(game, primary_user, reason="was eliminated")

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

        Game.objects.transfer_management_if_needed(game, primary_user)

        game.refresh_from_db()
        assert game.managing_member is None
        mock_send_notification_to_users.assert_not_called()

    @pytest.mark.django_db
    def test_no_transfer_for_sandbox_game(
        self,
        management_transfer_sandbox_game_factory,
        primary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game, primary_member, secondary_member = management_transfer_sandbox_game_factory()

        Game.objects.transfer_management_if_needed(game, primary_user)

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

        Game.objects.transfer_management_if_needed(game, secondary_user)

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

        Game.objects.transfer_management_if_needed(game, None)

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

        Game.objects.transfer_management_if_needed(game, primary_user)

        game.refresh_from_db()
        first_manager = game.managing_member

        first_manager.civil_disorder = True
        first_manager.save()

        Game.objects.transfer_management_if_needed(game, first_manager.user)

        game.refresh_from_db()
        assert game.managing_member is not None
        assert game.managing_member != first_manager


class TestTransferManagementOnKick:

    @pytest.mark.django_db
    def test_kick_calls_transfer_management_if_needed(
        self, player_run_pending_game_factory, secondary_user, user_factory, api_client
    ):
        game, primary_member, secondary_member, tertiary_member = player_run_pending_game_factory()
        game.managing_member = secondary_member
        game.save()

        extra_user = user_factory()
        nations = list(game.variant.nations.filter(non_playable=False))
        extra_member = game.members.create(user=extra_user, nation=nations[3])

        with patch.object(Game.objects, "transfer_management_if_needed") as mock_transfer:
            api_client.force_authenticate(user=secondary_user)
            url = reverse(kick_viewname, args=[game.id, extra_member.id])
            response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_transfer.assert_called_once_with(game, extra_user, reason="was kicked")


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


class TestGameListQueryCount:

    @pytest.mark.django_db
    def test_game_list_query_count_does_not_grow_with_managing_member(
        self,
        player_run_active_game_factory,
        primary_user,
        secondary_user,
        api_client,
    ):
        game1, primary_member1, secondary_member1, _ = player_run_active_game_factory()
        game1.managing_member = secondary_member1
        game1.save()

        url = reverse("game-list")
        api_client.force_authenticate(user=primary_user)

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            api_client.get(url)
        query_count_one_game = len(connection.queries)

        game2, primary_member2, secondary_member2, _ = player_run_active_game_factory()
        game2.managing_member = secondary_member2
        game2.save()

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            api_client.get(url)
        query_count_two_games = len(connection.queries)

        assert query_count_one_game == query_count_two_games
