from unittest.mock import patch

import pytest

from adjudication import service as adjudication_service
from bot_profile.utils import get_bot_user
from common.constants import DeadlineMode, MovementPhaseDuration, NationAssignment
from game.models import Game


@pytest.fixture
def bot_game_factory(db, primary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany):
    def _create():
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="Bot Game",
            nation_assignment=NationAssignment.ORDERED,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            created_by=primary_user,
        )
        game.members.create(user=primary_user)
        game.members.create(user=get_bot_user())

        with patch.object(
            adjudication_service, "start", return_value=adjudication_data_italy_vs_germany
        ):
            game.start()

        return game

    return _create


@pytest.fixture
def bot_public_channel_factory(bot_game_factory):
    def _create():
        game = bot_game_factory()
        channel = game.channels.create(name="Public Press", private=False)
        for member in game.members.all():
            channel.member_channels.create(member=member)
        return game, channel

    return _create


@pytest.fixture
def bot_private_channel_factory(bot_game_factory):
    def _create():
        game = bot_game_factory()
        channel = game.channels.create(name="Private", private=True)
        for member in game.members.all():
            channel.member_channels.create(member=member)
        return game, channel

    return _create
