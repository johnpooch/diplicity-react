from common.loaders import Hydrator
from member.models import Member

from .policies import can_leave_channel, can_mute_channel, can_rename_channel


class ChannelPermissionsHydrator(Hydrator):
    def hydrate(self, channels, actor):
        members = {}
        if actor.pk is not None:
            viewer_members = Member.objects.filter(
                game_id__in={channel.game_id for channel in channels},
                user_id=actor.pk,
            ).order_by("pk")
            for member in viewer_members:
                members.setdefault(member.game_id, member)
        for channel in channels:
            member = members.get(channel.game_id)
            is_channel_member = member is not None and (
                not channel.private
                or any(
                    channel_member.id == member.id
                    for channel_member in channel.members.all()
                )
            )
            channel.viewer_can_rename = can_rename_channel(
                channel, channel.game, member, is_channel_member
            )
            channel.viewer_can_mute = can_mute_channel(member, is_channel_member)
            channel.viewer_can_leave = can_leave_channel(
                channel, member, is_channel_member
            )
