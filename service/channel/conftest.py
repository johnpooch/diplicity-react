import pytest
from channel.models import Channel, ChannelMessage
from django.contrib.auth import get_user_model
from django.apps import apps
from unittest.mock import patch
from common.constants import GameStatus

User = get_user_model()


@pytest.fixture
def active_game_with_private_channel(db, active_game_with_phase_state):

    private_channel = Channel.objects.create(game=active_game_with_phase_state, name="Private Channel", private=True)
    private_channel.members.add(active_game_with_phase_state.members.first())
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_public_channel(db, active_game_with_phase_state):

    Channel.objects.create(game=active_game_with_phase_state, name="Public Channel", private=False)
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_channels(db, active_game_with_phase_state, secondary_user, classical_france_nation):

    private_member_channel = Channel.objects.create(
        game=active_game_with_phase_state, name="Private Member", private=True
    )
    private_member_channel.members.add(active_game_with_phase_state.members.first())
    ChannelMessage.objects.create(
        channel=private_member_channel, sender=active_game_with_phase_state.members.first(), body="Test message"
    )
    Channel.objects.create(game=active_game_with_phase_state, name="Private Non-Member", private=True)
    Channel.objects.create(game=active_game_with_phase_state, name="Public Channel", private=False)
    active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    return active_game_with_phase_state


@pytest.fixture
def game_with_two_members(
    db, active_game_with_phase_state, secondary_user, classical_england_nation, classical_france_nation
):
    game = active_game_with_phase_state
    game.members.first().nation = classical_england_nation
    game.members.first().save()
    game.members.create(user=secondary_user, nation=classical_france_nation)
    return game


@pytest.fixture
def sandbox_game(primary_user, classical_variant, classical_england_nation):
    """Create a sandbox game for testing."""
    Game = apps.get_model("game", "Game")
    game = Game.objects.create(
        name="Sandbox Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
        sandbox=True,
    )
    game.members.create(user=primary_user, nation=classical_england_nation)
    return game


@pytest.fixture
def sandbox_game_with_channel(sandbox_game):
    """Create a sandbox game with a channel for testing."""
    channel = Channel.objects.create(game=sandbox_game, name="Sandbox Channel", private=True)
    channel.members.add(sandbox_game.members.first())
    return sandbox_game
