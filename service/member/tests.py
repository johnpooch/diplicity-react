import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from game.models import Game
from phase.models import Phase
from user_profile.models import UserProfile
from common.constants import GameStatus, NationAssignment

User = get_user_model()

join_viewname = "game-join"
retrieve_viewname = "game-retrieve"


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
def test_join_game_member_is_not_game_master(
    authenticated_client, pending_game_created_by_secondary_user, primary_user
):
    """
    Test that a user who joins an existing game is NOT set as game master.
    Only the creator should be the game master.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["is_game_master"] is False

    member = pending_game_created_by_secondary_user.members.get(user=primary_user)
    assert member.is_game_master is False


@pytest.mark.django_db
def test_game_has_exactly_one_game_master(
    authenticated_client, pending_game_created_by_secondary_user, primary_user, secondary_user
):
    """
    Test that a game can only have one game master (the creator).
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED

    game = pending_game_created_by_secondary_user
    game_masters = game.members.filter(is_game_master=True)
    assert game_masters.count() == 1
    assert game_masters.first().user == secondary_user


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
