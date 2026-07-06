import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from bot.models import BotProfile
from bot.utils import get_bot_user
from channel.models import Channel, ChannelMember, ChannelMessage
from game.models import Game
from phase.models import Phase
from user_profile.models import UserProfile
from common.constants import GameStatus, NationAssignment, PhaseStatus, PressType

User = get_user_model()

join_viewname = "game-join"
retrieve_viewname = "game-retrieve"
recovery_viewname = "civil-disorder-recovery"


class TestCivilDisorderSerialization:

    @pytest.mark.django_db
    def test_civil_disorder_defaults_to_false_in_serialized_member(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["civil_disorder"] is False

    @pytest.mark.django_db
    def test_civil_disorder_true_is_serialized(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(
            user=primary_user, nation=classical_england_nation, civil_disorder=True
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["civil_disorder"] is True


class TestDeletedUserMemberSerialization:

    @pytest.mark.django_db
    def test_member_with_null_user_serializes_as_deleted_user(
        self, authenticated_client, classical_variant, classical_england_nation
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=None, nation=classical_england_nation, kicked=True)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        deleted_member = response.data["members"][0]
        assert deleted_member["name"] == "Deleted User"
        assert deleted_member["picture"] is None
        assert deleted_member["is_current_user"] is False

    @pytest.mark.django_db
    def test_deleting_user_preserves_member_with_null_user(
        self, classical_variant, classical_england_nation
    ):
        user = User.objects.create_user(
            username="deletable_user", email="deletable@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=user, name="Deletable User", picture="")

        game = Game.objects.create(
            name="Preservation Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        member = game.members.create(user=user, nation=classical_england_nation)
        member_id = member.id

        user.delete()

        from member.models import Member
        preserved_member = Member.objects.get(id=member_id)
        assert preserved_member.user is None
        assert preserved_member.game == game
        assert preserved_member.nation == classical_england_nation


@pytest.mark.django_db
def test_join_game_success(authenticated_client, pending_game_created_by_secondary_user, primary_user):
    """
    Test that an authenticated user can successfully join a game.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == primary_user.profile.name
    assert response.data["is_current_user"] is True


@pytest.mark.django_db
def test_join_game_unauthenticated(unauthenticated_client, pending_game_created_by_secondary_user):
    """
    Test that unauthenticated users cannot join a game.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_join_game_already_member(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that a user cannot join a game they are already a member of.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_join_game_non_pending(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that a user cannot join a game that is not in pending status.
    """
    game = pending_game_created_by_secondary_user
    game.status = GameStatus.ACTIVE
    game.save()

    url = reverse(join_viewname, args=[game.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_join_game_not_found(authenticated_client):
    """
    Test that attempting to join a non-existent game returns 404.
    """
    url = reverse(join_viewname, args=[999])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_join_game_max_players(
    authenticated_client, pending_game_created_by_secondary_user, italy_vs_germany_variant, tertiary_user
):
    """
    Test that a user cannot join a game that already has the maximum number of players.
    This simulates a scenario where the task worker failed to start the game after
    all players joined.
    """
    game = pending_game_created_by_secondary_user
    game.variant = italy_vs_germany_variant
    game.save()

    game.members.create(user=tertiary_user)

    url = reverse(join_viewname, args=[game.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


class TestJoinGameIntroMessage:

    @pytest.mark.django_db
    def test_join_with_intro_message_creates_public_press_message(
        self, authenticated_client, pending_game_created_by_secondary_user, primary_user
    ):
        game = pending_game_created_by_secondary_user
        public_channel = Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, {"intro_message": "Hi all, excited to play!"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        message = ChannelMessage.objects.get(channel=public_channel)
        assert message.body == "Hi all, excited to play!"
        assert message.sender.user == primary_user

    @pytest.mark.django_db
    def test_join_without_intro_message_creates_no_message(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_blank_intro_message_creates_no_message(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, {"intro_message": ""}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_whitespace_only_intro_message_creates_no_message(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, {"intro_message": "   "}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_intro_message_no_press_game_creates_no_message(
        self, authenticated_client, classical_variant
    ):
        game = Game.objects.create(
            name="No Press Pending Game",
            variant=classical_variant,
            status=GameStatus.PENDING,
            press_type=PressType.NO_PRESS,
        )
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, {"intro_message": "Hello"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_intro_message_anonymous_game_creates_no_message(
        self, authenticated_client, classical_variant
    ):
        game = Game.objects.create(
            name="Anonymous Pending Game",
            variant=classical_variant,
            status=GameStatus.PENDING,
            anonymous=True,
        )
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(url, {"intro_message": "Hello"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_intro_message_over_limit_rejected(
        self, authenticated_client, pending_game_created_by_secondary_user, settings
    ):
        game = pending_game_created_by_secondary_user
        Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(
            url, {"intro_message": "x" * (settings.CHAT_MESSAGE_MAX_CHARS + 1)}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ChannelMessage.objects.exists()

    @pytest.mark.django_db
    def test_join_with_intro_message_counts_toward_bot_channel_cap(
        self, authenticated_client, pending_game_created_by_secondary_user, classical_france_nation, settings
    ):
        game = pending_game_created_by_secondary_user
        public_channel = Channel.objects.create(game=game, name="Public Press", private=False)
        bot_member = game.members.create(user=get_bot_user(), nation=classical_france_nation)
        ChannelMember.objects.create(member=bot_member, channel=public_channel)

        url = reverse(join_viewname, args=[game.id])
        authenticated_client.post(url, {"intro_message": "hi"}, format="json")

        msg_url = reverse("channel-message-create", args=[game.id, public_channel.id])
        for _ in range(settings.BOT_CHANNEL_MESSAGE_CAP):
            authenticated_client.post(msg_url, {"body": "hello"}, format="json")

        blocked = authenticated_client.post(msg_url, {"body": "one too many"}, format="json")

        assert blocked.status_code == status.HTTP_400_BAD_REQUEST
        assert ChannelMessage.objects.filter(channel=public_channel).count() == settings.BOT_CHANNEL_MESSAGE_CAP


# Leave/Delete Member Tests
leave_viewname = "game-leave"


@pytest.mark.django_db
def test_leave_game_success(
    authenticated_client, pending_game_created_by_secondary_user_joined_by_primary, primary_user
):
    """
    Test that an authenticated user can successfully leave a game.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user_joined_by_primary.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not pending_game_created_by_secondary_user_joined_by_primary.members.filter(user=primary_user).exists()


@pytest.mark.django_db
def test_leave_game_unauthenticated(unauthenticated_client, pending_game_created_by_secondary_user):
    """
    Test that unauthenticated users cannot leave a game.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user.id])
    response = unauthenticated_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_leave_game_not_a_member(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that a user cannot leave a game they are not a member of.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_leave_game_non_pending(authenticated_client, pending_game_created_by_secondary_user_joined_by_primary):
    """
    Test that a user cannot leave a game that is not in pending status.
    """
    game = pending_game_created_by_secondary_user_joined_by_primary
    game.status = GameStatus.ACTIVE
    game.save()

    url = reverse(leave_viewname, args=[game.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_leave_game_not_found(authenticated_client):
    """
    Test that attempting to leave a non-existent game returns 404.
    """
    url = reverse(leave_viewname, args=[999])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_leave_pending_game_as_sole_member_deletes_game(
    authenticated_client, pending_game_created_by_primary_user
):
    game = pending_game_created_by_primary_user
    game_id = game.id

    url = reverse(leave_viewname, args=[game_id])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Game.objects.filter(id=game_id).exists()


@pytest.mark.django_db
def test_leave_pending_game_with_other_members_preserves_game(
    authenticated_client, pending_game_created_by_secondary_user_joined_by_primary
):
    game = pending_game_created_by_secondary_user_joined_by_primary

    url = reverse(leave_viewname, args=[game.id])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Game.objects.filter(id=game.id).exists()
    assert game.members.count() == 1


@pytest.mark.django_db
def test_join_game_member_is_not_game_creator(
    authenticated_client, pending_game_created_by_secondary_user, primary_user
):
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["is_game_creator"] is False
    assert pending_game_created_by_secondary_user.created_by != primary_user


@pytest.mark.django_db
def test_game_creator_unchanged_after_join(
    authenticated_client, pending_game_created_by_secondary_user, primary_user, secondary_user
):
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED

    game = pending_game_created_by_secondary_user
    game.refresh_from_db()
    assert game.created_by == secondary_user


kick_viewname = "game-kick"


class TestKickMember:

    @pytest.mark.django_db
    def test_kick_member_success(
        self,
        authenticated_client,
        pending_game_created_by_primary_user,
        secondary_user,
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not game.members.filter(user=secondary_user).exists()

    @pytest.mark.django_db
    def test_kick_member_non_game_master_forbidden(
        self,
        authenticated_client,
        pending_game_created_by_secondary_user_joined_by_primary,
        secondary_user,
    ):
        game = pending_game_created_by_secondary_user_joined_by_primary
        gm_member = game.members.get(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, gm_member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_kick_member_active_game_forbidden(
        self,
        authenticated_client,
        active_game_created_by_primary_user,
        secondary_user,
    ):
        game = active_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_kick_self_forbidden(
        self,
        authenticated_client,
        pending_game_created_by_primary_user,
        primary_user,
    ):
        game = pending_game_created_by_primary_user
        gm_member = game.members.get(user=primary_user)

        url = reverse(kick_viewname, args=[game.id, gm_member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_kick_nonexistent_member_404(
        self,
        authenticated_client,
        pending_game_created_by_primary_user,
    ):
        game = pending_game_created_by_primary_user

        url = reverse(kick_viewname, args=[game.id, 99999])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_kick_unauthenticated(
        self,
        unauthenticated_client,
        pending_game_created_by_secondary_user,
        secondary_user,
    ):
        game = pending_game_created_by_secondary_user
        member = game.members.get(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = unauthenticated_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_kicked_player_can_rejoin(
        self,
        authenticated_client,
        pending_game_created_by_secondary_user,
        primary_user,
        secondary_user,
    ):
        game = pending_game_created_by_secondary_user
        member = game.members.create(user=primary_user)

        secondary_client = APIClient()
        secondary_client.force_authenticate(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        secondary_client.delete(url)

        assert not game.members.filter(user=primary_user).exists()

        join_url = reverse(join_viewname, args=[game.id])
        response = authenticated_client.post(join_url)
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_game_start_phase_not_immediately_resolvable(classical_variant, primary_user):
    # After game.start(), the active phase must NOT appear in filter_due_phases()
    # for a duration-based game with a future deadline.
    #
    # Before the fix, game.start() was not wrapped in transaction.atomic(). Between
    # current_phase.save() and PhaseState.objects.bulk_create(), the phase was ACTIVE
    # with no phase states — making all_confirmed vacuously True and the phase appear
    # immediately due to any concurrent sweep task. The transaction.atomic() wrapper
    # ensures the intermediate state (phase active, no phase states) is never committed
    # and therefore never visible to concurrent resolvers.
    from common.constants import MovementPhaseDuration, DeadlineMode

    game = Game.objects.create_from_template(
        classical_variant,
        name="Test Duration Game",
        nation_assignment=NationAssignment.ORDERED,
        deadline_mode=DeadlineMode.DURATION,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    for _ in classical_variant.nations.all():
        game.members.create(user=primary_user)
    game.start()

    phase = game.current_phase
    assert phase.status == "active"
    assert phase.phase_states.exists()
    assert phase not in Phase.objects.filter_due_phases()


class TestMemberUserIdSerialization:

    @pytest.mark.django_db
    def test_user_id_exposed_on_member(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["user_id"] == primary_user.id

    @pytest.mark.django_db
    def test_user_id_masked_in_anonymous_active_game(
        self,
        authenticated_client,
        authenticated_client_for_secondary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        primary_user,
        secondary_user,
    ):
        game = Game.objects.create(
            name="Anon Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            anonymous=True,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=secondary_user, nation=classical_france_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        for member_data in response.data["members"]:
            if member_data["is_current_user"]:
                assert member_data["user_id"] == primary_user.id
            else:
                assert member_data["user_id"] is None

    @pytest.mark.django_db
    def test_user_id_visible_in_completed_anonymous_game(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        primary_user,
        secondary_user,
    ):
        game = Game.objects.create(
            name="Completed Anon",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            anonymous=True,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=secondary_user, nation=classical_france_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        user_ids = [m["user_id"] for m in response.data["members"]]
        assert primary_user.id in user_ids
        assert secondary_user.id in user_ids

    @pytest.mark.django_db
    def test_user_id_null_for_deleted_user(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        primary_user,
    ):
        game = Game.objects.create(
            name="Deleted User Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=None, nation=classical_france_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        for member_data in response.data["members"]:
            if member_data["name"] == "Deleted User":
                assert member_data["user_id"] is None


class TestCivilDisorderRecovery:

    @pytest.mark.django_db
    def test_recover_from_civil_disorder(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        secondary_user,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        game = Game.objects.create(
            name="CD Recovery Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        member = game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            civil_disorder=True,
        )
        game.members.create(user=secondary_user, nation=classical_france_nation)

        phase = game.phases.create(
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        phase.phase_states.create(member=member, orders_confirmed=True)

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["civil_disorder"] is False

        member.refresh_from_db()
        assert member.civil_disorder is False

        phase_state = phase.phase_states.get(member=member)
        assert phase_state.orders_confirmed is False

        mock_send_notification_to_users.assert_called_once()
        call_kwargs = mock_send_notification_to_users.call_args[1]
        assert call_kwargs["notification_type"] == "civil_disorder_recovery"
        assert secondary_user.id in call_kwargs["user_ids"]
        assert primary_user.id not in call_kwargs["user_ids"]
        assert "England" in call_kwargs["body"]

    @pytest.mark.django_db
    def test_recover_fails_if_not_in_civil_disorder(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        classical_england_nation,
    ):
        game = Game.objects.create(
            name="Not CD Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            civil_disorder=False,
        )

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_recover_fails_if_not_game_member(
        self,
        authenticated_client,
        classical_variant,
        secondary_user,
        classical_england_nation,
    ):
        game = Game.objects.create(
            name="No Member Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(
            user=secondary_user,
            nation=classical_england_nation,
            civil_disorder=True,
        )

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_recover_fails_if_game_not_active(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        classical_england_nation,
    ):
        game = Game.objects.create(
            name="Completed Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
        )
        game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            civil_disorder=True,
        )

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_recover_fails_if_unauthenticated(
        self,
        unauthenticated_client,
        classical_variant,
        classical_england_nation,
        primary_user,
    ):
        game = Game.objects.create(
            name="Unauth Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(
            user=primary_user,
            nation=classical_england_nation,
            civil_disorder=True,
        )

        url = reverse(recovery_viewname, args=[game.id])
        response = unauthenticated_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReplaceableSerialization:

    @pytest.mark.django_db
    def test_replaceable_when_civil_disorder(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(user=primary_user, nation=classical_england_nation, civil_disorder=True)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["replaceable"] is True

    @pytest.mark.django_db
    def test_replaceable_when_seeking_replacement(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(
            user=primary_user, nation=classical_england_nation, seeking_replacement=True
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        member = response.data["members"][0]
        assert member["seeking_replacement"] is True
        assert member["replaceable"] is True

    @pytest.mark.django_db
    def test_not_replaceable_by_default(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(user=primary_user, nation=classical_england_nation)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        member = response.data["members"][0]
        assert member["seeking_replacement"] is False
        assert member["replaceable"] is False

    @pytest.mark.django_db
    def test_not_replaceable_when_eliminated(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(
            user=primary_user, nation=classical_england_nation, civil_disorder=True, eliminated=True
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["replaceable"] is False

    @pytest.mark.django_db
    def test_not_replaceable_when_kicked(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(
            user=primary_user, nation=classical_england_nation, seeking_replacement=True, kicked=True
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["replaceable"] is False

    @pytest.mark.django_db
    def test_not_replaceable_when_replaced(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user, secondary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        replacement = game.members.create(user=secondary_user, nation=classical_england_nation)
        game.members.create(
            user=primary_user, nation=classical_england_nation, civil_disorder=True, replaced_by=replacement
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        primary_member = next(m for m in response.data["members"] if m["is_current_user"])
        assert primary_member["replaceable"] is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tier,min_reliability,allowed",
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
def test_join_game_reliability_requirement(
    authenticated_client, pending_game_created_by_secondary_user, tier, min_reliability, allowed
):
    game = pending_game_created_by_secondary_user
    game.min_reliability = min_reliability
    game.save(update_fields=["min_reliability"])
    url = reverse(join_viewname, args=[game.id])

    with patch(
        "common.permissions.get_player_stats",
        return_value={"reliability_tier": tier},
    ):
        response = authenticated_client.post(url)

    if allowed:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.fixture
def roster_bot_user(db):
    return (
        BotProfile.objects.exclude(user__username="diplicitybot")
        .order_by("user__profile__name")
        .first()
        .user
    )


class TestBotMemberSerialization:

    @pytest.mark.django_db
    def test_is_bot_serialized(
        self, authenticated_client, pending_game_created_by_primary_user, roster_bot_user
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=roster_bot_user)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_name = {m["name"]: m for m in response.data["members"]}
        assert members_by_name[roster_bot_user.profile.name]["is_bot"] is True
        assert members_by_name["Primary User"]["is_bot"] is False

    @pytest.mark.django_db
    def test_bot_not_masked_in_anonymous_game(
        self,
        authenticated_client,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        primary_user,
        secondary_user,
        roster_bot_user,
    ):
        game = Game.objects.create(
            name="Anon Bot Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            anonymous=True,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=secondary_user, nation=classical_france_nation)
        game.members.create(user=roster_bot_user, nation=classical_germany_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        bot_member = members_by_nation["Germany"]
        assert bot_member["is_bot"] is True
        assert bot_member["name"] == roster_bot_user.profile.name
        assert bot_member["user_id"] == roster_bot_user.id
        human_member = members_by_nation["France"]
        assert human_member["is_bot"] is False
        assert human_member["name"] == "Anonymous"
        assert human_member["user_id"] is None


class TestKickBotMember:

    @pytest.mark.django_db
    def test_kick_bot_sends_no_notification(
        self, authenticated_client, pending_game_created_by_primary_user, roster_bot_user
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=roster_bot_user)

        with patch("member.views.send_notification") as mock_send:
            url = reverse(kick_viewname, args=[game.id, member.id])
            response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not game.members.filter(user=roster_bot_user).exists()
        mock_send.defer.assert_not_called()

    @pytest.mark.django_db
    def test_kick_human_sends_notification(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        with patch("member.views.send_notification") as mock_send:
            url = reverse(kick_viewname, args=[game.id, member.id])
            response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_send.defer.assert_called_once()


@pytest.mark.django_db
def test_leave_pending_game_with_only_bots_remaining_deletes_game(
    authenticated_client, pending_game_created_by_primary_user, roster_bot_user
):
    game = pending_game_created_by_primary_user
    game.members.create(user=roster_bot_user)
    game_id = game.id

    url = reverse(leave_viewname, args=[game_id])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Game.objects.filter(id=game_id).exists()
