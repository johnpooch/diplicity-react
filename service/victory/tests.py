import pytest
from django.db import IntegrityError
from rest_framework.test import APIRequestFactory
from common.constants import PhaseType, PhaseStatus, GameStatus
from victory.models import Victory
from victory.utils import check_for_solo_winner
from victory.constants import VictoryType
from victory.serializers import VictorySerializer


class TestCheckForSoloWinner:

    @pytest.mark.parametrize(
        "threshold,sc_counts,winner_index",
        [
            pytest.param(18, [18, 16], 0, id="clear_solo_winner_at_threshold"),
            pytest.param(18, [20, 14], 0, id="solo_winner_above_threshold"),
            pytest.param(18, [17, 16], None, id="no_winner_below_threshold"),
            pytest.param(18, [18, 18], None, id="no_winner_when_tied_at_threshold"),
            pytest.param(18, [19, 19], None, id="no_winner_when_tied_above_threshold"),
            pytest.param(8, [8, 5], 0, id="variant_specific_threshold"),
            pytest.param(18, [17, 17, 17], None, id="three_way_tie"),
            pytest.param(18, [18, 10, 8, 7, 5, 3, 2], 0, id="clear_winner_with_multiple_players"),
        ],
    )
    def test_check_for_solo_winner(
        self,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
        threshold,
        sc_counts,
        winner_index,
    ):
        game = game_factory(variant__solo_victory_sc_count=threshold)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        members = [member_factory(game=game) for _ in sc_counts]

        for member, count in zip(members, sc_counts):
            for _ in range(count):
                supply_center_factory(phase=phase, nation=member.nation)

        result = check_for_solo_winner(game, phase)

        if winner_index is None:
            assert result is None
        else:
            assert result == members[winner_index]

    def test_returns_none_when_variant_has_no_solo_victory_condition(
        self,
        game_factory,
        phase_factory,
        member_factory,
        supply_center_factory,
    ):
        game = game_factory()
        game.variant.victory_conditions = [{"type": "timed-resolution", "year": 1910, "resolution": "shared-draw"}]
        game.variant.save()

        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member = member_factory(game=game)
        for _ in range(30):
            supply_center_factory(phase=phase, nation=member.nation)

        assert check_for_solo_winner(game, phase) is None


class TestVictoryManager:

    def test_try_create_victory_creates_solo_victory(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=phase, nation=winner.nation)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=other_member.nation)

        victory = Victory.objects.try_create_victory(phase)

        assert victory is not None
        assert victory.game == game
        assert victory.winning_phase == phase
        assert victory.type == VictoryType.SOLO
        assert victory.members.count() == 1
        assert victory.members.first() == winner

    def test_try_create_victory_returns_none_when_no_winner(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        for _ in range(17):
            supply_center_factory(phase=phase, nation=member1.nation)

        for _ in range(10):
            supply_center_factory(phase=phase, nation=member2.nation)

        victory = Victory.objects.try_create_victory(phase)

        assert victory is None
        assert Victory.objects.count() == 0

    def test_try_create_victory_detects_solo_on_movement_phase(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        movement_phase = phase_factory(game=game, type=PhaseType.MOVEMENT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=movement_phase, nation=winner.nation)

        for _ in range(10):
            supply_center_factory(phase=movement_phase, nation=other_member.nation)

        victory = Victory.objects.try_create_victory(movement_phase)

        assert victory is not None
        assert victory.winning_phase == movement_phase
        assert victory.type == VictoryType.SOLO
        assert victory.members.count() == 1
        assert victory.members.first() == winner

    def test_try_create_victory_detects_solo_on_retreat_phase(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        retreat_phase = phase_factory(game=game, type=PhaseType.RETREAT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=retreat_phase, nation=winner.nation)

        for _ in range(10):
            supply_center_factory(phase=retreat_phase, nation=other_member.nation)

        victory = Victory.objects.try_create_victory(retreat_phase)

        assert victory is not None
        assert victory.winning_phase == retreat_phase
        assert victory.type == VictoryType.SOLO
        assert victory.members.count() == 1
        assert victory.members.first() == winner

    def test_try_create_victory_works_with_hundred_variant(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=9)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Year", year=1430)

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(9):
            supply_center_factory(phase=phase, nation=winner.nation)

        for _ in range(5):
            supply_center_factory(phase=phase, nation=other_member.nation)

        victory = Victory.objects.try_create_victory(phase)

        assert victory is not None
        assert victory.game == game
        assert victory.winning_phase == phase
        assert victory.type == VictoryType.SOLO
        assert victory.members.count() == 1
        assert victory.members.first() == winner

    def test_try_create_victory_idempotent(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=phase, nation=winner.nation)

        victory1 = Victory.objects.try_create_victory(phase)

        with pytest.raises(IntegrityError):
            victory2 = Victory.objects.try_create_victory(phase)

    def test_solo_and_draw_victories_querysets(self, victory_factory, member_factory):
        solo_victory = victory_factory()
        solo_victory.members.add(member_factory())

        draw_victory = victory_factory()
        draw_victory.members.add(member_factory(), member_factory())

        solo_victories = Victory.objects.solo_victories()

        assert solo_victories.count() == 1
        assert solo_victory in solo_victories
        assert draw_victory not in solo_victories

        draw_victories = Victory.objects.draw_victories()

        assert draw_victories.count() == 1
        assert draw_victory in draw_victories
        assert solo_victory not in draw_victories

    def test_draw_victories_with_various_member_counts(
        self, victory_factory, member_factory
    ):
        draw_2 = victory_factory()
        draw_2.members.add(member_factory(), member_factory())

        draw_3 = victory_factory()
        draw_3.members.add(member_factory(), member_factory(), member_factory())

        draw_4 = victory_factory()
        draw_4.members.add(
            member_factory(), member_factory(), member_factory(), member_factory()
        )

        draw_victories = Victory.objects.draw_victories()

        assert draw_victories.count() == 3
        assert draw_2 in draw_victories
        assert draw_3 in draw_victories
        assert draw_4 in draw_victories


class TestVictoryModel:

    @pytest.mark.parametrize(
        "member_count,expected_type",
        [
            pytest.param(1, VictoryType.SOLO, id="solo"),
            pytest.param(2, VictoryType.DRAW, id="draw"),
            pytest.param(3, VictoryType.DRAW, id="draw_three_members"),
        ],
    )
    def test_type_property(self, victory_factory, member_factory, member_count, expected_type):
        victory = victory_factory()
        victory.members.add(*[member_factory() for _ in range(member_count)])

        assert victory.type == expected_type

    def test_cascade_delete_when_game_deleted(self, game_factory, victory_factory):
        game = game_factory()
        victory = victory_factory(game=game)
        victory_id = victory.id

        game.delete()

        assert not Victory.objects.filter(id=victory_id).exists()

    def test_cascade_delete_when_phase_deleted(self, phase_factory, victory_factory):
        phase = phase_factory()
        victory = victory_factory(winning_phase=phase)
        victory_id = victory.id

        phase.delete()

        assert not Victory.objects.filter(id=victory_id).exists()

    def test_one_to_one_constraint_enforced(
        self, game_factory, phase_factory, member_factory
    ):
        game = game_factory()
        phase = phase_factory(game=game)
        member = member_factory(game=game)

        victory1 = Victory.objects.create(game=game, winning_phase=phase)
        victory1.members.add(member)

        with pytest.raises(IntegrityError):
            victory2 = Victory.objects.create(game=game, winning_phase=phase)


class TestVictorySerializer:

    def test_serializes_solo_victory(self, victory_factory, member_factory, primary_user):
        victory = victory_factory()
        member = member_factory(user=primary_user)
        victory.members.add(member)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = primary_user

        serializer = VictorySerializer(victory, context={'request': request})
        data = serializer.data

        assert data['type'] == VictoryType.SOLO
        assert data['id'] == victory.id
        assert data['winning_phase_id'] == victory.winning_phase.id
        assert len(data['members']) == 1
        assert data['members'][0]['id'] == member.id
        assert 'id' in data
        assert 'type' in data
        assert 'winning_phase_id' in data
        assert 'members' in data
        assert isinstance(data['members'], list)

    def test_serializes_draw_victory(self, victory_factory, member_factory, primary_user, secondary_user, tertiary_user):
        victory = victory_factory()
        member1 = member_factory(user=primary_user)
        member2 = member_factory(user=secondary_user)
        member3 = member_factory(user=tertiary_user)
        victory.members.add(member1, member2, member3)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = primary_user

        serializer = VictorySerializer(victory, context={'request': request})
        data = serializer.data

        assert data['type'] == VictoryType.DRAW
        assert data['id'] == victory.id
        assert data['winning_phase_id'] == victory.winning_phase.id
        assert len(data['members']) == 3

        member_ids = [m['id'] for m in data['members']]
        assert member1.id in member_ids
        assert member2.id in member_ids
        assert member3.id in member_ids

