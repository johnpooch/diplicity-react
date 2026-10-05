from rest_framework.permissions import BasePermission

from .policies import can_mute_channel, can_rename_channel


def is_channel_member(channel, member):
    if member is None:
        return False
    if not channel.private:
        return True
    return channel.members.filter(id=member.id).exists()


class CanRenameChannel(BasePermission):
    message = "You cannot rename this channel."

    def has_permission(self, request, view):
        channel = view.get_channel()
        game = view.get_game()
        member = view.get_current_game_member()
        return can_rename_channel(
            channel,
            game,
            member,
            is_channel_member(channel, member),
        )


class CanMuteChannel(BasePermission):
    message = "You cannot mute this channel."

    def has_permission(self, request, view):
        channel = view.get_channel()
        member = view.get_current_game_member()
        return can_mute_channel(member, is_channel_member(channel, member))
