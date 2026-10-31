from common.constants import GameStatus, MemberKind, PressType


def _no_press_active(game):
    return game.press_type == PressType.NO_PRESS and game.status not in (
        GameStatus.COMPLETED,
        GameStatus.ABANDONED,
    )


def can_create_channel(game, member):
    return bool(
        member
        and member.kind == MemberKind.PLAYER
        and not member.left_seat
        and not game.sandbox
        and not _no_press_active(game)
    )


def can_rename_channel(channel, game, member, is_channel_member):
    return bool(
        member
        and is_channel_member
        and channel.private
        and not member.left_seat
        and not game.sandbox
        and not _no_press_active(game)
    )


def can_mute_channel(member, is_channel_member):
    return bool(member and is_channel_member)
