import ast
import importlib
import random
import sys
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from django.apps import apps
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status

from bot.constants import BotKind, RunStatus, RunStep
from bot.core.constants import (
    BASIC_BOT_JOURNAL_ENTRY,
    BASIC_BOT_REPLY,
    OrderType,
    ResponseMode,
)
from bot.core.basic import BasicBot, BasicSelector
from bot.core.exceptions import BotCoreError
from channel.models import Channel, ChannelMember, ChannelMessage
from bot.context import BotContextBuilder
from bot.coordinator import Coordinator
from bot.models import Bot, Run
from bot.steps import DrawDecisionStep
from bot.tasks import coordinate, decide_draw
from common.constants import GameStatus, UserKind
from draw_proposal.constants import DrawProposalStatus
from draw_proposal.models import DrawProposal
from dumbbot.policy import select_orders as dumbbot_select_orders
from harness.adapter import fixture_to_context
from member.models import Member
from user_profile.models import UserProfile
from victory.models import Victory

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


def _context(fixture):
    return {**fixture_to_context(fixture), "member_id": 1, "nations": []}


class TestBasicOrders:

    def test_returns_options_by_identity(self):
        context = _context(_movement_fixture())
        orders = BasicBot(context, random.Random(1)).select_orders()

        option_ids = {id(option) for option in context["order_options"]}
        assert orders
        assert all(id(order) in option_ids for order in orders)

    def test_at_most_one_order_per_source_and_full_coverage(self):
        context = _context(_movement_fixture())
        orders = BasicBot(context, random.Random(1)).select_orders()

        sources = [order["source"] for order in orders]
        assert sorted(sources) == ["edi", "lon", "lvp"]

    def test_seeded_rng_is_deterministic(self):
        context = _context(_movement_fixture())
        first = BasicBot(context, random.Random(42)).select_orders()
        second = BasicBot(context, random.Random(42)).select_orders()

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
        context = _context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        for seed in range(20):
            orders = BasicBot(context, random.Random(seed)).select_orders()

            army_order = next(order for order in orders if order["source"] == "ank")
            assert army_order["order_type"] != OrderType.MOVE_VIA_CONVOY
            assert army_order["target"] != "sev"

    def test_empty_adjacencies_still_covers_every_source(self):
        context = _context(_movement_fixture())
        for province in context["provinces"]:
            province["adjacencies"] = []

        orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(context, random.Random(1)).select_orders()

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
        context = _context(fixture)

        with patch("bot.core.dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = BasicBot(context, random.Random(1)).select_orders()

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.DISBAND
        assert orders[0]["source"] == "wal"

    def test_raises_when_current_nation_missing(self):
        context = _context(_movement_fixture())
        for member in context["members"]:
            member["is_current_user"] = False

        with pytest.raises(BotCoreError):
            BasicBot(context, random.Random(1)).select_orders()

    def test_empty_options_return_no_orders(self):
        context = _context(_movement_fixture(order_options=[]))

        assert BasicBot(context, random.Random(1)).select_orders() == []

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
        context = _context(_movement_fixture(**overrides))

        for seed in range(20):
            assert BasicBot(
                context, random.Random(seed)
            ).select_orders() == dumbbot_select_orders(context, rng=random.Random(seed))


def _channel(*sender_ids):
    return {
        "id": 1,
        "messages": [
            {"sender_id": sender_id, "body": "Hello"} for sender_id in sender_ids
        ],
    }


def _bot():
    context = _context(_movement_fixture())
    context["channels"] = [_channel(2)]
    context["nations"] = ["England", "France"]
    return BasicBot(context, random.Random(1))


class TestBasicDraw:

    def test_accepts_every_draw(self):
        assert _bot().decide_draw() is True


class TestBasicResponses:

    def test_full_response_says_it_cannot_chat(self):
        assert _bot().respond(1, ResponseMode.FULL) == BASIC_BOT_REPLY

    def test_light_response_says_it_cannot_chat(self):
        assert _bot().respond(1, ResponseMode.LIGHT) == BASIC_BOT_REPLY

    def test_writes_placeholder_journal_entry(self):
        assert _bot().write_journal_entry() == BASIC_BOT_JOURNAL_ENTRY

    def test_plans_no_conversations(self):
        assert _bot().plan() == []


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


def _make_bot(member):
    return Bot.objects.create(
        user=member.user, kind=BotKind.BASIC, name=f"Test Bot {member.pk}"
    )


def _jobs(connector, task_name):
    return [job for job in connector.jobs.values() if job["task_name"] == task_name]


def _draw_run(member, proposal, **kwargs):
    return Run.objects.create(
        step=RunStep.DRAW_DECISION,
        bot=member.user.bot,
        member=member,
        phase=proposal.phase,
        draw_proposal=proposal,
        **kwargs,
    )


class TestBotContextBuilder:

    @pytest.mark.django_db
    def test_builds_what_the_bot_can_see(self, active_game_factory, primary_user):
        game = active_game_factory()
        human = game.members.get(user=primary_user)
        bot_member = game.members.exclude(user=primary_user).first()
        _make_bot(bot_member)
        channel = Channel.objects.create(game=game, name="Public Press", private=False)
        ChannelMember.objects.create(member=human, channel=channel)
        ChannelMember.objects.create(member=bot_member, channel=channel)
        ChannelMessage.objects.create(channel=channel, sender=human, body="Draw?")

        context = BotContextBuilder(bot_member).build()

        assert context["member_id"] == bot_member.id
        assert len(context["nations"]) == 7
        assert [
            member["nation"]
            for member in context["members"]
            if member["is_current_user"]
        ] == [bot_member.nation.name]
        assert context["phase"]["type"] == "Movement"
        assert context["units"]
        assert context["order_options"]
        assert context["channels"] == [
            {"id": channel.id, "messages": [{"sender_id": human.id, "body": "Draw?"}]}
        ]


class TestDrawDecisionRuns:

    def _propose(self, authenticated_client, game, capture):
        with capture(execute=True):
            response = authenticated_client.post(
                f"/games/{game.id}/draw-proposals/create/", {}, format="json"
            )
        assert response.status_code == status.HTTP_201_CREATED
        return DrawProposal.objects.get(game=game)

    @pytest.mark.django_db
    def test_bot_accepts_a_draw_proposed_by_a_player(
        self,
        active_game_factory,
        authenticated_client,
        primary_user,
        in_memory_procrastinate,
        django_capture_on_commit_callbacks,
    ):
        game = active_game_factory()
        bot_member = game.members.exclude(user=primary_user).first()
        _make_bot(bot_member)

        proposal = self._propose(
            authenticated_client, game, django_capture_on_commit_callbacks
        )

        run = Run.objects.get()
        assert run.step == RunStep.DRAW_DECISION
        assert run.status == RunStatus.PENDING
        assert run.member == bot_member
        assert run.draw_proposal == proposal
        assert len(_jobs(in_memory_procrastinate, "bot.coordinate")) == 1

        coordinate()

        run.refresh_from_db()
        assert run.status == RunStatus.RUNNING
        assert [
            job["args"] for job in _jobs(in_memory_procrastinate, "bot.decide_draw")
        ] == [{"pk": run.pk}]

        decide_draw(run.pk)

        run.refresh_from_db()
        assert run.status == RunStatus.SUCCEEDED
        assert run.completed_at is not None
        assert run.snapshot["member_id"] == bot_member.id
        assert proposal.votes.get(member=bot_member).accepted is True
        assert proposal.status == DrawProposalStatus.PENDING

    @pytest.mark.django_db
    def test_draw_passes_when_the_only_other_voters_are_bots(
        self,
        active_game_factory,
        authenticated_client,
        primary_user,
        in_memory_procrastinate,
        django_capture_on_commit_callbacks,
    ):
        game = active_game_factory()
        for member in game.members.exclude(user=primary_user):
            _make_bot(member)

        self._propose(authenticated_client, game, django_capture_on_commit_callbacks)
        coordinate()
        for run in Run.objects.all():
            decide_draw(run.pk)

        assert set(Run.objects.values_list("status", flat=True)) == {
            RunStatus.SUCCEEDED
        }
        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        assert Victory.objects.get(game=game).members.count() == 7

    @pytest.mark.django_db
    def test_humans_get_no_runs(
        self,
        active_game_factory,
        authenticated_client,
        in_memory_procrastinate,
        django_capture_on_commit_callbacks,
    ):
        game = active_game_factory()

        self._propose(authenticated_client, game, django_capture_on_commit_callbacks)

        assert not Run.objects.exists()
        assert _jobs(in_memory_procrastinate, "bot.coordinate") == []


class TestRunCommands:

    def _setup(
        self, game_factory, phase_factory, member_factory, draw_proposal_factory
    ):
        game = game_factory()
        phase = phase_factory(game=game)
        proposer = member_factory(game=game)
        bot_member = member_factory(game=game)
        _make_bot(bot_member)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=phase,
            included_member_ids=[proposer.id, bot_member.id],
        )
        return game, bot_member, proposal

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "run_status",
        [RunStatus.RUNNING, RunStatus.SUCCEEDED, RunStatus.SKIPPED],
    )
    def test_start_does_nothing_when_the_run_is_not_pending(
        self,
        run_status,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        in_memory_procrastinate,
    ):
        _, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        run = _draw_run(bot_member, proposal, status=run_status)

        assert Run.objects.start(run) is None

        run.refresh_from_db()
        assert run.status == run_status
        assert run.started_at is None
        assert _jobs(in_memory_procrastinate, "bot.decide_draw") == []

    @pytest.mark.django_db
    def test_tick_skips_runs_whose_phase_is_no_longer_current(
        self,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        in_memory_procrastinate,
    ):
        game, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        run = _draw_run(bot_member, proposal)
        phase_factory(game=game, season="Fall", ordinal=2)

        Coordinator().tick()

        run.refresh_from_db()
        assert run.status == RunStatus.SKIPPED
        assert run.completed_at is not None
        assert _jobs(in_memory_procrastinate, "bot.decide_draw") == []

    @pytest.mark.django_db
    def test_tick_waits_for_the_earliest_start(
        self,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
        in_memory_procrastinate,
    ):
        _, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        run = _draw_run(
            bot_member,
            proposal,
            earliest_start_at=timezone.now() + timedelta(minutes=1),
        )

        Coordinator().tick()

        run.refresh_from_db()
        assert run.status == RunStatus.PENDING
        assert _jobs(in_memory_procrastinate, "bot.decide_draw") == []

    @pytest.mark.django_db
    def test_tick_times_out_runs_past_their_step_timeout(
        self,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
    ):
        _, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        overdue = _draw_run(
            bot_member,
            proposal,
            status=RunStatus.RUNNING,
            started_at=timezone.now() - DrawDecisionStep.timeout - timedelta(seconds=1),
        )
        recent = _draw_run(
            bot_member,
            proposal,
            status=RunStatus.RUNNING,
            started_at=timezone.now(),
        )

        Coordinator().tick()

        overdue.refresh_from_db()
        recent.refresh_from_db()
        assert overdue.status == RunStatus.TIMED_OUT
        assert overdue.completed_at is not None
        assert recent.status == RunStatus.RUNNING

    @pytest.mark.django_db
    def test_timed_out_run_does_not_vote(
        self,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
    ):
        _, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        run = _draw_run(bot_member, proposal, status=RunStatus.TIMED_OUT)

        assert Run.objects.vote_on_draw(run, True) is None

        assert proposal.votes.get(member=bot_member).accepted is None

    @pytest.mark.django_db
    def test_refused_vote_skips_the_run(
        self,
        active_game_factory,
        primary_user,
        draw_proposal_factory,
        caplog,
    ):
        game = active_game_factory()
        proposer = game.members.get(user=primary_user)
        bot_member = game.members.exclude(user=primary_user).first()
        _make_bot(bot_member)
        proposal = draw_proposal_factory(
            game=game,
            created_by=proposer,
            phase=game.current_phase,
            included_member_ids=[proposer.id, bot_member.id],
            cancelled_at=timezone.now(),
        )
        run = _draw_run(bot_member, proposal, status=RunStatus.RUNNING)

        decide_draw(run.pk)

        run.refresh_from_db()
        assert run.status == RunStatus.SKIPPED
        assert proposal.votes.get(member=bot_member).accepted is None
        assert [
            record.levelname for record in caplog.records if record.name == "bot.steps"
        ] == ["WARNING"]

    @pytest.mark.django_db
    def test_unexpected_error_fails_the_run(
        self,
        game_factory,
        phase_factory,
        member_factory,
        draw_proposal_factory,
    ):
        _, bot_member, proposal = self._setup(
            game_factory, phase_factory, member_factory, draw_proposal_factory
        )
        run = _draw_run(bot_member, proposal, status=RunStatus.RUNNING)
        factory = Mock()
        factory.build.side_effect = RuntimeError("bot exploded")

        with patch("bot.steps.BotContextBuilder.build", return_value={}):
            with pytest.raises(RuntimeError):
                DrawDecisionStep(factory=factory).execute(run)

        run.refresh_from_db()
        assert run.status == RunStatus.FAILED
        assert run.error == "bot exploded"
        assert run.completed_at is not None
