from types import SimpleNamespace

import pytest

from common.constants import GameStatus, PressType

from channel.policies import can_mute_channel, can_rename_channel


def test_can_rename_private_channel():
    channel = SimpleNamespace(private=True)
    game = SimpleNamespace(
        press_type=PressType.FULL_PRESS,
        status=GameStatus.ACTIVE,
        sandbox=False,
    )
    member = SimpleNamespace(kicked=False)

    assert can_rename_channel(channel, game, member, True) is True


@pytest.mark.parametrize(
    ("private", "member", "is_channel_member", "sandbox", "press_type", "status"),
    [
        (False, SimpleNamespace(kicked=False), True, False, PressType.FULL_PRESS, GameStatus.ACTIVE),
        (True, None, False, False, PressType.FULL_PRESS, GameStatus.ACTIVE),
        (True, SimpleNamespace(kicked=False), False, False, PressType.FULL_PRESS, GameStatus.ACTIVE),
        (True, SimpleNamespace(kicked=True), True, False, PressType.FULL_PRESS, GameStatus.ACTIVE),
        (True, SimpleNamespace(kicked=False), True, True, PressType.FULL_PRESS, GameStatus.ACTIVE),
        (True, SimpleNamespace(kicked=False), True, False, PressType.NO_PRESS, GameStatus.ACTIVE),
    ],
)
def test_cannot_rename_channel_when_not_permitted(
    private,
    member,
    is_channel_member,
    sandbox,
    press_type,
    status,
):
    channel = SimpleNamespace(private=private)
    game = SimpleNamespace(
        press_type=press_type,
        status=status,
        sandbox=sandbox,
    )

    assert can_rename_channel(channel, game, member, is_channel_member) is False


def test_can_rename_private_channel_after_no_press_game_ends():
    channel = SimpleNamespace(private=True)
    game = SimpleNamespace(
        press_type=PressType.NO_PRESS,
        status=GameStatus.COMPLETED,
        sandbox=False,
    )
    member = SimpleNamespace(kicked=False)

    assert can_rename_channel(channel, game, member, True) is True


@pytest.mark.parametrize(
    ("member", "is_channel_member", "expected"),
    [
        (SimpleNamespace(), True, True),
        (SimpleNamespace(), False, False),
        (None, False, False),
    ],
)
def test_can_mute_channel(member, is_channel_member, expected):
    assert can_mute_channel(member, is_channel_member) is expected
