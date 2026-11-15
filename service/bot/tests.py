import ast
import importlib
import random
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib.auth.models import User

from bot.constants import BotKind
from bot.core.constants import BASIC_BOT_REPLY, OrderType, ResponseMode
from bot.core.basic import BasicBot, BasicSelector
from bot.core.exceptions import BotCoreError
from bot.models import Bot
from common.constants import UserKind
from dumbbot.policy import select_orders as dumbbot_select_orders
from harness.adapter import fixture_to_context
from member.models import Member
from user_profile.models import UserProfile

seed_bots_migration = importlib.import_module("bot.migrations.0002_seed_bots")

CORE_DIR = Path(__file__).parent / "core"


class TestSeedBots:

    @pytest.mark.django_db
    def test_seeds_forty_numbered_automatons(self):
        names = set(
            Bot.objects.filter(kind=BotKind.BASIC).values_list("name", flat=True)
        )

        assert len(names) == 40
        assert {"Automaton I", "Automaton IX", "Automaton XIV", "Automaton XL"} <= names

    @pytest.mark.django_db
    def test_automaton_bot_name_matches_its_profile(self):
        bot = Bot.objects.get(name="Automaton XXXIX")

        assert bot.user.profile.name == "Automaton XXXIX"
        assert bot.user.profile.kind == UserKind.DUMBBOT
        assert bot.user.email == "automaton_xxxix@bots.diplicity.com"

    @pytest.mark.django_db
    def test_llm_profiles_become_ai_bots(self):
        llm_user_ids = set(
            UserProfile.objects.filter(kind=UserKind.LLM).values_list(
                "user_id", flat=True
            )
        )

        assert llm_user_ids
        assert (
            set(Bot.objects.filter(kind=BotKind.AI).values_list("user_id", flat=True))
            == llm_user_ids
        )

    @pytest.mark.django_db
    def test_creates_bot_rows_for_existing_bot_profiles(self, user_factory):
        user = user_factory(name="Legacy Bot")
        UserProfile.objects.filter(user=user).update(kind=UserKind.DUMBBOT)

        seed_bots_migration.seed_bots(apps, None)

        bot = Bot.objects.get(user=user)
        assert bot.kind == BotKind.BASIC
        assert bot.name == "Legacy Bot"

    @pytest.mark.django_db
    def test_is_idempotent(self):
        bot_count = Bot.objects.count()
        user_count = User.objects.count()

        seed_bots_migration.seed_bots(apps, None)

        assert Bot.objects.count() == bot_count
        assert User.objects.count() == user_count

    @pytest.mark.django_db
    def test_skips_human_profiles(self, primary_user):
        seed_bots_migration.seed_bots(apps, None)

        assert not Bot.objects.filter(user=primary_user).exists()


class TestIsBot:

    @pytest.mark.django_db
    def test_user_with_bot_row_is_bot(self, user_factory):
        user = user_factory()
        Bot.objects.create(user=user, kind=BotKind.BASIC, name="Test Bot")
        user = User.objects.get(id=user.id)

        assert user.profile.is_bot is True

    @pytest.mark.django_db
    def test_user_with_bot_profile_kind_and_no_bot_row_is_not_bot(self, user_factory):
        user = user_factory()
        UserProfile.objects.filter(user=user).update(kind=UserKind.DUMBBOT)
        user = User.objects.get(id=user.id)

        assert user.profile.is_bot is False

    @pytest.mark.django_db
    def test_member_of_bot_user_is_bot(
        self, pending_game_created_by_primary_user, bot_user, primary_user
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=bot_user)

        members = {member.user_id: member for member in game.members.all()}

        assert members[bot_user.id].is_bot is True
        assert members[primary_user.id].is_bot is False

    @pytest.mark.django_db
    def test_humans_excludes_bot_members(
        self, pending_game_created_by_primary_user, bot_user, primary_user
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=bot_user)

        assert list(
            Member.objects.filter(game=game).humans().values_list("user_id", flat=True)
        ) == [primary_user.id]

    @pytest.mark.django_db
    def test_addable_to_game_lists_bots_not_in_the_game(
        self, pending_game_created_by_primary_user, bot_user, user_factory
    ):
        game = pending_game_created_by_primary_user
        game.members.create(user=bot_user)
        fake_bot = user_factory()
        UserProfile.objects.filter(user=fake_bot).update(kind=UserKind.LLM)

        addable_user_ids = set(
            UserProfile.objects.addable_to_game(game).values_list("user_id", flat=True)
        )

        assert addable_user_ids == set(
            Bot.objects.exclude(user=bot_user).values_list("user_id", flat=True)
        )


def _movement_fixture(**overrides):
    fixture = {
        "id": "movement",
        "variant": "classical",
        "nation": "England",
        "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
        "units": [
            {"type": "Fleet", "nation": "England", "province": "lon"},
            {"type": "Fleet", "nation": "England", "province": "edi"},
            {"type": "Army", "nation": "England", "province": "lvp"},
        ],
        "supply_centers": [
            {"nation": "England", "province": "lon"},
            {"nation": "England", "province": "edi"},
            {"nation": "England", "province": "lvp"},
            {"nation": "France", "province": "par"},
            {"nation": "France", "province": "bre"},
            {"nation": "France", "province": "mar"},
        ],
        "order_options": [
            {"source": "lon", "order_type": "Hold"},
            {"source": "lon", "order_type": "Move", "target": "nth"},
            {"source": "lon", "order_type": "Move", "target": "eng"},
            {"source": "edi", "order_type": "Hold"},
            {"source": "edi", "order_type": "Move", "target": "nth"},
            {"source": "edi", "order_type": "Move", "target": "nrg"},
            {"source": "lvp", "order_type": "Hold"},
            {"source": "lvp", "order_type": "Move", "target": "yor"},
            {"source": "lvp", "order_type": "Move", "target": "wal"},
        ],
    }
    fixture.update(overrides)
    return fixture


class TestBasicOrders:

    def test_returns_options_by_identity(self):
        context = fixture_to_context(_movement_fixture())
        orders = BasicBot(random.Random(1)).choose_orders(context)

        option_ids = {id(option) for option in context["order_options"]}
        assert orders
        assert all(id(order) in option_ids for order in orders)

    def test_at_most_one_order_per_source_and_full_coverage(self):
        context = fixture_to_context(_movement_fixture())
        orders = BasicBot(random.Random(1)).choose_orders(context)

        sources = [order["source"] for order in orders]
        assert sorted(sources) == ["edi", "lon", "lvp"]

    def test_seeded_rng_is_deterministic(self):
        context = fixture_to_context(_movement_fixture())
        first = BasicBot(random.Random(42)).choose_orders(context)
        second = BasicBot(random.Random(42)).choose_orders(context)

        assert first == second

    def test_moves_toward_fat_undefended_enemy_center(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1901, "type": "Movement"},
            units=[{"type": "Army", "nation": "England", "province": "pic"}],
            order_options=[
                {"source": "pic", "order_type": "Hold"},
                {"source": "pic", "order_type": "Move", "target": "par"},
                {"source": "pic", "order_type": "Move", "target": "bur"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(random.Random(1)).choose_orders(context)

        assert orders == [
            {
                "source": "pic",
                "order_type": OrderType.MOVE,
                "target": "par",
                "aux": None,
                "unit_type": None,
                "named_coast": None,
            }
        ]

    def test_never_moves_to_a_province_that_needs_a_convoy(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1901, "type": "Movement"},
            nation="Turkey",
            units=[
                {"type": "Army", "nation": "Turkey", "province": "ank"},
                {"type": "Fleet", "nation": "Turkey", "province": "bla"},
            ],
            supply_centers=[
                {"nation": "Turkey", "province": "ank"},
                {"nation": "Russia", "province": "sev"},
                {"nation": "Russia", "province": "mos"},
                {"nation": "Russia", "province": "war"},
                {"nation": "Russia", "province": "stp"},
            ],
            order_options=[
                {"source": "ank", "order_type": "Hold"},
                {"source": "ank", "order_type": "Move", "target": "con"},
                {"source": "ank", "order_type": "Move", "target": "arm"},
                {"source": "ank", "order_type": "Move", "target": "sev"},
                {"source": "ank", "order_type": "MoveViaConvoy", "target": "sev"},
                {"source": "bla", "order_type": "Hold"},
                {"source": "bla", "order_type": "Move", "target": "rum"},
                {
                    "source": "bla",
                    "order_type": "Convoy",
                    "aux": "ank",
                    "target": "sev",
                },
            ],
        )
        context = fixture_to_context(fixture)

        for seed in range(20):
            orders = BasicBot(random.Random(seed)).choose_orders(context)

            army_order = next(order for order in orders if order["source"] == "ank")
            assert army_order["order_type"] != OrderType.MOVE_VIA_CONVOY
            assert army_order["target"] != "sev"

    def test_empty_adjacencies_still_covers_every_source(self):
        context = fixture_to_context(_movement_fixture())
        for province in context["provinces"]:
            province["adjacencies"] = []

        orders = BasicBot(random.Random(1)).choose_orders(context)

        assert sorted(order["source"] for order in orders) == ["edi", "lon", "lvp"]

    def test_fleet_move_to_multi_coast_province_keeps_named_coast(self):
        fixture = _movement_fixture(
            units=[{"type": "Fleet", "nation": "England", "province": "mid"}],
            supply_centers=[
                {"nation": "France", "province": "spa"},
                {"nation": "France", "province": "par"},
                {"nation": "France", "province": "mar"},
            ],
            order_options=[
                {"source": "mid", "order_type": "Hold"},
                {
                    "source": "mid",
                    "order_type": "Move",
                    "target": "spa",
                    "named_coast": "spa/nc",
                },
                {
                    "source": "mid",
                    "order_type": "Move",
                    "target": "spa",
                    "named_coast": "spa/sc",
                },
                {"source": "mid", "order_type": "Move", "target": "nat"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(random.Random(1)).choose_orders(context)

        assert len(orders) == 1
        assert orders[0]["target"] == "spa"
        assert orders[0]["named_coast"] in ("spa/nc", "spa/sc")

    def test_retreat_options_presented_as_moves_are_handled(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1902, "type": "Retreat"},
            nation="Austria",
            units=[
                {
                    "type": "Army",
                    "nation": "Austria",
                    "province": "tri",
                    "dislodged": True,
                },
                {"type": "Army", "nation": "Italy", "province": "tri"},
            ],
            supply_centers=[
                {"nation": "Italy", "province": "tri"},
            ],
            order_options=[
                {"source": "tri", "order_type": "Move", "target": "ser"},
                {"source": "tri", "order_type": "Move", "target": "alb"},
                {"source": "tri", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(random.Random(1)).choose_orders(context)

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.MOVE
        assert orders[0]["target"] == "ser"

    def test_retreat_disbands_when_every_destination_is_occupied(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1902, "type": "Retreat"},
            nation="Austria",
            units=[
                {
                    "type": "Army",
                    "nation": "Austria",
                    "province": "tri",
                    "dislodged": True,
                },
                {"type": "Army", "nation": "Italy", "province": "tri"},
                {"type": "Army", "nation": "Italy", "province": "ser"},
                {"type": "Army", "nation": "Italy", "province": "alb"},
            ],
            supply_centers=[],
            order_options=[
                {"source": "tri", "order_type": "Move", "target": "ser"},
                {"source": "tri", "order_type": "Move", "target": "alb"},
                {"source": "tri", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        orders = BasicBot(random.Random(1)).choose_orders(context)

        assert [order["order_type"] for order in orders] == [OrderType.DISBAND]

    def test_builds_respect_max_orders(self):
        fixture = _movement_fixture(
            phase={"season": "Winter", "year": 1901, "type": "Adjustment"},
            nation="Russia",
            max_orders=1,
            units=[
                {"type": "Army", "nation": "Russia", "province": "mos"},
            ],
            supply_centers=[
                {"nation": "Russia", "province": "mos"},
                {"nation": "Russia", "province": "war"},
                {"nation": "Russia", "province": "sev"},
            ],
            order_options=[
                {"source": "sev", "order_type": "Build", "unit_type": "Army"},
                {"source": "war", "order_type": "Build", "unit_type": "Army"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(random.Random(1)).choose_orders(context)

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.BUILD
        assert orders[0]["source"] == "sev"

    def test_disbands_least_valuable_unit_up_to_max_orders(self):
        fixture = _movement_fixture(
            phase={"season": "Winter", "year": 1902, "type": "Adjustment"},
            max_orders=1,
            units=[
                {"type": "Army", "nation": "England", "province": "bur"},
                {"type": "Army", "nation": "England", "province": "wal"},
            ],
            supply_centers=[
                {"nation": "England", "province": "lon"},
                {"nation": "France", "province": "par"},
                {"nation": "France", "province": "mar"},
                {"nation": "France", "province": "bre"},
            ],
            order_options=[
                {"source": "bur", "order_type": "Disband"},
                {"source": "wal", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(random.Random(1)).choose_orders(context)

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.DISBAND
        assert orders[0]["source"] == "wal"

    def test_raises_when_current_nation_missing(self):
        context = fixture_to_context(_movement_fixture())
        for member in context["members"]:
            member["is_current_user"] = False

        with pytest.raises(BotCoreError):
            BasicBot(random.Random(1)).choose_orders(context)

    def test_empty_options_return_no_orders(self):
        context = fixture_to_context(_movement_fixture(order_options=[]))

        assert BasicBot(random.Random(1)).choose_orders(context) == []

    @pytest.mark.parametrize(
        "overrides",
        [
            {},
            {"phase": {"season": "Fall", "year": 1901, "type": "Movement"}},
            {
                "phase": {"season": "Fall", "year": 1902, "type": "Retreat"},
                "nation": "Austria",
                "units": [
                    {
                        "type": "Army",
                        "nation": "Austria",
                        "province": "tri",
                        "dislodged": True,
                    },
                    {"type": "Army", "nation": "Italy", "province": "tri"},
                ],
                "supply_centers": [{"nation": "Italy", "province": "tri"}],
                "order_options": [
                    {"source": "tri", "order_type": "Move", "target": "ser"},
                    {"source": "tri", "order_type": "Move", "target": "alb"},
                    {"source": "tri", "order_type": "Disband"},
                ],
            },
            {
                "phase": {"season": "Winter", "year": 1901, "type": "Adjustment"},
                "nation": "Russia",
                "max_orders": 2,
                "units": [{"type": "Army", "nation": "Russia", "province": "mos"}],
                "supply_centers": [
                    {"nation": "Russia", "province": "mos"},
                    {"nation": "Russia", "province": "war"},
                    {"nation": "Russia", "province": "sev"},
                ],
                "order_options": [
                    {"source": "sev", "order_type": "Build", "unit_type": "Army"},
                    {"source": "war", "order_type": "Build", "unit_type": "Army"},
                    {"source": "war", "order_type": "Build", "unit_type": "Fleet"},
                ],
            },
            {
                "phase": {"season": "Winter", "year": 1902, "type": "Adjustment"},
                "max_orders": 1,
                "units": [
                    {"type": "Army", "nation": "England", "province": "bur"},
                    {"type": "Army", "nation": "England", "province": "wal"},
                ],
                "order_options": [
                    {"source": "bur", "order_type": "Disband"},
                    {"source": "wal", "order_type": "Disband"},
                ],
            },
        ],
    )
    def test_matches_dumbbot_app(self, overrides):
        context = fixture_to_context(_movement_fixture(**overrides))

        for seed in range(20):
            assert BasicBot(random.Random(seed)).choose_orders(
                context
            ) == dumbbot_select_orders(context, rng=random.Random(seed))


def _channel(*sender_ids):
    return {
        "id": 1,
        "messages": [
            {"sender_id": sender_id, "body": "Hello"} for sender_id in sender_ids
        ],
    }


def _phase():
    return {"season": "Spring", "year": 1901, "type": "Movement"}


class TestBasicDraw:

    def test_accepts_every_draw(self):
        bot = BasicBot(random.Random(1))

        assert (
            bot.decide_draw(
                {"member_id": 1, "phase": _phase(), "nations": ["England", "France"]}
            )
            is True
        )


class TestBasicResponses:

    def test_response_says_it_cannot_chat(self):
        bot = BasicBot(random.Random(1))

        assert (
            bot.respond(
                {
                    "member_id": 1,
                    "channel": _channel(2),
                    "phase": _phase(),
                    "provinces": [],
                    "units": [],
                    "supply_centers": [],
                }
            )
            == BASIC_BOT_REPLY
        )

    def test_light_response_says_it_cannot_chat(self):
        bot = BasicBot(random.Random(1))

        assert (
            bot.respond_lightly({"member_id": 1, "channel": _channel(2)})
            == BASIC_BOT_REPLY
        )

    def test_writes_no_journal_entry(self):
        bot = BasicBot(random.Random(1))

        assert bot.write_journal_entry({"member_id": 1, "phase": _phase()}) is None

    def test_plans_no_conversations(self):
        bot = BasicBot(random.Random(1))

        assert (
            bot.plan({"member_id": 1, "phase": _phase(), "channels": [_channel(2)]})
            == []
        )


class TestBasicSelector:

    def test_selects_bot_that_has_not_posted_with_light_response(self):
        selection = BasicSelector().select({"channel": _channel(1), "candidates": [5]})

        assert selection == {"member_id": 5, "mode": ResponseMode.LIGHT}

    def test_skips_bot_that_has_posted(self):
        selection = BasicSelector().select(
            {"channel": _channel(1, 5), "candidates": [5, 6]}
        )

        assert selection == {"member_id": 6, "mode": ResponseMode.LIGHT}

    def test_selects_next_bot_after_first_bot_replies(self):
        selector = BasicSelector()

        first = selector.select({"channel": _channel(1), "candidates": [5, 6]})
        second = selector.select({"channel": _channel(1, 5), "candidates": [5, 6]})

        assert first["member_id"] == 5
        assert second["member_id"] == 6

    def test_selects_no_one_once_every_bot_has_posted(self):
        selection = BasicSelector().select(
            {"channel": _channel(1, 5, 6), "candidates": [5, 6]}
        )

        assert selection is None

    def test_selects_no_one_without_candidates(self):
        selection = BasicSelector().select({"channel": _channel(1), "candidates": []})

        assert selection is None

    def test_human_messages_do_not_count_as_bot_replies(self):
        selection = BasicSelector().select(
            {"channel": _channel(1, 2, 3), "candidates": [5]}
        )

        assert selection == {"member_id": 5, "mode": ResponseMode.LIGHT}


def _core_imports():
    for path in CORE_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield path, alias.name
            elif isinstance(node, ast.ImportFrom):
                yield path, "." * node.level + (node.module or "")


class TestCoreBoundary:

    def test_core_imports_only_the_standard_library_and_itself(self):
        violations = sorted(
            f"{path.relative_to(CORE_DIR)}: {module}"
            for path, module in _core_imports()
            if module.split(".")[0] not in sys.stdlib_module_names
            and module != "bot.core"
            and not module.startswith("bot.core.")
        )

        assert violations == []
