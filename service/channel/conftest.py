import pytest
from channel.models import Channel, ChannelMessage
from django.contrib.auth import get_user_model
from django.apps import apps
from unittest.mock import patch

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
