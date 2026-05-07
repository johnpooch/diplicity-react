import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from game.models import Game
from user_profile.models import UserProfile
from common.constants import (
    GameStatus,
    MemberOutcomeState,
    PhaseStatus,
    PhaseType,
)
from member.utils import classify_outcomes_for_finished_game, kick_inactive_members

User = get_user_model()

join_viewname = "game-join"
retrieve_viewname = "game-retrieve"


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


class TestClassifyOutcomesForFinishedGame:

    def _make_finished_game(self, variant, sandbox=False):
        return Game.objects.create(
            name="Outcome Test Game",
            variant=variant,
            status=GameStatus.COMPLETED,
            sandbox=sandbox,
        )

    def _add_movement_phase(self, game, ordinal, member_to_unit, member_to_orders):
        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1900 + ordinal,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=ordinal,
        )
        for member, province in member_to_unit.items():
            phase.units.create(type="Fleet", nation=member.nation, province=province)
        for member, has_order in member_to_orders.items():
            phase_state = phase.phase_states.create(member=member, has_possible_orders=True)
            if has_order:
                province = member_to_unit.get(member)
                if province is not None:
                    phase_state.orders.create(source=province, order_type="Hold")
        return phase

    @pytest.mark.django_db
    def test_member_with_all_orders_classified_completed(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: True},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.COMPLETED

    @pytest.mark.django_db
    def test_member_with_two_consecutive_nmrs_classified_completed(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal, has_order in [(1, True), (2, False), (3, False), (4, True)]:
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: has_order},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.COMPLETED

    @pytest.mark.django_db
    def test_member_with_three_consecutive_nmrs_classified_abandoned(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal, has_order in [(1, True), (2, False), (3, False), (4, False)]:
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: has_order},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.ABANDONED

    @pytest.mark.django_db
    def test_streak_resets_when_member_submits_orders(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Two NMRs, one order, two NMRs — longest streak is 2
        for ordinal, has_order in [(1, False), (2, False), (3, True), (4, False), (5, False)]:
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: has_order},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.COMPLETED

    @pytest.mark.django_db
    def test_kicked_member_classified_abandoned(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(
            user=primary_user, nation=classical_england_nation, kicked=True
        )

        # Even with all orders submitted, kicked overrides
        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: True},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.ABANDONED

    @pytest.mark.django_db
    def test_phases_without_units_dont_count_toward_streak(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Eliminated member: had units in phase 1, then no units in phases 2-5.
        # Phase 1 NMR + phases 2-5 with no units = streak of 1, not 5.
        for ordinal in range(1, 6):
            member_to_unit = {member: classical_edinburgh_province} if ordinal == 1 else {}
            self._add_movement_phase(
                game,
                ordinal,
                member_to_unit,
                {member: False},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.COMPLETED

    @pytest.mark.django_db
    def test_game_master_not_classified(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        gm = game.members.create(user=primary_user, is_game_master=True)

        classify_outcomes_for_finished_game(game)
        gm.refresh_from_db()
        assert gm.outcome_state is None

    @pytest.mark.django_db
    def test_sandbox_game_not_classified(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant, sandbox=True)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 5):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state is None

    @pytest.mark.django_db
    def test_only_movement_phases_count(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_finished_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Three retreat-phase NMRs do not classify as Abandoned
        for ordinal in range(1, 4):
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1900 + ordinal,
                type=PhaseType.RETREAT,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.units.create(
                type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province
            )
            phase.phase_states.create(member=member, has_possible_orders=True)

        classify_outcomes_for_finished_game(game)
        member.refresh_from_db()
        assert member.outcome_state == MemberOutcomeState.COMPLETED


class TestKickInactiveMembers:

    def _make_active_game(self, variant, sandbox=False):
        return Game.objects.create(
            name="Kick Test Game",
            variant=variant,
            status=GameStatus.ACTIVE,
            sandbox=sandbox,
        )

    def _add_movement_phase(self, game, ordinal, member_to_unit, member_to_orders):
        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1900 + ordinal,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
            ordinal=ordinal,
        )
        for member, province in member_to_unit.items():
            phase.units.create(type="Fleet", nation=member.nation, province=province)
        for member, has_order in member_to_orders.items():
            phase_state = phase.phase_states.create(member=member, has_possible_orders=True)
            if has_order:
                province = member_to_unit.get(member)
                if province is not None:
                    phase_state.orders.create(source=province, order_type="Hold")
        return phase

    @pytest.mark.django_db
    def test_member_with_three_consecutive_movement_nmrs_is_kicked(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is True
        assert kicked == [member]

    @pytest.mark.django_db
    def test_member_with_two_consecutive_movement_nmrs_not_kicked(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 3):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False
        assert kicked == []

    @pytest.mark.django_db
    def test_member_with_recent_order_not_kicked(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Three NMRs followed by an order — the most recent 3 phases include the order, so no kick.
        for ordinal, has_order in [(1, False), (2, False), (3, False), (4, True)]:
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: has_order},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False
        assert kicked == []

    @pytest.mark.django_db
    def test_kick_uses_only_most_recent_three_movement_phases(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # First three phases NMR, fourth has an order. Must not kick — recent 3 are 2,3,4 with an order at 4.
        for ordinal, has_order in [(1, False), (2, False), (3, False), (4, True)]:
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: has_order},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False

    @pytest.mark.django_db
    def test_eliminated_member_not_kicked(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Lost units after phase 1 — phases 2, 3 have no units → cannot accumulate streak in last 3.
        for ordinal in range(1, 4):
            member_to_unit = {member: classical_edinburgh_province} if ordinal == 1 else {}
            self._add_movement_phase(
                game,
                ordinal,
                member_to_unit,
                {member: False},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False

    @pytest.mark.django_db
    def test_game_master_not_kicked(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        gm = game.members.create(user=primary_user, is_game_master=True)

        for ordinal in range(1, 4):
            self._add_movement_phase(game, ordinal, {}, {})

        kicked = kick_inactive_members(game)
        gm.refresh_from_db()
        assert gm.kicked is False
        assert kicked == []

    @pytest.mark.django_db
    def test_already_kicked_member_skipped(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(
            user=primary_user, nation=classical_england_nation, kicked=True
        )

        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        kicked = kick_inactive_members(game)
        # Already kicked, not re-included in the returned set.
        assert kicked == []

    @pytest.mark.django_db
    def test_sandbox_game_no_kicks(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant, sandbox=True)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False
        assert kicked == []

    @pytest.mark.django_db
    def test_retreat_phases_dont_count_toward_threshold(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        # Two movement-phase NMRs interspersed with retreat phases that also have no orders.
        # Retreats shouldn't count, so streak is only 2 movement phases — no kick.
        for ordinal, phase_type in [
            (1, PhaseType.MOVEMENT),
            (2, PhaseType.RETREAT),
            (3, PhaseType.MOVEMENT),
        ]:
            phase = game.phases.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1900 + ordinal,
                type=phase_type,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            phase.units.create(
                type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province
            )
            phase.phase_states.create(member=member, has_possible_orders=True)

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False
        assert kicked == []

    @pytest.mark.django_db
    def test_multiple_members_kicked_simultaneously(
        self,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_paris_province,
        primary_user,
        secondary_user,
    ):
        game = self._make_active_game(classical_variant)
        member_a = game.members.create(user=primary_user, nation=classical_england_nation)
        member_b = game.members.create(user=secondary_user, nation=classical_france_nation)

        for ordinal in range(1, 4):
            self._add_movement_phase(
                game,
                ordinal,
                {
                    member_a: classical_edinburgh_province,
                    member_b: classical_paris_province,
                },
                {
                    member_a: False,
                    member_b: False,
                },
            )

        kicked = kick_inactive_members(game)
        member_a.refresh_from_db()
        member_b.refresh_from_db()
        assert member_a.kicked is True
        assert member_b.kicked is True
        assert set(kicked) == {member_a, member_b}

    @pytest.mark.django_db
    def test_fewer_than_three_movement_phases_no_kicks(
        self, classical_variant, classical_england_nation, classical_edinburgh_province, primary_user
    ):
        game = self._make_active_game(classical_variant)
        member = game.members.create(user=primary_user, nation=classical_england_nation)

        for ordinal in range(1, 3):
            self._add_movement_phase(
                game,
                ordinal,
                {member: classical_edinburgh_province},
                {member: False},
            )

        kicked = kick_inactive_members(game)
        member.refresh_from_db()
        assert member.kicked is False
        assert kicked == []
