from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from adjudicator import service as adjudication_service
from agent.api_client import bot_request_host
from channel.models import ChannelEvent, ChannelMessage
from common.constants import DeadlineMode, MovementPhaseDuration
from game.models import Game


@pytest.fixture
def bot_game_factory(db, primary_user, bot_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany):
    def _create():
        game = Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="Bot Game",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            created_by=primary_user,
        )
        game.members.create(user=primary_user)
        game.members.create(user=bot_user)

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


def _create_history(channel, senders, count):
    base = timezone.now() - timedelta(days=1)
    messages = ChannelMessage.objects.bulk_create(
        [
            ChannelMessage(channel=channel, sender=senders[index % len(senders)], body=f"Message {index}")
            for index in range(count)
        ]
    )
    for index, message in enumerate(messages):
        message.created_at = base + timedelta(seconds=index)
    ChannelMessage.objects.bulk_update(messages, ["created_at"])


@pytest.fixture
def bot_game_with_channel_history(bot_public_channel_factory, bot_user):
    game, public_channel = bot_public_channel_factory()
    bot_member = game.members.get(user=bot_user)
    human_member = game.members.get(user=game.created_by)
    private_channel = game.channels.create(name="Private", title="Allies", private=True)
    private_channel.member_channels.create(member=bot_member, muted_indefinitely=True)
    private_channel.member_channels.create(member=human_member)
    hidden_channel = game.channels.create(name="Hidden", private=True)
    hidden_channel.member_channels.create(member=human_member)
    empty_channel = game.channels.create(name="Empty", private=False)

    _create_history(public_channel, [human_member, bot_member], 230)
    _create_history(private_channel, [bot_member, human_member], 150)
    _create_history(hidden_channel, [human_member], 3)
    ChannelEvent.objects.create_for_channels(
        "phase_resolved", [public_channel, private_channel, empty_channel], phase=game.current_phase
    )
    ChannelEvent.objects.create_for_channels(
        "channel_renamed", [private_channel], payload={"nation": "Italy", "name": "Allies"}
    )
    ChannelEvent.objects.create_for_channels("game_start", [public_channel])

    legacy_client = APIClient(SERVER_NAME=bot_request_host())
    legacy_client.force_authenticate(user=bot_user)
    legacy_channels = list(legacy_client.get(reverse("channel-list", args=[game.id])).data)
    return game, legacy_channels
