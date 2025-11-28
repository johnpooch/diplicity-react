import pytest
from django.db import IntegrityError
from rest_framework.test import APIRequestFactory
from common.constants import PhaseType, PhaseStatus, GameStatus
from victory.models import Victory
from victory.utils import check_for_solo_winner
from victory.constants import VictoryType
from victory.serializers import VictorySerializer


class TestCheckForSoloWinner:

    def test_clear_solo_winner_at_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=phase, nation=winner.nation)

        for _ in range(16):
            supply_center_factory(phase=phase, nation=other_member.nation)

        result = check_for_solo_winner(game, phase)

        assert result == winner

    def test_solo_winner_above_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(20):
            supply_center_factory(phase=phase, nation=winner.nation)

        for _ in range(14):
            supply_center_factory(phase=phase, nation=other_member.nation)

        result = check_for_solo_winner(game, phase)

        assert result == winner

    def test_no_winner_below_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        for _ in range(17):
            supply_center_factory(phase=phase, nation=member1.nation)

        for _ in range(16):
            supply_center_factory(phase=phase, nation=member2.nation)

        result = check_for_solo_winner(game, phase)

        assert result is None

    def test_no_winner_when_tied_at_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=phase, nation=member1.nation)

        for _ in range(18):
            supply_center_factory(phase=phase, nation=member2.nation)

        result = check_for_solo_winner(game, phase)

        assert result is None

    def test_no_winner_when_tied_above_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member1 = member_factory(game=game)
        member2 = member_factory(game=game)

        for _ in range(19):
            supply_center_factory(phase=phase, nation=member1.nation)

        for _ in range(19):
            supply_center_factory(phase=phase, nation=member2.nation)

        result = check_for_solo_winner(game, phase)

        assert result is None

    def test_variant_specific_threshold(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=8)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)
        other_member = member_factory(game=game)

        for _ in range(8):
            supply_center_factory(phase=phase, nation=winner.nation)

        for _ in range(5):
            supply_center_factory(phase=phase, nation=other_member.nation)

        result = check_for_solo_winner(game, phase)

        assert result == winner

    def test_three_way_tie(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        member1 = member_factory(game=game)
        member2 = member_factory(game=game)
        member3 = member_factory(game=game)

        for _ in range(17):
            supply_center_factory(phase=phase, nation=member1.nation)

        for _ in range(17):
            supply_center_factory(phase=phase, nation=member2.nation)

        for _ in range(17):
            supply_center_factory(phase=phase, nation=member3.nation)

        result = check_for_solo_winner(game, phase)

        assert result is None

    def test_clear_winner_with_multiple_players(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)
        phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Fall")

        winner = member_factory(game=game)
        members = [member_factory(game=game) for _ in range(6)]

        for _ in range(18):
            supply_center_factory(phase=phase, nation=winner.nation)

        sc_counts = [10, 8, 7, 5, 3, 2]
        for member, count in zip(members, sc_counts):
            for _ in range(count):
                supply_center_factory(phase=phase, nation=member.nation)

        result = check_for_solo_winner(game, phase)

        assert result == winner


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

    def test_try_create_victory_only_checks_fall_adjustment(
        self, game_factory, phase_factory, member_factory, supply_center_factory
    ):
        game = game_factory(variant__solo_victory_sc_count=18)

        spring_phase = phase_factory(game=game, type=PhaseType.ADJUSTMENT, season="Spring")
        winner = member_factory(game=game)

        for _ in range(18):
            supply_center_factory(phase=spring_phase, nation=winner.nation)

        victory = Victory.objects.try_create_victory(spring_phase)
        assert victory is None

        movement_phase = phase_factory(game=game, type=PhaseType.MOVEMENT, season="Fall")

        for _ in range(18):
            supply_center_factory(phase=movement_phase, nation=winner.nation)

        victory = Victory.objects.try_create_victory(movement_phase)
        assert victory is None

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

    def test_solo_victories_queryset(self, victory_factory, member_factory):
        solo_victory = victory_factory()
        solo_victory.members.add(member_factory())

        draw_victory = victory_factory()
        draw_victory.members.add(member_factory(), member_factory())

        solo_victories = Victory.objects.solo_victories()

        assert solo_victories.count() == 1
        assert solo_victory in solo_victories
        assert draw_victory not in solo_victories

    def test_draw_victories_queryset(self, victory_factory, member_factory):
        solo_victory = victory_factory()
        solo_victory.members.add(member_factory())

        draw_victory = victory_factory()
        draw_victory.members.add(member_factory(), member_factory())

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

    def test_type_property_solo(self, victory_factory, member_factory):
        victory = victory_factory()
        victory.members.add(member_factory())

        assert victory.type == VictoryType.SOLO

    def test_type_property_draw(self, victory_factory, member_factory):
        victory = victory_factory()
        victory.members.add(member_factory(), member_factory())

        assert victory.type == VictoryType.DRAW

    def test_type_property_draw_three_members(self, victory_factory, member_factory):
        victory = victory_factory()
        victory.members.add(member_factory(), member_factory(), member_factory())

        assert victory.type == VictoryType.DRAW

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

    def test_includes_all_required_fields(self, victory_factory, member_factory, primary_user):
        victory = victory_factory()
        member = member_factory(user=primary_user)
        victory.members.add(member)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = primary_user

        serializer = VictorySerializer(victory, context={'request': request})
        data = serializer.data

        assert 'id' in data
        assert 'type' in data
        assert 'winning_phase_id' in data
        assert 'members' in data
        assert isinstance(data['members'], list)
