from common.constants import GameStatus, PressType


def can_rename_channel(channel, game, member, is_channel_member):
    no_press_active = (
        game.press_type == PressType.NO_PRESS
        and game.status not in (GameStatus.COMPLETED, GameStatus.ABANDONED)
    )
    return bool(
        member
        and is_channel_member
        and channel.private
        and not member.kicked
        and not game.sandbox
        and not no_press_active
    )


def can_mute_channel(member, is_channel_member):
    return bool(member and is_channel_member)
