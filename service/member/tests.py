import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from agent.constants import AgentTaskKind, AgentTaskStatus
from agent.models import AgentTask
from game.models import Game
from member.models import Member
from member.views import MemberCreateView, MemberJoinView
from notification.models import Notification
from order.models import Order
from phase.models import Phase, PhaseState
from user_profile.models import UserProfile
from common.constants import Commitment, CommitmentRequirement, GameStatus, OrderType, PhaseStatus, UserKind

User = get_user_model()

join_viewname = "game-join"
seat_viewname = "game-member-create"
legacy_join_viewname = "game-join-legacy"
legacy_seat_viewname = "game-add-bot-legacy"
retrieve_viewname = "game-retrieve"
recovery_viewname = "civil-disorder-recovery"


def _kicked_from_staging_notifications():
    return Notification.objects.filter(event_type="kicked_from_staging")


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


@pytest.mark.django_db
def test_join_game_rejects_request_whose_seat_is_taken_by_the_same_user_after_its_checks(
    authenticated_client, pending_game_created_by_secondary_user, italy_vs_germany_variant, primary_user
):
    game = pending_game_created_by_secondary_user
    game.variant = italy_vs_germany_variant
    game.save()

    original_perform_create = MemberJoinView.perform_create

    def perform_create_after_competing_join(view, serializer):
        game.members.create(user=primary_user)
        return original_perform_create(view, serializer)

    url = reverse(join_viewname, args=[game.id])
    with patch.object(MemberJoinView, "perform_create", perform_create_after_competing_join):
        response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert game.members.filter(user=primary_user).count() == 1


@pytest.mark.django_db
def test_join_game_rejects_request_whose_last_seat_is_taken_after_its_checks(
    authenticated_client, pending_game_created_by_secondary_user, italy_vs_germany_variant, tertiary_user
):
    game = pending_game_created_by_secondary_user
    game.variant = italy_vs_germany_variant
    game.save()

    original_perform_create = MemberJoinView.perform_create

    def perform_create_after_competing_join(view, serializer):
        game.members.create(user=tertiary_user)
        return original_perform_create(view, serializer)

    url = reverse(join_viewname, args=[game.id])
    with patch.object(MemberJoinView, "perform_create", perform_create_after_competing_join):
        response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert game.members.count() == 2


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
    def test_kick_member_completed_game_forbidden(
        self,
        authenticated_client,
        active_game_created_by_primary_user,
        secondary_user,
    ):
        game = active_game_created_by_primary_user
        game.status = GameStatus.COMPLETED
        game.save()
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


def _record_nmr(game, member):
    phase = game.phases.create(
        variant=game.variant,
        season="Spring",
        year=1900,
        type="Movement",
        status=PhaseStatus.COMPLETED,
        ordinal=0,
    )
    phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_outcome=PhaseState.OrdersOutcome.NMR,
    )
    return phase


class TestRemoveMemberFromActiveGame:

    @pytest.mark.django_db
    def test_remove_keeps_the_row_and_marks_it_kicked(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        member.refresh_from_db()
        assert member.kicked is True
        assert member.replaced_by is None
        assert member.user is not None

    @pytest.mark.django_db
    def test_remove_discards_orders_and_vacates_the_phase_state(
        self, authenticated_client, active_game_factory, classical_london_province
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)
        phase_state = game.current_phase.phase_states.get(member=member)
        Order.objects.create(
            phase_state=phase_state, source=classical_london_province, order_type=OrderType.HOLD
        )

        url = reverse(kick_viewname, args=[game.id, member.id])
        authenticated_client.delete(url)

        phase_state.refresh_from_db()
        assert phase_state.has_possible_orders is False
        assert not Order.objects.filter(phase_state__member=member).exists()

    @pytest.mark.django_db
    def test_removed_seat_no_longer_holds_up_early_resolution(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)
        phase = game.current_phase
        phase.phase_states.exclude(member=member).update(orders_confirmed=True)

        assert phase.id not in [p.id for p in Phase.objects.filter_due_phases()]

        url = reverse(kick_viewname, args=[game.id, member.id])
        authenticated_client.delete(url)

        assert phase.id in [p.id for p in Phase.objects.filter_due_phases()]

    @pytest.mark.django_db
    def test_remove_notifies_the_removed_player(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        authenticated_client.delete(url)

        notifications = Notification.objects.filter(event_type="removed_from_game")
        assert [n.recipient_id for n in notifications] == [member.user_id]

    @pytest.mark.django_db
    def test_remove_does_not_notify_a_bot(
        self, authenticated_client, active_game_factory, bot_user
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        member.user = bot_user
        member.save()
        _record_nmr(game, member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        authenticated_client.delete(url)

        assert not Notification.objects.filter(event_type="removed_from_game").exists()

    @pytest.mark.django_db
    def test_removed_player_cannot_submit_orders(self, active_game_factory, classical_london_province):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        Member.objects.remove(member)

        client = APIClient()
        client.force_authenticate(user=member.user)
        response = client.post(
            reverse("order-create", args=[game.id]),
            {"selected": [classical_london_province.province_id]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_removed_player_can_still_read_the_game(self, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        Member.objects.remove(member)

        client = APIClient()
        client.force_authenticate(user=member.user)
        response = client.get(reverse(retrieve_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_200_OK


class TestRemovalRequiresMissedOrders:

    @pytest.mark.django_db
    def test_member_who_missed_the_last_resolved_phase_can_be_removed(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_member_in_civil_disorder_can_be_removed(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        member.civil_disorder = True
        member.save()

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_member_with_a_clean_record_cannot_be_removed(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "This player has not missed any orders."
        member.refresh_from_db()
        assert member.kicked is False

    @pytest.mark.django_db
    def test_member_who_submitted_orders_last_phase_cannot_be_removed(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        phase = _record_nmr(game, member)
        phase.phase_states.filter(member=member).update(
            orders_outcome=PhaseState.OrdersOutcome.RECEIVED
        )

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_bot_with_a_clean_record_can_be_removed(
        self, authenticated_client, active_game_factory, bot_user
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        member.user = bot_user
        member.save()

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_already_removed_member_cannot_be_removed_again(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)
        Member.objects.remove(member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRemovableSerialization:

    @pytest.mark.django_db
    def test_removable_is_false_for_a_clean_member(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        members_by_id = {m["id"]: m for m in response.data["members"]}
        assert members_by_id[member.id]["removable"] is False

    @pytest.mark.django_db
    def test_removable_is_true_after_a_missed_phase(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        members_by_id = {m["id"]: m for m in response.data["members"]}
        assert members_by_id[member.id]["removable"] is True

    @pytest.mark.django_db
    def test_removable_is_false_once_removed(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)
        Member.objects.remove(member)

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        members_by_id = {m["id"]: m for m in response.data["members"]}
        assert members_by_id[member.id]["removable"] is False

    @pytest.mark.django_db
    def test_removable_is_true_in_a_pending_game(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        members_by_id = {m["id"]: m for m in response.data["members"]}
        assert members_by_id[member.id]["removable"] is True


replace_viewname = "game-member-replace"


class TestMemberReplace:

    def _open_seat(self, game):
        member = game.members.exclude(user=game.admin).first()
        Member.objects.remove(member)
        return member

    @pytest.mark.django_db
    def test_takes_over_the_seat(self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user):
        game = active_game_factory()
        member = self._open_seat(game)

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["nation"] == member.nation.name
        replacement = game.members.get(user=tertiary_user)
        assert replacement.nation == member.nation
        assert replacement.kicked is False
        member.refresh_from_db()
        assert member.replaced_by == replacement

    @pytest.mark.django_db
    def test_replaced_member_is_swapped_out_of_the_members_list(
        self, authenticated_client, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user
    ):
        game = active_game_factory()
        member = self._open_seat(game)

        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))
        member_ids = [m["id"] for m in response.data["members"]]
        assert member.id not in member_ids
        assert game.members.get(user=tertiary_user).id in member_ids

    @pytest.mark.django_db
    def test_replacement_joins_every_channel_the_original_was_in(
        self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user
    ):
        game = active_game_factory()
        member = self._open_seat(game)
        private = game.channels.create(name="Private", private=True)
        private.member_channels.create(member=member)

        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        replacement = game.members.get(user=tertiary_user)
        assert private.id in replacement.member_channels.values_list("channel_id", flat=True)

    @pytest.mark.django_db
    def test_replacement_gets_a_phase_state_for_the_current_phase(
        self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user
    ):
        game = active_game_factory()
        member = self._open_seat(game)

        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        phase = game.current_phase
        replacement = game.members.get(user=tertiary_user)
        assert phase.phase_states.get(member=replacement).has_possible_orders is True
        assert phase.phase_states.get(member=member).has_possible_orders is False

    @pytest.mark.django_db
    def test_civil_disorder_seat_can_be_taken_over(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        member.civil_disorder = True
        member.save()

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_open_seat_notifies_the_other_players(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = self._open_seat(game)

        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        notifications = Notification.objects.filter(event_type="seat_filled")
        assert notifications.exists()
        assert member.nation.name in notifications.first().deliveries.first().body

    @pytest.mark.django_db
    def test_seat_that_is_not_open_forbidden(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_eliminated_seat_forbidden(self, authenticated_client_for_tertiary_user, active_game_factory):
        game = active_game_factory()
        member = self._open_seat(game)
        member.eliminated = True
        member.save()

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_second_takeover_of_the_same_seat_forbidden(
        self, authenticated_client_for_tertiary_user, active_game_factory, user_factory
    ):
        game = active_game_factory()
        member = self._open_seat(game)
        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        other_client = APIClient()
        other_client.force_authenticate(user=user_factory())
        response = other_client.post(reverse(replace_viewname, args=[game.id, member.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_existing_member_forbidden(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._open_seat(game)

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_game_master_forbidden(self, active_game_factory, tertiary_user):
        game = active_game_factory()
        member = self._open_seat(game)
        game.game_master = tertiary_user
        game.save()

        client = APIClient()
        client.force_authenticate(user=tertiary_user)
        response = client.post(reverse(replace_viewname, args=[game.id, member.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_pending_game_forbidden(
        self, authenticated_client_for_tertiary_user, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user, kicked=True)

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._open_seat(game)

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
    def test_replaceable_when_kicked(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(user=primary_user, nation=classical_england_nation, kicked=True)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        member = response.data["members"][0]
        assert member["kicked"] is True
        assert member["replaceable"] is True

    @pytest.mark.django_db
    def test_not_replaceable_when_kicked_and_eliminated(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(
            user=primary_user, nation=classical_england_nation, kicked=True, eliminated=True
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["replaceable"] is False

    @pytest.mark.django_db
    def test_replaced_member_is_not_listed(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user, secondary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        replacement = game.members.create(user=secondary_user, nation=classical_england_nation)
        replaced = game.members.create(
            user=primary_user, nation=classical_england_nation, civil_disorder=True, replaced_by=replacement
        )
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert [m["id"] for m in response.data["members"]] == [replacement.id]
        assert not any(m["is_current_user"] for m in response.data["members"])
        assert replaced.replaceable is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "commitment,commitment_requirement,private,allowed",
    [
        (Commitment.HIGH, CommitmentRequirement.OPEN, False, True),
        (Commitment.HIGH, CommitmentRequirement.COMMITTED, False, True),
        (Commitment.MEDIUM, CommitmentRequirement.OPEN, False, True),
        (Commitment.MEDIUM, CommitmentRequirement.COMMITTED, False, False),
        (Commitment.UNDEFINED, CommitmentRequirement.OPEN, False, True),
        (Commitment.UNDEFINED, CommitmentRequirement.COMMITTED, False, False),
        (Commitment.LOW, CommitmentRequirement.OPEN, False, False),
        (Commitment.LOW, CommitmentRequirement.COMMITTED, False, False),
        (Commitment.LOW, CommitmentRequirement.OPEN, True, True),
        (Commitment.LOW, CommitmentRequirement.COMMITTED, True, False),
    ],
)
def test_join_game_commitment_requirement(
    authenticated_client,
    primary_user,
    pending_game_created_by_secondary_user,
    set_commitment,
    commitment,
    commitment_requirement,
    private,
    allowed,
):
    game = pending_game_created_by_secondary_user
    game.commitment_requirement = commitment_requirement
    game.private = private
    game.save(update_fields=["commitment_requirement", "private"])
    set_commitment(primary_user, commitment)
    url = reverse(join_viewname, args=[game.id])

    response = authenticated_client.post(url)

    if allowed:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBotMemberSerialization:

    @pytest.mark.django_db
    def test_is_bot_serialized(
        self, authenticated_client, pending_game_created_by_primary_user, bot_user
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=bot_user)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        members_by_name = {m["name"]: m for m in response.data["members"]}
        assert members_by_name[bot_user.profile.name]["is_bot"] is True
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
        bot_user,
    ):
        game = Game.objects.create(
            name="Anon Bot Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            anonymous=True,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)
        game.members.create(user=secondary_user, nation=classical_france_nation)
        game.members.create(user=bot_user, nation=classical_germany_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        members_by_nation = {m["nation"]: m for m in response.data["members"]}
        bot_member = members_by_nation["Germany"]
        assert bot_member["is_bot"] is True
        assert bot_member["name"] == bot_user.profile.name
        assert bot_member["user_id"] == bot_user.id
        human_member = members_by_nation["France"]
        assert human_member["is_bot"] is False
        assert human_member["name"] == "Anonymous"
        assert human_member["user_id"] is None


class TestKickBotMember:

    @pytest.mark.django_db
    def test_kick_bot_sends_no_notification(
        self, authenticated_client, pending_game_created_by_primary_user, bot_user, in_memory_procrastinate
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=bot_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not game.members.filter(user=bot_user).exists()
        assert not _kicked_from_staging_notifications().exists()

    @pytest.mark.django_db
    def test_kick_human_sends_notification(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user, in_memory_procrastinate
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert _kicked_from_staging_notifications().exists()


@pytest.mark.django_db
def test_leave_pending_game_with_only_bots_remaining_deletes_game(
    authenticated_client, pending_game_created_by_primary_user, bot_user
):
    game = pending_game_created_by_primary_user
    game.members.create(user=bot_user)
    game_id = game.id

    url = reverse(leave_viewname, args=[game_id])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Game.objects.filter(id=game_id).exists()


class TestKickedMemberCivilDisorderRecovery:

    @pytest.mark.django_db
    def test_recovery_as_kicked_member_forbidden(
        self, authenticated_client_for_secondary_user, active_game_with_kicked_member
    ):
        game = active_game_with_kicked_member
        member = game.members.get(kicked=True)
        member.civil_disorder = True
        member.save(update_fields=["civil_disorder"])

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        member.refresh_from_db()
        assert member.civil_disorder is True


class TestReplanOrdersAdminAction:

    def _post_action(self, client, member):
        return client.post(
            "/admin/member/member/",
            {"action": "replan_orders", "_selected_action": [str(member.id)]},
            follow=True,
        )

    def _staff_client(self, authenticated_client, primary_user):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)
        return authenticated_client

    @pytest.mark.django_db
    def test_queues_a_plan_task_for_a_bot_member(
        self, authenticated_client, active_game_factory, primary_user, in_memory_procrastinate
    ):
        game = active_game_factory()
        member = game.members.exclude(user=primary_user).first()
        UserProfile.objects.filter(user=member.user).update(kind=UserKind.LLM)
        client = self._staff_client(authenticated_client, primary_user)

        response = self._post_action(client, member)

        assert response.status_code == status.HTTP_200_OK
        task = AgentTask.objects.get(kind=AgentTaskKind.PLAN, member=member)
        assert task.phase == game.current_phase
        assert task.status == AgentTaskStatus.PENDING

    @pytest.mark.django_db
    def test_reports_an_error_for_a_member_not_played_by_a_bot(
        self, authenticated_client, active_game_factory, primary_user, in_memory_procrastinate
    ):
        game = active_game_factory()
        member = game.members.exclude(user=primary_user).first()
        client = self._staff_client(authenticated_client, primary_user)

        response = self._post_action(client, member)

        assert response.status_code == status.HTTP_200_OK
        assert "not played by a bot" in response.content.decode()
        assert not AgentTask.objects.filter(member=member).exists()


@pytest.fixture
def allowlisted_client(authenticated_client, primary_user, settings):
    settings.BOT_OPPONENT_ALLOWLIST = [primary_user.email.lower()]
    return authenticated_client


def _create_game_via_api(client, variant_id, **overrides):
    payload = {
        "name": "Bot Seat Game",
        "variant_id": variant_id,
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    response = client.post(reverse("game-create"), payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


class TestSeatMember:

    @pytest.mark.django_db
    def test_manager_can_seat_a_bot(self, allowlisted_client, classical_variant, bot_user):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_bot"] is True
        assert response.data["name"] == bot_user.profile.name
        member = game.members.get(user=bot_user)
        assert game.get_public_press().member_channels.filter(member=member).exists()
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING

    @pytest.mark.django_db
    def test_seating_the_last_seat_starts_the_game(
        self, allowlisted_client, italy_vs_germany_variant, bot_user
    ):
        game = _create_game_via_api(allowlisted_client, italy_vs_germany_variant.id)

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.current_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_game_master_can_seat_a_bot(self, allowlisted_client, classical_variant, bot_user):
        game = _create_game_via_api(
            allowlisted_client, classical_variant.id, private=True, game_master=True
        )

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert game.members.filter(user=bot_user).exists()

    @pytest.mark.django_db
    def test_bot_already_in_the_game_is_rejected(self, allowlisted_client, classical_variant, bot_user):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)
        game.members.create(user=bot_user)

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_human_user_is_rejected(self, allowlisted_client, classical_variant, secondary_user):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": secondary_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_manager_cannot_seat_a_bot(
        self, allowlisted_client, authenticated_client_for_secondary_user, classical_variant, bot_user, settings
    ):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com", "secondary@example.com"]

        response = authenticated_client_for_secondary_user.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_user_off_the_allowlist_cannot_seat_a_bot(
        self, allowlisted_client, classical_variant, bot_user, settings
    ):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = allowlisted_client.post(
            reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_cannot_seat_a_bot_in_a_non_pending_game(
        self, allowlisted_client, active_game_created_by_primary_user, bot_user
    ):
        response = allowlisted_client.post(
            reverse(seat_viewname, args=[active_game_created_by_primary_user.id]),
            {"user_id": bot_user.id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_rejects_request_whose_bot_is_seated_after_its_checks(
        self, allowlisted_client, classical_variant, bot_user
    ):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)
        original_perform_create = MemberCreateView.perform_create

        def perform_create_after_competing_seat(view, serializer):
            game.members.create(user=bot_user)
            return original_perform_create(view, serializer)

        with patch.object(MemberCreateView, "perform_create", perform_create_after_competing_seat):
            response = allowlisted_client.post(
                reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert game.members.filter(user=bot_user).count() == 1

    @pytest.mark.django_db
    def test_rejects_request_whose_last_seat_is_taken_after_its_checks(
        self, allowlisted_client, italy_vs_germany_variant, secondary_user, bot_user
    ):
        game = _create_game_via_api(allowlisted_client, italy_vs_germany_variant.id)
        original_perform_create = MemberCreateView.perform_create

        def perform_create_after_competing_join(view, serializer):
            game.members.create(user=secondary_user)
            return original_perform_create(view, serializer)

        with patch.object(MemberCreateView, "perform_create", perform_create_after_competing_join):
            response = allowlisted_client.post(
                reverse(seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert game.members.count() == 2


class TestLegacyMemberJoinView:

    def test_serves_the_path_shipped_mobile_builds_call(self):
        assert reverse(legacy_join_viewname, args=["abc123"]) == "/game/abc123/join/"

    @pytest.mark.django_db
    def test_join_game_success(
        self, authenticated_client, pending_game_created_by_secondary_user, primary_user
    ):
        url = reverse(legacy_join_viewname, args=[pending_game_created_by_secondary_user.id])
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == primary_user.profile.name
        assert response.data["is_current_user"] is True
        assert pending_game_created_by_secondary_user.members.filter(user=primary_user).exists()

    @pytest.mark.django_db
    def test_join_game_unauthenticated(self, unauthenticated_client, pending_game_created_by_secondary_user):
        url = reverse(legacy_join_viewname, args=[pending_game_created_by_secondary_user.id])
        response = unauthenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_join_game_already_member(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(legacy_join_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_join_game_non_pending(self, authenticated_client, pending_game_created_by_secondary_user):
        game = pending_game_created_by_secondary_user
        game.status = GameStatus.ACTIVE
        game.save()

        url = reverse(legacy_join_viewname, args=[game.id])
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_join_game_not_found(self, authenticated_client):
        url = reverse(legacy_join_viewname, args=[999])
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_joining_the_last_seat_starts_the_game(
        self, authenticated_client, pending_game_created_by_secondary_user, italy_vs_germany_variant
    ):
        game = pending_game_created_by_secondary_user
        game.variant = italy_vs_germany_variant
        game.save()

        url = reverse(legacy_join_viewname, args=[game.id])
        response = authenticated_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE


class TestLegacyMemberCreateView:

    def test_serves_the_path_shipped_mobile_builds_call(self):
        assert reverse(legacy_seat_viewname, args=["abc123"]) == "/game/abc123/add-bot/"

    @pytest.mark.django_db
    def test_manager_can_seat_a_bot(self, allowlisted_client, classical_variant, bot_user):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)

        response = allowlisted_client.post(
            reverse(legacy_seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_bot"] is True
        member = game.members.get(user=bot_user)
        assert game.get_public_press().member_channels.filter(member=member).exists()

    @pytest.mark.django_db
    def test_human_user_is_rejected(self, allowlisted_client, classical_variant, secondary_user):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)

        response = allowlisted_client.post(
            reverse(legacy_seat_viewname, args=[game.id]), {"user_id": secondary_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_user_off_the_allowlist_cannot_seat_a_bot(
        self, allowlisted_client, classical_variant, bot_user, settings
    ):
        game = _create_game_via_api(allowlisted_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = allowlisted_client.post(
            reverse(legacy_seat_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


preference_viewname = "game-member-nation-preference"
assign_viewname = "game-member-nation-assign"


class TestMemberNationPreferenceView:

    @pytest.mark.django_db
    def test_get_defaults_to_empty_list(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nation_ids"] == []

    @pytest.mark.django_db
    def test_put_and_get_roundtrip(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.put(url, {"nation_ids": ["france", "england"]}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nation_ids"] == ["france", "england"]
        response = authenticated_client.get(url)
        assert response.data["nation_ids"] == ["france", "england"]

    @pytest.mark.django_db
    def test_put_replaces_existing_ranking(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        authenticated_client.put(url, {"nation_ids": ["france", "england"]}, format="json")
        response = authenticated_client.put(url, {"nation_ids": ["england", "france", "turkey"]}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nation_ids"] == ["england", "france", "turkey"]

    @pytest.mark.django_db
    def test_put_empty_list_clears_preferences(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        authenticated_client.put(url, {"nation_ids": ["france"]}, format="json")
        response = authenticated_client.put(url, {"nation_ids": []}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nation_ids"] == []

    @pytest.mark.django_db
    def test_duplicate_nations_rejected(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.put(url, {"nation_ids": ["france", "france"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_nation_from_another_variant_rejected(
        self, authenticated_client, pending_game_created_by_primary_user, italy_vs_germany_variant
    ):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client.put(url, {"nation_ids": ["nonexistent-nation"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_playable_nation_rejected(self, authenticated_client, pending_game_created_by_primary_user):
        game = pending_game_created_by_primary_user
        game.variant.nations.create(nation_id="neutral", name="Neutral", color="#000000", non_playable=True)
        url = reverse(preference_viewname, args=[game.id])
        response = authenticated_client.put(url, {"nation_ids": ["neutral"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_member_forbidden(
        self, authenticated_client_for_secondary_user, pending_game_created_by_primary_user
    ):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = authenticated_client_for_secondary_user.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_game_master_forbidden(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        url = reverse(preference_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_active_game_forbidden(self, authenticated_client, active_game_with_phase_state):
        url = reverse(preference_viewname, args=[active_game_with_phase_state.id])
        response = authenticated_client.put(url, {"nation_ids": ["france"]}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, pending_game_created_by_primary_user):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMemberNationAssignView:

    def _game_with_member(self, factory, secondary_user):
        game = factory()
        member = game.members.create(user=secondary_user)
        return game, member

    @pytest.mark.django_db
    def test_game_master_can_pin_nation(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        response = authenticated_client.put(url, {"nation_id": "france"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.nation.nation_id == "france"

    @pytest.mark.django_db
    def test_game_master_can_repin_same_member(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        authenticated_client.put(url, {"nation_id": "france"}, format="json")
        response = authenticated_client.put(url, {"nation_id": "england"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.nation.nation_id == "england"

    @pytest.mark.django_db
    def test_game_master_can_unpin_nation(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        authenticated_client.put(url, {"nation_id": "france"}, format="json")
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        member.refresh_from_db()
        assert member.nation is None

    @pytest.mark.django_db
    def test_pinning_nation_held_by_another_member_rejected(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user, tertiary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        other = game.members.create(user=tertiary_user)
        authenticated_client.put(reverse(assign_viewname, args=[game.id, member.id]), {"nation_id": "france"}, format="json")
        response = authenticated_client.put(
            reverse(assign_viewname, args=[game.id, other.id]), {"nation_id": "france"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        other.refresh_from_db()
        assert other.nation is None

    @pytest.mark.django_db
    def test_constraint_holds_when_validation_bypassed(
        self, db, pending_game_with_game_master_factory, secondary_user, tertiary_user, classical_france_nation
    ):
        from django.db import IntegrityError

        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        Member.objects.assign_nation(member, classical_france_nation)
        with pytest.raises(IntegrityError):
            game.members.create(user=tertiary_user, nation=classical_france_nation)

    @pytest.mark.django_db
    def test_invalid_nation_rejected(
        self, authenticated_client, pending_game_with_game_master_factory, secondary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        response = authenticated_client.put(url, {"nation_id": "not-a-nation"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_game_master_member_forbidden(
        self, authenticated_client_for_secondary_user, pending_game_with_game_master_factory, secondary_user
    ):
        game, member = self._game_with_member(pending_game_with_game_master_factory, secondary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        response = authenticated_client_for_secondary_user.put(url, {"nation_id": "france"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_no_game_master_forbidden(self, authenticated_client, pending_game_created_by_primary_user, primary_user):
        game = pending_game_created_by_primary_user
        member = game.members.get(user=primary_user)
        url = reverse(assign_viewname, args=[game.id, member.id])
        response = authenticated_client.put(url, {"nation_id": "france"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_active_game_forbidden(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        member = game.members.first()
        url = reverse(assign_viewname, args=[game.id, member.id])
        response = authenticated_client.put(url, {"nation_id": "france"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_unknown_member_returns_404(
        self, authenticated_client, pending_game_with_game_master_factory
    ):
        game = pending_game_with_game_master_factory()
        url = reverse(assign_viewname, args=[game.id, 999999])
        response = authenticated_client.put(url, {"nation_id": "france"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
