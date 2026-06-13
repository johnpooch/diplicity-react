import pytest
from types import SimpleNamespace
from django.contrib.auth import get_user_model

from common.constants import GameStatus, PhaseType, PhaseStatus, UnitType
from common.permissions import (
    IsGameMember,
    IsActiveGameMember,
    IsNotGameMember,
    IsInCivilDisorder,
    IsGameCreator,
)
from draw_proposal.models import DrawProposal
from game.models import Game
from member.models import Member
from phase.models import Phase, PhaseState
from user_profile.utils import get_player_stats
from victory.utils import check_for_solo_winner

User = get_user_model()


def _permission_request(user, game):
    return SimpleNamespace(user=user), SimpleNamespace(kwargs={"game_id": game.id})


@pytest.fixture
def replaced_seat(db, classical_variant, classical_england_nation, primary_user, secondary_user):
    game = Game.objects.create(
        variant=classical_variant,
        name="Replacement Hardening",
        status=GameStatus.ACTIVE,
    )
    successor = Member.objects.create(
        game=game, user=secondary_user, nation=classical_england_nation
    )
    predecessor = Member.objects.create(
        game=game,
        user=primary_user,
        nation=classical_england_nation,
        civil_disorder=True,
        replaced_by=successor,
    )
    return game, predecessor, successor


class TestPermissionsExcludeReplacedMembers:

    @pytest.mark.django_db
    def test_is_game_member(self, replaced_seat, primary_user, secondary_user):
        game, predecessor, successor = replaced_seat

        request, view = _permission_request(primary_user, game)
        assert IsGameMember().has_permission(request, view) is False

        request, view = _permission_request(secondary_user, game)
        assert IsGameMember().has_permission(request, view) is True

    @pytest.mark.django_db
    def test_is_active_game_member(self, replaced_seat, primary_user, secondary_user):
        game, predecessor, successor = replaced_seat

        request, view = _permission_request(primary_user, game)
        permission = IsActiveGameMember()
        assert permission.has_permission(request, view) is False
        assert permission.message == "User is not a member of the game."

        request, view = _permission_request(secondary_user, game)
        assert IsActiveGameMember().has_permission(request, view) is True

    @pytest.mark.django_db
    def test_is_not_game_member(self, replaced_seat, primary_user, secondary_user):
        game, predecessor, successor = replaced_seat

        request, view = _permission_request(primary_user, game)
        assert IsNotGameMember().has_permission(request, view) is True

        request, view = _permission_request(secondary_user, game)
        assert IsNotGameMember().has_permission(request, view) is False

    @pytest.mark.django_db
    def test_is_in_civil_disorder(self, replaced_seat, primary_user, secondary_user):
        game, predecessor, successor = replaced_seat

        request, view = _permission_request(primary_user, game)
        permission = IsInCivilDisorder()
        assert permission.has_permission(request, view) is False
        assert permission.message == "User is not a member of the game."

    @pytest.mark.django_db
    def test_is_game_creator_with_replaced_creator(
        self, replaced_seat, primary_user, secondary_user
    ):
        game, predecessor, successor = replaced_seat
        game.created_by = primary_user
        game.save()

        request, view = _permission_request(primary_user, game)
        permission = IsGameCreator()
        assert permission.has_permission(request, view) is False
        assert permission.message == "User is not a member of the game."

    @pytest.mark.django_db
    def test_is_game_creator_with_active_creator(
        self, replaced_seat, secondary_user
    ):
        game, predecessor, successor = replaced_seat
        game.created_by = secondary_user
        game.save()

        request, view = _permission_request(secondary_user, game)
        assert IsGameCreator().has_permission(request, view) is True


class TestPhaseQueriesExcludeReplacedMembers:

    @pytest.mark.django_db
    def test_check_eliminations_ignores_replaced_member(
        self,
        elimination_game_factory,
        user_factory,
        italy_vs_germany_variant,
        italy_vs_germany_italy_nation,
        italy_vs_germany_germany_nation,
        italy_vs_germany_kiel_province,
        in_memory_procrastinate,
    ):
        game, italy, germany = elimination_game_factory()
        predecessor = Member.objects.create(
            game=game, user=user_factory(), nation=italy_vs_germany_italy_nation, replaced_by=italy
        )

        previous_phase = Phase.objects.create(
            game=game, variant=italy_vs_germany_variant,
            season="Spring", year=1901, type=PhaseType.MOVEMENT,
            ordinal=1, status=PhaseStatus.COMPLETED,
        )
        new_phase = Phase.objects.create(
            game=game, variant=italy_vs_germany_variant,
            season="Fall", year=1901, type=PhaseType.MOVEMENT,
            ordinal=2, status=PhaseStatus.ACTIVE,
        )
        new_phase.units.create(
            province=italy_vs_germany_kiel_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
        )
        new_phase.supply_centers.create(
            province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation
        )

        Phase.objects._check_eliminations(previous_phase, new_phase)

        italy.refresh_from_db()
        germany.refresh_from_db()
        predecessor.refresh_from_db()
        assert italy.eliminated is True
        assert germany.eliminated is False
        assert predecessor.eliminated is False

    @pytest.mark.django_db
    def test_check_abandonment_ignores_replaced_member(
        self,
        db,
        user_factory,
        italy_vs_germany_variant,
        italy_vs_germany_italy_nation,
        primary_user,
    ):
        game = Game.objects.create(
            variant=italy_vs_germany_variant,
            name="Abandonment Replacement",
            status=GameStatus.ACTIVE,
        )
        successor = Member.objects.create(
            game=game, user=primary_user, nation=italy_vs_germany_italy_nation, civil_disorder=True
        )
        Member.objects.create(
            game=game, user=user_factory(), nation=italy_vs_germany_italy_nation,
            civil_disorder=False, replaced_by=successor,
        )

        assert Phase.objects._check_abandonment(game) is True

    @pytest.mark.django_db
    def test_new_phase_states_skip_replaced_member(
        self,
        italy_vs_germany_phase_with_orders,
        mock_adjudication_data_basic,
        user_factory,
        italy_vs_germany_italy_nation,
        primary_user,
    ):
        phase = italy_vs_germany_phase_with_orders
        game = phase.game
        active_italy = game.members.get(user=primary_user)
        predecessor = Member.objects.create(
            game=game, user=user_factory(), nation=italy_vs_germany_italy_nation, replaced_by=active_italy
        )

        new_phase = Phase.objects.create_from_adjudication_data(phase, mock_adjudication_data_basic)

        assert new_phase.phase_states.count() == 2
        assert not new_phase.phase_states.filter(member=predecessor).exists()


class TestDrawVotesExcludeReplacedMembers:

    @pytest.mark.django_db
    def test_create_proposal_skips_replaced_member(
        self,
        db,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        primary_user,
        secondary_user,
        user_factory,
    ):
        game = Game.objects.create(
            variant=classical_variant,
            name="Draw Replacement",
            status=GameStatus.ACTIVE,
        )
        phase = Phase.objects.create(
            game=game, variant=classical_variant,
            season="Spring", year=1901, type=PhaseType.MOVEMENT,
            ordinal=1, status=PhaseStatus.ACTIVE,
        )
        proposer = Member.objects.create(
            game=game, user=primary_user, nation=classical_england_nation
        )
        successor = Member.objects.create(
            game=game, user=secondary_user, nation=classical_france_nation
        )
        predecessor = Member.objects.create(
            game=game, user=user_factory(), nation=classical_france_nation, replaced_by=successor
        )

        proposal = DrawProposal.objects.create_proposal(game, created_by=proposer)

        assert proposal.votes.count() == 2
        assert not proposal.votes.filter(member=predecessor).exists()


class TestSoloWinnerIgnoresReplacedMembers:

    @pytest.mark.django_db
    def test_check_for_solo_winner_ignores_replaced_member(
        self,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        user_factory,
        classical_variant,
        classical_england_nation,
    ):
        game = game_factory(variant=classical_variant, variant__solo_victory_sc_count=3)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        active = member_factory(game=game, nation=classical_england_nation)
        member_factory(
            game=game, user=user_factory(), nation=classical_england_nation, replaced_by=active
        )

        for _ in range(3):
            supply_center_factory(phase=phase, nation=classical_england_nation)

        result = check_for_solo_winner(game, phase)

        assert result == active


class TestPlayerStatsRetiredPolicy:

    @pytest.mark.django_db
    def test_retired_member_kept_in_record_excluded_from_tally(
        self,
        classical_variant,
        classical_england_nation,
        user_factory,
    ):
        from django.utils import timezone

        user = user_factory()
        game = Game.objects.create(
            name="Retired Record Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
        )
        successor = game.members.create(user=user_factory(), nation=classical_england_nation)
        retired = game.members.create(
            user=user, nation=classical_england_nation,
            civil_disorder=True, replaced_by=successor,
        )
        phase = game.phases.create(
            variant=classical_variant, season="Spring", year=1901,
            type=PhaseType.MOVEMENT, status=PhaseStatus.COMPLETED, ordinal=1,
        )
        phase.phase_states.create(
            member=retired, has_possible_orders=True,
            orders_outcome=PhaseState.OrdersOutcome.NMR,
        )

        stats = get_player_stats(user)

        assert stats["total_games"] == 0
        assert stats["solo_wins"] == 0
        assert stats["draws"] == 0
        assert stats["losses"] == 0
        assert stats["nmr_rate"] == 1.0
        assert stats["cd_rate"] == 1.0
        assert stats["reliability_tier"] == "new"

    @pytest.mark.django_db
    def test_active_membership_counted_retired_membership_excluded(
        self,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        user_factory,
    ):
        from django.utils import timezone

        user = user_factory()

        active_game = Game.objects.create(
            name="Active Tally Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
        )
        active_game.members.create(user=user, nation=classical_england_nation)

        retired_game = Game.objects.create(
            name="Retired Tally Game",
            variant=classical_variant,
            status=GameStatus.COMPLETED,
            finished_at=timezone.now(),
        )
        successor = retired_game.members.create(
            user=user_factory(), nation=classical_france_nation
        )
        retired_game.members.create(
            user=user, nation=classical_france_nation, replaced_by=successor
        )

        stats = get_player_stats(user)

        assert stats["total_games"] == 1
        assert stats["losses"] == 1
