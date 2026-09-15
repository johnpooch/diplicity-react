import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import override_settings

from adjudicator import service as adjudication_service
from common.constants import GameStatus
from game.utils import assign_nations
from member.models import Member


def fake_nation(nation_id):
    return SimpleNamespace(id=nation_id)


def fake_member(member_id, preferences=(), nation=None):
    return SimpleNamespace(
        id=member_id,
        nation=nation,
        nation_id=nation.id if nation else None,
        nation_preferences=SimpleNamespace(
            all=lambda: [SimpleNamespace(nation_id=nation_id) for nation_id in preferences]
        ),
    )


class TestAssignNations:

    def test_distinct_top_preferences_assigned(self):
        nations = [fake_nation(n) for n in ["austria", "england", "france"]]
        members = [
            fake_member(1, preferences=["england"]),
            fake_member(2, preferences=["france"]),
            fake_member(3, preferences=["austria"]),
        ]
        for seed in range(10):
            result = assign_nations(seed, members, nations)
            assert result[1].id == "england"
            assert result[2].id == "france"
            assert result[3].id == "austria"

    def test_contested_nation_goes_to_earlier_member_in_priority_order(self):
        nations = [fake_nation(n) for n in ["england", "france"]]
        members = [
            fake_member(1, preferences=["england", "france"]),
            fake_member(2, preferences=["england", "france"]),
        ]
        seed = 7
        priority = list(members)
        random.Random(seed).shuffle(priority)
        result = assign_nations(seed, members, nations)
        assert result[priority[0].id].id == "england"
        assert result[priority[1].id].id == "france"

    def test_member_with_fully_taken_list_gets_remainder(self):
        nations = [fake_nation(n) for n in ["england", "france", "germany"]]
        members = [
            fake_member(1, nation=fake_nation("england")),
            fake_member(2, nation=fake_nation("france")),
            fake_member(3, preferences=["england", "france"]),
        ]
        result = assign_nations(1, members, nations)
        assert result[3].id == "germany"

    def test_empty_preference_list_falls_back_to_random(self):
        nations = [fake_nation(n) for n in ["england", "france", "germany"]]
        members = [fake_member(1), fake_member(2), fake_member(3)]
        result = assign_nations(1, members, nations)
        assert {n.id for n in result.values()} == {"england", "france", "germany"}

    def test_same_seed_gives_same_result(self):
        nations = [fake_nation(n) for n in ["austria", "england", "france", "germany"]]
        members = [fake_member(i, preferences=["england"]) for i in range(1, 5)]
        first = assign_nations(42, members, nations)
        second = assign_nations(42, members, nations)
        assert {m: n.id for m, n in first.items()} == {m: n.id for m, n in second.items()}

    def test_pinned_nation_honoured_and_removed_from_pool(self):
        nations = [fake_nation(n) for n in ["england", "france"]]
        members = [
            fake_member(1, nation=fake_nation("england")),
            fake_member(2, preferences=["england"]),
        ]
        result = assign_nations(1, members, nations)
        assert result[1].id == "england"
        assert result[2].id == "france"

    def test_pinned_member_preferences_ignored(self):
        nations = [fake_nation(n) for n in ["england", "france"]]
        members = [
            fake_member(1, preferences=["france"], nation=fake_nation("england")),
            fake_member(2),
        ]
        result = assign_nations(1, members, nations)
        assert result[1].id == "england"
        assert result[2].id == "france"


class TestGameStartAssignment:

    def _fill_game(self, game, user_factory, count=7):
        return [game.members.create(user=user_factory()) for _ in range(count)]

    @pytest.mark.django_db
    def test_pinning_six_of_seven_forces_the_seventh(
        self, pending_game_with_game_master_factory, user_factory, adjudication_data_classical
    ):
        game = pending_game_with_game_master_factory()
        members = self._fill_game(game, user_factory)
        nations = list(game.variant.nations.all())
        for member, nation in zip(members[:6], nations[:6]):
            Member.objects.assign_nation(member, nation)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        last = game.members.get(id=members[6].id)
        assert last.nation == nations[6]

    @pytest.mark.django_db
    def test_preferences_applied_on_start(
        self, pending_game_with_game_master_factory, user_factory, adjudication_data_classical
    ):
        game = pending_game_with_game_master_factory()
        members = self._fill_game(game, user_factory)
        nations = {n.nation_id: n for n in game.variant.nations.all()}
        Member.objects.set_nation_preferences(members[0], [nations["turkey"]])
        for member, nation_id in zip(members[1:], ["austria", "england", "france", "germany", "italy", "russia"]):
            Member.objects.assign_nation(member, nations[nation_id])

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        first = game.members.get(id=members[0].id)
        assert first.nation == nations["turkey"]

    @pytest.mark.django_db
    def test_preference_rows_kept_after_start(
        self, pending_game_with_game_master_factory, user_factory, adjudication_data_classical
    ):
        game = pending_game_with_game_master_factory()
        members = self._fill_game(game, user_factory)
        nations = list(game.variant.nations.all())
        Member.objects.set_nation_preferences(members[0], nations[:3])

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        assert members[0].nation_preferences.count() == 3

    @pytest.mark.django_db
    def test_start_query_count_with_preferences(
        self, pending_game_with_game_master_factory, user_factory, adjudication_data_classical
    ):
        game = pending_game_with_game_master_factory()
        members = self._fill_game(game, user_factory)
        nations = list(game.variant.nations.all())
        for member in members:
            Member.objects.set_nation_preferences(member, nations[:2])

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
                game.start()
        query_count = len(connection.queries)
        assert query_count == 19
