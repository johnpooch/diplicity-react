import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import User

from bot.constants import BotKind
from bot.models import Bot
from common.constants import UserKind
from member.models import Member
from user_profile.models import UserProfile

seed_bots_migration = importlib.import_module("bot.migrations.0002_seed_bots")


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
