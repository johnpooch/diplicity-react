import pytest
from unittest.mock import patch
from django.db import connection
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from agent.constants import AgentTaskKind, AgentTaskStatus
from agent.models import AgentTask
from draw_proposal.models import DrawProposal
from game.models import Game
from member.models import Member
from member.views import MemberCreateView, MemberJoinView
from notification.models import Notification
from order.models import Order
from phase.models import Phase, PhaseState
from user_profile.models import UserProfile
from victory.models import Victory
from common.constants import Commitment, CommitmentRequirement, GameStatus, MemberKind, OrderType, PhaseStatus, UserKind

User = get_user_model()

join_viewname = "game-join"
seat_viewname = "game-member-create"
legacy_join_viewname = "game-join-legacy"
legacy_seat_viewname = "game-add-bot-legacy"
retrieve_viewname = "game-retrieve"
list_viewname = "game-list"
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
            user=primary_user, nation=classical_england_nation, civil_disorder_at=timezone.now()
        )

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["civil_disorder"] is True


class TestUploadedPictureSerialization:

    @pytest.mark.django_db
    def test_uploaded_picture_is_served_to_other_members(
        self,
        authenticated_client_for_secondary_user,
        classical_variant,
        classical_england_nation,
        primary_user,
        stored_picture,
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        game.members.create(user=primary_user, nation=classical_england_nation)

        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["picture"].endswith(
            reverse(
                "user-picture-image",
                kwargs={
                    "user_id": primary_user.id,
                    "content_hash": stored_picture.content_hash,
                },
            )
        )


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
        game.members.create(user=None, nation=classical_england_nation, removed_at=timezone.now())

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
def test_joining_the_last_seat_starts_a_game_with_a_long_id(
    authenticated_client, secondary_user, classical_variant, italy_vs_germany_variant, base_pending_phase
):
    game = Game.objects.create(
        name="The Contest of the Contumacious Comb MIRROR REALITY",
        variant=classical_variant,
        status=GameStatus.PENDING,
        created_by=secondary_user,
        admin=secondary_user,
    )
    base_pending_phase(game)
    game.variant = italy_vs_germany_variant
    game.save()
    game.channels.create(name="Public Press", private=False)
    game.seat(secondary_user)

    url = reverse(join_viewname, args=[game.id])
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_201_CREATED
    game.refresh_from_db()
    assert game.status == GameStatus.ACTIVE
    assert Notification.objects.filter(event_type="game_start", recipient=secondary_user).exists()


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
def test_leave_pending_game_deletes_private_channel_left_with_one_member(
    authenticated_client,
    authenticated_client_factory,
    pending_game_created_by_secondary_user_joined_by_primary,
    secondary_user,
):
    game = pending_game_created_by_secondary_user_joined_by_primary
    authenticated_client.post(
        reverse("channel-create", args=[game.id]),
        {"member_ids": [game.members.get(user=secondary_user).id]},
        format="json",
    )

    response = authenticated_client.delete(reverse(leave_viewname, args=[game.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    channels = authenticated_client_factory(secondary_user).get(reverse("channel-preview-list", args=[game.id])).data
    assert [channel["private"] for channel in channels] == [False]


@pytest.mark.django_db
def test_leave_pending_game_names_private_channel_after_remaining_members(
    authenticated_client,
    authenticated_client_factory,
    user_factory,
    pending_game_created_by_secondary_user_joined_by_primary,
    secondary_user,
):
    game = pending_game_created_by_secondary_user_joined_by_primary
    third_user = user_factory()
    authenticated_client_factory(third_user).post(reverse(join_viewname, args=[game.id]), {}, format="json")
    authenticated_client.post(
        reverse("channel-create", args=[game.id]),
        {"member_ids": [game.members.get(user=secondary_user).id, game.members.get(user=third_user).id]},
        format="json",
    )

    authenticated_client.delete(reverse(leave_viewname, args=[game.id]))

    channels = authenticated_client_factory(secondary_user).get(reverse("channel-preview-list", args=[game.id])).data
    private_names = [channel["name"] for channel in channels if channel["private"]]
    assert private_names == [", ".join(sorted([secondary_user.profile.name, third_user.profile.name]))]


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
    def test_kick_member_from_pending_game_deletes_private_channel_left_with_one_member(
        self,
        authenticated_client,
        authenticated_client_factory,
        pending_game_created_by_primary_user,
        secondary_user,
    ):
        game = pending_game_created_by_primary_user
        secondary_client = authenticated_client_factory(secondary_user)
        secondary_client.post(reverse(join_viewname, args=[game.id]), {}, format="json")
        member = game.members.get(user=secondary_user)
        authenticated_client.post(reverse("channel-create", args=[game.id]), {"member_ids": [member.id]}, format="json")

        response = authenticated_client.delete(reverse(kick_viewname, args=[game.id, member.id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        channels = authenticated_client.get(reverse("channel-preview-list", args=[game.id])).data
        assert [channel["private"] for channel in channels] == [False]

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
    def test_remove_keeps_the_row_and_records_the_removal(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        _record_nmr(game, member)

        url = reverse(kick_viewname, args=[game.id, member.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        member.refresh_from_db()
        assert member.removed_at is not None
        assert member.replaced_by is None
        assert member.user is not None

    @pytest.mark.django_db
    def test_remove_discards_orders_and_confirms_the_phase_state(
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
        assert phase_state.orders_confirmed is True
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
    def test_game_with_every_player_removed_is_abandoned_at_resolution(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        for member in game.members.exclude(user=game.admin):
            _record_nmr(game, member)
            authenticated_client.delete(reverse(kick_viewname, args=[game.id, member.id]))
        Member.objects.remove(game.members.get(user=game.admin))

        Phase.objects.resolve(game.current_phase)

        game.refresh_from_db()
        assert game.status == GameStatus.ABANDONED

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
        member.civil_disorder_at = timezone.now()
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
        assert member.left_seat is False

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
        assert replacement.left_seat is False
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
        member.civil_disorder_at = timezone.now()
        member.save()

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        member.refresh_from_db()
        assert member.replaced_by is not None
        assert member.removed_at is None

    @pytest.mark.django_db
    def test_withdrawn_seat_can_be_taken_over_without_recording_a_removal(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        member.refresh_from_db()
        assert member.replaced_by is not None
        assert member.removed_at is None

    @pytest.mark.django_db
    def test_removed_seat_keeps_its_removal_time_when_taken_over(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = self._open_seat(game)
        member.refresh_from_db()
        removed_at = member.removed_at

        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        member.refresh_from_db()
        assert member.replaced_by is not None
        assert member.removed_at == removed_at

    @pytest.mark.django_db
    def test_replaced_member_is_reported_as_kicked(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = game.members.exclude(user=game.admin).first()
        member.civil_disorder_at = timezone.now()
        member.save()
        authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        response = _client_for(member.user).get(reverse("phase-state-list", args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["member"]["kicked"] is True
        assert response.data[0]["member"]["civil_disorder"] is True

    @pytest.mark.django_db
    def test_civil_disorder_player_cannot_reclaim_their_own_seat(
        self, authenticated_client, active_game_factory, primary_user
    ):
        game = active_game_factory()
        member = game.members.get(user=primary_user)
        member.civil_disorder_at = timezone.now()
        member.save()

        url = reverse(replace_viewname, args=[game.id, member.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        member.refresh_from_db()
        assert member.replaced_by is None

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
        member.eliminated_at = timezone.now()
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
        member = game.members.create(user=secondary_user, removed_at=timezone.now())

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
def test_game_start_phase_not_immediately_resolvable(classical_variant, user_factory):
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
        game.members.create(user=user_factory())
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


class TestCivilDisorderRecoveryView:

    def test_serves_the_path_shipped_mobile_builds_call(self):
        assert reverse(recovery_viewname, args=["abc123"]) == "/game/abc123/recover-from-civil-disorder/"

    @pytest.mark.django_db
    def test_civil_disorder_is_permanent(self, authenticated_client, active_game_factory, primary_user):
        game = active_game_factory()
        member = game.members.get(user=primary_user)
        member.civil_disorder_at = timezone.now()
        member.save()

        url = reverse(recovery_viewname, args=[game.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_410_GONE
        member.refresh_from_db()
        assert member.civil_disorder is True

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, active_game_factory):
        game = active_game_factory()

        url = reverse(recovery_viewname, args=[game.id])
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReplaceableSerialization:

    @pytest.mark.django_db
    def test_replaceable_when_civil_disorder(
        self, authenticated_client, classical_variant, classical_england_nation, primary_user
    ):
        game = Game.objects.create(name="T", variant=classical_variant, status=GameStatus.ACTIVE)
        game.members.create(user=primary_user, nation=classical_england_nation, civil_disorder_at=timezone.now())
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
            user=primary_user, nation=classical_england_nation, civil_disorder_at=timezone.now(), eliminated_at=timezone.now()
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
        game.members.create(user=primary_user, nation=classical_england_nation, removed_at=timezone.now())
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
            user=primary_user, nation=classical_england_nation, removed_at=timezone.now(), eliminated_at=timezone.now()
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
            user=primary_user, nation=classical_england_nation, civil_disorder_at=timezone.now(), replaced_by=replacement
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


class TestMemberNationPreferenceIdsField:

    @pytest.mark.django_db
    def test_defaults_to_empty_list(self, authenticated_client, pending_game_created_by_primary_user):
        response = authenticated_client.get(
            reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["members"][0]["nation_preference_ids"] == []

    @pytest.mark.django_db
    def test_own_preferences_are_listed_in_rank_order(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        url = reverse(preference_viewname, args=[pending_game_created_by_primary_user.id])
        authenticated_client.put(url, {"nation_ids": ["turkey", "france", "england"]}, format="json")

        response = authenticated_client.get(
            reverse(retrieve_viewname, args=[pending_game_created_by_primary_user.id])
        )

        assert response.data["members"][0]["nation_preference_ids"] == ["turkey", "france", "england"]

    @pytest.mark.django_db
    def test_another_members_preferences_are_not_exposed(
        self,
        authenticated_client,
        authenticated_client_for_secondary_user,
        pending_game_created_by_primary_user,
        secondary_user,
    ):
        game = pending_game_created_by_primary_user
        game.seat(secondary_user)
        authenticated_client_for_secondary_user.put(
            reverse(preference_viewname, args=[game.id]), {"nation_ids": ["france"]}, format="json"
        )

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        preferences = {
            member["name"]: member["nation_preference_ids"] for member in response.data["members"]
        }
        assert preferences[secondary_user.profile.name] == []

    @pytest.mark.django_db
    def test_exposed_in_the_games_list(self, authenticated_client, pending_game_created_by_primary_user):
        authenticated_client.put(
            reverse(preference_viewname, args=[pending_game_created_by_primary_user.id]),
            {"nation_ids": ["russia"]},
            format="json",
        )

        response = authenticated_client.get(reverse("game-list"), {"mine": "true"})

        game = next(
            g for g in response.data["results"] if g["id"] == pending_game_created_by_primary_user.id
        )
        assert game["members"][0]["nation_preference_ids"] == ["russia"]

    @pytest.mark.django_db
    def test_listing_does_not_query_per_member(
        self,
        authenticated_client,
        pending_game_created_by_primary_user,
        user_factory,
        classical_france_nation,
        classical_england_nation,
    ):
        game = pending_game_created_by_primary_user

        def rank(member):
            Member.objects.set_nation_preferences(
                member, [classical_france_nation, classical_england_nation]
            )

        def list_query_count():
            connection.queries_log.clear()
            with override_settings(DEBUG=True):
                response = authenticated_client.get(reverse(list_viewname))
            assert response.status_code == status.HTTP_200_OK
            return len(connection.queries)

        for member in game.members.all():
            rank(member)
        few_members_count = list_query_count()

        for index in range(5):
            rank(game.members.create(user=user_factory(f"ranker{index}")))
        many_members_count = list_query_count()

        assert many_members_count == few_members_count


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


withdraw_viewname = "game-member-withdraw"


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _withdraw(game, member):
    return _client_for(member.user).patch(reverse(withdraw_viewname, args=[game.id]))


def _non_admin_player(game):
    return game.members.players().exclude(user=game.admin).first()


class TestMemberWithdrawView:

    @pytest.mark.django_db
    def test_withdraw_marks_the_member_withdrawn(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)

        response = _withdraw(game, member)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["withdrawn"] is True
        member.refresh_from_db()
        assert member.withdrawn_at is not None

    @pytest.mark.django_db
    def test_withdraw_discards_orders_and_confirms_the_phase_state(
        self, active_game_factory, classical_london_province
    ):
        game = active_game_factory()
        member = _non_admin_player(game)
        phase_state = game.current_phase.phase_states.get(member=member)
        Order.objects.create(
            phase_state=phase_state, source=classical_london_province, order_type=OrderType.HOLD
        )

        _withdraw(game, member)

        phase_state.refresh_from_db()
        assert phase_state.orders_confirmed is True
        assert not Order.objects.filter(phase_state__member=member).exists()

    @pytest.mark.django_db
    def test_withdraw_resolves_the_phase_when_every_other_player_has_confirmed(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        phase = game.current_phase
        phase.phase_states.exclude(member=member).update(orders_confirmed=True)

        assert phase.id not in [p.id for p in Phase.objects.filter_due_phases()]

        _withdraw(game, member)

        assert phase.id in [p.id for p in Phase.objects.filter_due_phases()]

    @pytest.mark.django_db
    def test_withdrawn_seat_gets_no_orders_outcome(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        phase = game.current_phase

        _withdraw(game, member)
        Phase.objects.resolve(phase)

        phase.refresh_from_db()
        assert phase.status == PhaseStatus.COMPLETED
        assert phase.phase_states.get(member=member).orders_outcome is None
        assert phase.phase_states.exclude(member=member).filter(orders_outcome__isnull=False).exists()

    @pytest.mark.django_db
    def test_withdraw_is_allowed_in_a_paused_game(self, active_game_factory):
        game = active_game_factory()
        Game.objects.filter(id=game.id).update(paused_at=timezone.now())

        response = _withdraw(game, _non_admin_player(game))

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_withdraw_unauthenticated(self, unauthenticated_client, active_game_factory):
        game = active_game_factory()

        response = unauthenticated_client.patch(reverse(withdraw_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_withdraw_rejected_for_a_non_player(self, authenticated_client_for_tertiary_user, active_game_factory):
        game = active_game_factory()

        response = authenticated_client_for_tertiary_user.patch(reverse(withdraw_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdraw_rejected_for_a_game_master_without_a_seat(
        self, authenticated_client, active_game_with_game_master_factory
    ):
        game = active_game_with_game_master_factory()

        response = authenticated_client.patch(reverse(withdraw_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "departure",
        [
            {"eliminated_at": timezone.now()},
            {"civil_disorder_at": timezone.now()},
            {"removed_at": timezone.now()},
            {"withdrawn_at": timezone.now()},
        ],
    )
    def test_withdraw_rejected_for_a_member_who_cannot_act(self, active_game_factory, departure):
        game = active_game_factory()
        member = _non_admin_player(game)
        game.members.filter(id=member.id).update(**departure)

        response = _withdraw(game, member)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdraw_rejected_for_a_replaced_member(self, active_game_factory, tertiary_user):
        game = active_game_factory()
        member = _non_admin_player(game)
        Member.objects.remove(member)
        Member.objects.hand_over_seat(member, tertiary_user)

        response = _withdraw(game, member)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdraw_rejected_in_a_sandbox_game(self, authenticated_client, sandbox_game_with_phase_options):
        game = sandbox_game_with_phase_options

        response = authenticated_client.patch(reverse(withdraw_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "game_status",
        [GameStatus.PENDING, GameStatus.MUSTERING, GameStatus.COMPLETED, GameStatus.ABANDONED],
    )
    def test_withdraw_rejected_unless_the_game_is_active(self, active_game_factory, game_status):
        game = active_game_factory()
        Game.objects.filter(id=game.id).update(status=game_status)

        response = _withdraw(game, _non_admin_player(game))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_submit_orders(self, active_game_factory, classical_london_province):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = _client_for(member.user).post(
            reverse("order-create", args=[game.id]),
            {"selected": [classical_london_province.province_id]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_confirm_the_phase(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = _client_for(member.user).post(reverse("game-confirm-phase", args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_propose_a_draw(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = _client_for(member.user).post(reverse("draw-proposal-create", args=[game.id]), {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not DrawProposal.objects.filter(game=game).exists()

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_vote_on_a_draw(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        proposer = game.members.get(user=game.admin)
        _withdraw(game, member)
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=proposer)

        response = _client_for(member.user).patch(
            reverse("draw-proposal-vote", args=[game.id, proposal.id]), {"accepted": False}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert proposal.votes.get(member=member).accepted is True

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_retake_their_seat(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = _client_for(member.user).post(reverse(replace_viewname, args=[game.id, member.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdrawn_player_cannot_rejoin(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = _client_for(member.user).post(reverse(join_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_withdrawn_seat_can_be_taken_over(
        self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user
    ):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = authenticated_client_for_tertiary_user.post(reverse(replace_viewname, args=[game.id, member.id]))

        assert response.status_code == status.HTTP_201_CREATED
        member.refresh_from_db()
        assert member.replaced_by == game.members.get(user=tertiary_user)

    @pytest.mark.django_db
    def test_withdraw_cancels_the_players_own_draw_proposal(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=member)

        _withdraw(game, member)

        proposal.refresh_from_db()
        assert proposal.cancelled is True

    @pytest.mark.django_db
    def test_withdraw_accepts_other_draw_proposals_without_inclusion(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=game.members.get(user=game.admin))

        _withdraw(game, member)

        vote = proposal.votes.get(member=member)
        assert vote.accepted is True
        assert vote.included is False
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

    @pytest.mark.django_db
    def test_withdraw_completes_a_draw_only_the_player_was_holding_up(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=game.members.get(user=game.admin))
        proposal.votes.exclude(member=member).update(accepted=True)

        _withdraw(game, member)

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        victory = Victory.objects.get(game=game)
        assert member not in victory.members.all()
        assert victory.members.count() == game.members.players().count() - 1

    @pytest.mark.django_db
    def test_last_player_can_end_the_game_with_a_solo_draw(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        admin_member = game.members.get(user=game.admin)
        member = _non_admin_player(game)
        game.members.players().exclude(id__in=[admin_member.id, member.id]).update(civil_disorder_at=timezone.now())

        _withdraw(game, member)
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

        response = authenticated_client.post(reverse("draw-proposal-create", args=[game.id]), {}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        victory = Victory.objects.get(game=game)
        assert list(victory.members.all()) == [admin_member]

    @pytest.mark.django_db
    def test_withdrawal_by_the_last_playing_member_abandons_the_game(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)
        game.members.players().exclude(id=member.id).update(civil_disorder_at=timezone.now())

        _withdraw(game, member)

        game.refresh_from_db()
        assert game.status == GameStatus.ABANDONED

    @pytest.mark.django_db
    def test_withdrawal_reassigns_the_admin(self, active_game_factory, primary_user):
        game = active_game_factory()
        admin_member = game.members.get(user=primary_user)

        _withdraw(game, admin_member)

        game.refresh_from_db()
        assert game.admin_id is not None
        assert game.admin_id != primary_user.id

    @pytest.mark.django_db
    def test_withdrawal_notifies_the_other_players(self, active_game_factory):
        game = active_game_factory()
        member = _non_admin_player(game)

        _withdraw(game, member)

        recipients = set(
            Notification.objects.filter(event_type="withdrawal").values_list("recipient_id", flat=True)
        )
        others = set(game.members.players().exclude(id=member.id).values_list("user_id", flat=True))
        assert recipients == others

    @pytest.mark.django_db
    def test_withdrawn_member_is_serialized_as_withdrawn_and_not_removable(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        response = authenticated_client.get(reverse(retrieve_viewname, args=[game.id]))

        serialized = next(m for m in response.data["members"] if m["id"] == member.id)
        assert serialized["withdrawn"] is True
        assert serialized["removable"] is False
        assert serialized["replaceable"] is True


class TestCanWithdrawSerialization:

    @pytest.mark.django_db
    @pytest.mark.parametrize("viewname", [retrieve_viewname, list_viewname])
    def test_player_in_an_active_game_can_withdraw(self, authenticated_client, active_game_factory, viewname):
        game = active_game_factory()

        data = _game_data(authenticated_client, viewname, game)

        assert data["can_withdraw"] is True

    @pytest.mark.django_db
    @pytest.mark.parametrize("viewname", [retrieve_viewname, list_viewname])
    def test_withdrawn_player_cannot_withdraw_again(self, active_game_factory, viewname):
        game = active_game_factory()
        member = _non_admin_player(game)
        _withdraw(game, member)

        data = _game_data(_client_for(member.user), viewname, game)

        assert data["can_withdraw"] is False

    @pytest.mark.django_db
    def test_player_in_a_pending_game_cannot_withdraw(
        self, authenticated_client, pending_game_created_by_primary_user
    ):
        game = pending_game_created_by_primary_user

        data = _game_data(authenticated_client, retrieve_viewname, game)

        assert data["can_withdraw"] is False

    @pytest.mark.django_db
    def test_non_player_cannot_withdraw(self, authenticated_client_for_tertiary_user, active_game_factory):
        game = active_game_factory()

        data = _game_data(authenticated_client_for_tertiary_user, retrieve_viewname, game)

        assert data["can_withdraw"] is False


def _game_data(client, viewname, game):
    if viewname == retrieve_viewname:
        return client.get(reverse(retrieve_viewname, args=[game.id])).data
    response = client.get(reverse(list_viewname))
    return next(g for g in response.data["results"] if g["id"] == game.id)


member_retrieve_viewname = "game-member-retrieve"


def _actions(response):
    return [(action["key"], action["blocked_reason"]) for action in response.data["actions"]]


class TestMemberRetrieveView:

    def _other_member(self, game):
        return game.members.players().exclude(user=game.admin).first()

    def _retrieve(self, client, member):
        return client.get(reverse(member_retrieve_viewname, args=[member.game_id, member.id]))

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, active_game_factory):
        game = active_game_factory()

        response = self._retrieve(unauthenticated_client, self._other_member(game))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_member_of_another_game_not_found(
        self, authenticated_client, active_game_factory, pending_game_created_by_secondary_user
    ):
        game = active_game_factory()
        member = self._other_member(game)

        url = reverse(member_retrieve_viewname, args=[pending_game_created_by_secondary_user.id, member.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_nonexistent_member_not_found(self, authenticated_client, active_game_factory):
        game = active_game_factory()

        url = reverse(member_retrieve_viewname, args=[game.id, 0])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_returns_the_members_place_in_the_game(self, authenticated_client, active_game_factory):
        game = active_game_factory(nmr_extensions_allowed=2)
        member = self._other_member(game)

        response = self._retrieve(authenticated_client, member)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == member.id
        assert response.data["user_id"] == member.user_id
        assert response.data["name"] == member.user.profile.name
        assert response.data["is_current_user"] is False
        assert response.data["is_bot"] is False
        assert response.data["is_admin"] is False
        assert response.data["nation"] == member.nation.name
        assert response.data["participation_status"] == "playing"
        assert response.data["nmr_extensions_remaining"] == 2
        assert response.data["nmr_extensions_allowed"] == 2

    @pytest.mark.django_db
    def test_reports_the_admin(self, authenticated_client_for_secondary_user, active_game_factory, primary_user):
        game = active_game_factory()
        member = game.members.get(user=primary_user)

        response = self._retrieve(authenticated_client_for_secondary_user, member)

        assert response.data["is_admin"] is True

    @pytest.mark.django_db
    def test_masks_identity_in_an_anonymous_game(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        game.anonymous = True
        game.save()
        member = self._other_member(game)

        response = self._retrieve(authenticated_client, member)

        assert response.data["user_id"] is None
        assert response.data["name"] == "Anonymous"
        assert response.data["picture"] is None
        assert response.data["nation"] == member.nation.name

    @pytest.mark.django_db
    def test_does_not_mask_the_requesting_user_in_an_anonymous_game(
        self, authenticated_client, active_game_factory, primary_user
    ):
        game = active_game_factory()
        game.anonymous = True
        game.save()
        member = game.members.get(user=primary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["user_id"] == primary_user.id
        assert response.data["is_current_user"] is True

    @pytest.mark.django_db
    def test_game_master_status(self, authenticated_client, pending_game_with_game_master_factory):
        game = pending_game_with_game_master_factory()
        member = game.members.get(kind=MemberKind.GAME_MASTER)

        response = self._retrieve(authenticated_client, member)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["participation_status"] == "game_master"
        assert response.data["nation"] is None

    @pytest.mark.django_db
    def test_replaced_status_takes_precedence_over_removed(
        self, authenticated_client, active_game_factory, tertiary_user
    ):
        game = active_game_factory()
        member = self._other_member(game)
        Member.objects.remove(member)
        Member.objects.hand_over_seat(member, tertiary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "replaced"

    @pytest.mark.django_db
    def test_removed_status_takes_precedence_over_withdrawn(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        member.withdrawn_at = timezone.now()
        member.removed_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "removed"

    @pytest.mark.django_db
    def test_withdrawn_status_takes_precedence_over_victory(
        self, authenticated_client, active_game_factory, victory_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        member.withdrawn_at = timezone.now()
        member.save()
        victory = victory_factory(game=game, winning_phase=game.current_phase)
        victory.members.add(member)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "withdrawn"

    @pytest.mark.django_db
    def test_won_status_for_a_solo_victory(self, authenticated_client, active_game_factory, victory_factory):
        game = active_game_factory()
        member = self._other_member(game)
        victory = victory_factory(game=game, winning_phase=game.current_phase)
        victory.members.add(member)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "won"

    @pytest.mark.django_db
    def test_drew_status_for_a_draw(self, authenticated_client, active_game_factory, victory_factory, primary_user):
        game = active_game_factory()
        member = self._other_member(game)
        victory = victory_factory(game=game, winning_phase=game.current_phase)
        victory.members.add(member, game.members.get(user=primary_user))

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "drew"

    @pytest.mark.django_db
    def test_victory_status_takes_precedence_over_eliminated(
        self, authenticated_client, active_game_factory, victory_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        member.eliminated_at = timezone.now()
        member.save()
        victory = victory_factory(game=game, winning_phase=game.current_phase)
        victory.members.add(member)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "won"

    @pytest.mark.django_db
    def test_member_outside_the_victory_keeps_their_own_status(
        self, authenticated_client, active_game_factory, victory_factory, primary_user
    ):
        game = active_game_factory()
        member = self._other_member(game)
        victory = victory_factory(game=game, winning_phase=game.current_phase)
        victory.members.add(game.members.get(user=primary_user))

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "playing"

    @pytest.mark.django_db
    def test_eliminated_status_takes_precedence_over_civil_disorder(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        member.eliminated_at = timezone.now()
        member.civil_disorder_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "eliminated"

    @pytest.mark.django_db
    def test_civil_disorder_status(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        member.civil_disorder_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "civil_disorder"

    @pytest.mark.django_db
    def test_seat_unconfirmed_status_in_a_mustering_game(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        game.status = GameStatus.MUSTERING
        game.save()
        member = game.members.create(user=secondary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "seat_unconfirmed"

    @pytest.mark.django_db
    def test_seat_confirmed_status_once_mustered(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        game.status = GameStatus.MUSTERING
        game.save()
        member = game.members.create(user=secondary_user, mustered_at=timezone.now())

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "seat_confirmed"

    @pytest.mark.django_db
    def test_bot_seat_is_confirmed_in_a_mustering_game(
        self, authenticated_client, pending_game_created_by_primary_user, bot_user
    ):
        game = pending_game_created_by_primary_user
        game.status = GameStatus.MUSTERING
        game.save()
        member = game.members.create(user=bot_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "seat_confirmed"

    @pytest.mark.django_db
    def test_joined_status_in_a_pending_game(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        member = game.members.create(user=secondary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["participation_status"] == "joined"

    @pytest.mark.django_db
    def test_counts_units_and_supply_centers_from_the_current_phase(
        self,
        authenticated_client,
        active_game_with_phase_state,
        primary_user,
        classical_england_nation,
        classical_london_province,
        classical_liverpool_province,
    ):
        game = active_game_with_phase_state
        previous_phase = game.current_phase
        previous_phase.status = PhaseStatus.COMPLETED
        previous_phase.save()
        phase = game.phases.create(
            variant=game.variant,
            season="Fall",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=2,
        )
        phase.units.create(type="Army", nation=classical_england_nation, province=classical_london_province)
        phase.units.create(type="Army", nation=classical_england_nation, province=classical_liverpool_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_london_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_liverpool_province)
        phase.supply_centers.create(nation=classical_england_nation, province=previous_phase.units.first().province)

        response = self._retrieve(authenticated_client, game.members.get(user=primary_user))

        assert response.data["unit_count"] == 2
        assert response.data["supply_center_count"] == 3

    @pytest.mark.django_db
    def test_counts_are_null_before_the_game_starts(
        self, authenticated_client, pending_game_created_by_primary_user, primary_user
    ):
        member = pending_game_created_by_primary_user.members.get(user=primary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["unit_count"] is None
        assert response.data["supply_center_count"] is None

    @pytest.mark.django_db
    def test_counts_are_null_without_a_nation(self, authenticated_client, active_game_with_game_master_factory):
        game = active_game_with_game_master_factory()
        member = game.members.get(kind=MemberKind.GAME_MASTER)

        response = self._retrieve(authenticated_client, member)

        assert response.data["unit_count"] is None
        assert response.data["supply_center_count"] is None

    @pytest.mark.django_db
    def test_returns_nation_preferences_to_the_requesting_user_in_a_pending_game(
        self,
        authenticated_client,
        pending_game_created_by_primary_user,
        primary_user,
        classical_france_nation,
        classical_england_nation,
    ):
        member = pending_game_created_by_primary_user.members.get(user=primary_user)
        Member.objects.set_nation_preferences(member, [classical_france_nation, classical_england_nation])

        response = self._retrieve(authenticated_client, member)

        assert response.data["nation_preferences"] == [classical_france_nation.name, classical_england_nation.name]

    @pytest.mark.django_db
    def test_hides_nation_preferences_of_other_members(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user, classical_france_nation
    ):
        member = pending_game_created_by_primary_user.members.create(user=secondary_user)
        Member.objects.set_nation_preferences(member, [classical_france_nation])

        response = self._retrieve(authenticated_client, member)

        assert response.data["nation_preferences"] is None

    @pytest.mark.django_db
    def test_hides_nation_preferences_once_the_game_starts(
        self, authenticated_client, active_game_factory, primary_user
    ):
        member = active_game_factory().members.get(user=primary_user)

        response = self._retrieve(authenticated_client, member)

        assert response.data["nation_preferences"] is None

    @pytest.mark.django_db
    def test_own_member_returns_the_seat_actions(self, authenticated_client, active_game_factory, primary_user):
        game = active_game_factory()
        member = game.members.get(user=primary_user)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("withdraw", None)]

    @pytest.mark.django_db
    def test_own_member_offers_confirm_seat_and_leave_while_mustering(
        self, authenticated_client, pending_game_created_by_primary_user, primary_user
    ):
        game = pending_game_created_by_primary_user
        game.status = GameStatus.MUSTERING
        game.save()

        response = self._retrieve(authenticated_client, game.members.get(user=primary_user))

        assert _actions(response) == [("confirm_seat", None), ("leave", None)]

    @pytest.mark.django_db
    def test_playing_member_offers_no_actions_to_another_player(
        self, authenticated_client_for_secondary_user, active_game_factory, secondary_user, primary_user
    ):
        game = active_game_factory()
        players = list(game.members.players().exclude(user=primary_user))
        players[0].user = secondary_user
        players[0].save()

        response = self._retrieve(authenticated_client_for_secondary_user, players[1])

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_replaceable_seat_offers_take_over_to_an_outsider(
        self, authenticated_client_for_tertiary_user, active_game_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        Member.objects.remove(member)

        response = self._retrieve(authenticated_client_for_tertiary_user, member)

        assert _actions(response) == [("take_over", None), ("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_take_over_blocked_when_commitment_is_too_low(
        self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user, set_commitment
    ):
        game = active_game_factory()
        member = self._other_member(game)
        Member.objects.remove(member)
        set_commitment(tertiary_user, Commitment.LOW)

        response = self._retrieve(authenticated_client_for_tertiary_user, member)

        assert _actions(response) == [("take_over", "commitment_too_low"), ("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_take_over_blocked_when_the_game_requires_committed_players(
        self, authenticated_client_for_tertiary_user, active_game_factory, tertiary_user, set_commitment
    ):
        game = active_game_factory()
        game.commitment_requirement = CommitmentRequirement.COMMITTED
        game.save()
        member = self._other_member(game)
        Member.objects.remove(member)
        set_commitment(tertiary_user, Commitment.MEDIUM)

        response = self._retrieve(authenticated_client_for_tertiary_user, member)

        assert _actions(response) == [("take_over", "commitment_too_low"), ("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_replaceable_seat_offers_only_the_link_to_a_player(
        self, authenticated_client_for_secondary_user, active_game_factory, secondary_user, primary_user
    ):
        game = active_game_factory()
        players = list(game.members.players().exclude(user=primary_user))
        players[0].user = secondary_user
        players[0].save()
        Member.objects.remove(players[1])

        response = self._retrieve(authenticated_client_for_secondary_user, players[1])

        assert _actions(response) == [("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_replaceable_seat_offers_only_the_link_to_a_former_player(
        self, authenticated_client_for_secondary_user, active_game_factory, secondary_user, primary_user
    ):
        game = active_game_factory()
        players = list(game.members.players().exclude(user=primary_user))
        players[0].user = secondary_user
        players[0].save()
        Member.objects.remove(players[0])
        Member.objects.remove(players[1])

        response = self._retrieve(authenticated_client_for_secondary_user, players[1])

        assert _actions(response) == [("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_replaceable_seat_offers_only_the_link_to_the_game_master(
        self, authenticated_client_factory, active_game_with_game_master_factory
    ):
        game = active_game_with_game_master_factory()
        member = game.members.players().first()
        Member.objects.remove(member)

        response = self._retrieve(authenticated_client_factory(game.game_master), member)

        assert _actions(response) == [("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_replaced_seat_offers_no_actions(self, authenticated_client_for_tertiary_user, active_game_factory, user_factory):
        game = active_game_factory()
        member = self._other_member(game)
        Member.objects.remove(member)
        Member.objects.hand_over_seat(member, user_factory())

        response = self._retrieve(authenticated_client_for_tertiary_user, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_finished_game_offers_no_take_over(self, authenticated_client_for_tertiary_user, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        Member.objects.remove(member)
        game.status = GameStatus.COMPLETED
        game.save()

        response = self._retrieve(authenticated_client_for_tertiary_user, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_manager_can_remove_a_player_from_a_pending_game(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        member = pending_game_created_by_primary_user.members.create(user=secondary_user)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("remove_from_lobby", None)]

    @pytest.mark.django_db
    def test_manager_can_remove_a_player_from_a_mustering_game(
        self, authenticated_client, pending_game_created_by_primary_user, secondary_user
    ):
        game = pending_game_created_by_primary_user
        game.status = GameStatus.MUSTERING
        game.save()
        member = game.members.create(user=secondary_user)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("remove_from_lobby", None)]

    @pytest.mark.django_db
    def test_lobby_removal_not_offered_to_other_players(
        self, authenticated_client_for_secondary_user, pending_game_created_by_primary_user, secondary_user, tertiary_user
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=secondary_user)
        member = game.members.create(user=tertiary_user)

        response = self._retrieve(authenticated_client_for_secondary_user, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_lobby_removal_not_offered_for_the_game_master(
        self, authenticated_client_for_secondary_user, pending_game_with_game_master_factory, secondary_user
    ):
        game = pending_game_with_game_master_factory()
        game.admin = secondary_user
        game.save()
        game.members.create(user=secondary_user)
        member = game.members.get(kind=MemberKind.GAME_MASTER)

        response = self._retrieve(authenticated_client_for_secondary_user, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_removal_from_game_blocked_until_the_player_misses_orders(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("remove_from_game", "no_missed_orders")]

    @pytest.mark.django_db
    def test_removal_from_game_available_after_missed_orders(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        _record_nmr(game, member)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("remove_from_game", None)]

    @pytest.mark.django_db
    def test_civil_disorder_seat_offers_link_and_removal_to_the_manager(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        member.civil_disorder_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("share_replacement_link", None), ("remove_from_game", None)]

    @pytest.mark.django_db
    def test_removal_from_game_not_offered_for_a_removed_player(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        _record_nmr(game, member)
        Member.objects.remove(member)

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_removal_from_game_not_offered_for_a_withdrawn_player(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = self._other_member(game)
        member.withdrawn_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == [("share_replacement_link", None)]

    @pytest.mark.django_db
    def test_removal_from_game_not_offered_for_a_bot(self, authenticated_client, active_game_factory, bot_user):
        game = active_game_factory()
        member = self._other_member(game)
        member.user = bot_user
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_removal_from_game_not_offered_for_an_eliminated_player_in_civil_disorder(
        self, authenticated_client, active_game_factory
    ):
        game = active_game_factory()
        member = self._other_member(game)
        member.eliminated_at = timezone.now()
        member.civil_disorder_at = timezone.now()
        member.save()

        response = self._retrieve(authenticated_client, member)

        assert _actions(response) == []

    @pytest.mark.django_db
    def test_removal_from_game_not_offered_to_other_players(
        self, authenticated_client_for_secondary_user, active_game_factory, secondary_user, primary_user
    ):
        game = active_game_factory()
        players = list(game.members.players().exclude(user=primary_user))
        players[0].user = secondary_user
        players[0].save()
        _record_nmr(game, players[1])

        response = self._retrieve(authenticated_client_for_secondary_user, players[1])

        assert _actions(response) == []


class TestMemberRetrieveViewQueryPerformance:

    @pytest.mark.django_db
    def test_retrieve_member_query_count(self, authenticated_client, active_game_factory):
        game = active_game_factory()
        member = game.members.players().exclude(user=game.admin).first()
        _record_nmr(game, member)

        url = reverse(member_retrieve_viewname, args=[game.id, member.id])
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        query_count = len(connection.queries)
        assert query_count == 7
