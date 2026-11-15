from common.loaders import Hydrator
from member.loaders import BaseMemberLoader
from member.models import Member

from .models import Channel
from .policies import can_leave_channel, can_mute_channel, can_rename_channel


class SenderHydrator(Hydrator):
    def hydrate(self, messages, actor):
        BaseMemberLoader.hydrate([message.sender for message in messages], actor)


class LatestMessageHydrator(Hydrator):
    def hydrate(self, channels, actor):
        Channel.objects.hydrate_latest_messages(channels)
        BaseMemberLoader.hydrate(
            [
                channel.latest_message.sender
                for channel in channels
                if channel.latest_message is not None
            ],
            actor,
        )


class ChannelNameHydrator(Hydrator):
    def hydrate(self, channels, actor):
        private = [channel for channel in channels if channel.private]
        BaseMemberLoader.hydrate(
            [member for channel in private for member in channel.members.all()],
            actor,
        )
        for channel in channels:
            channel.display_name = (
                ", ".join(
                    sorted(
                        member.nation.name if member.nation else member.visible_name
                        for member in channel.members.all()
                        if member.replaced_by_id is None
                    )
                )
                if channel.private
                else channel.name
            )


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
