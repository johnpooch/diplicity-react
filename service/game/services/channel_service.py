import logging

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Case, When, Value, BooleanField
from rest_framework import exceptions

from .. import models
from .base_service import BaseService

logger = logging.getLogger("game")


class ChannelService(BaseService):
    def __init__(self, user):
        self.user = user

    def create(self, game_id, data):
        logger.info(f"ChannelService.create() called with game_id: {game_id} and data: {data}")

        game = get_object_or_404(models.Game, id=game_id)

        if game.status != models.Game.ACTIVE:
            logger.warning(f"ChannelService.create() called when game is not active. This shouldn't happen.")
            raise exceptions.ValidationError("Game is not active.")

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(f"ChannelService.create() called when user is not a member of the game. This shouldn't happen.")
            raise exceptions.PermissionDenied("User is not a member of the game.")

        member_ids = data["members"] + [member.id]
        channel_members = game.members.filter(id__in=member_ids)

        if channel_members.count() != len(member_ids):
            logger.warning(f"ChannelService.create() called when one or more members are not part of the game. This shouldn't happen.")
            raise exceptions.ValidationError(
                "One or more members are not part of the game."
            )

        nations = sorted([m.nation for m in channel_members])
        channel_name = ", ".join(nations)

        if game.channels.filter(name=channel_name).exists():
            logger.warning(f"ChannelService.create() called when a channel with the same members already exists. This shouldn't happen.")
            raise exceptions.ValidationError(
                "A channel with the same members already exists."
            )

        with transaction.atomic():
            channel = models.Channel.objects.create(
                name=channel_name,
                private=True,
                game=game,
            )
            channel.members.set(channel_members)

        logger.info(f"ChannelService.create() returning channel: {channel}")
        return channel

    def create_message(self, game_id, channel_id, data):
        logger.info(f"ChannelService.create_message() called with game_id: {game_id}, channel_id: {channel_id} and data: {data}")

        game = get_object_or_404(models.Game, id=game_id)
        channel = get_object_or_404(models.Channel, id=channel_id, game=game)

        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(f"ChannelService.create_message() called when user is not a member of the game. This shouldn't happen.")
            raise exceptions.PermissionDenied("User is not a member of the game.")

        # Check if user can post in this channel
        if channel.private and not channel.members.filter(id=member.id).exists():
            logger.warning(f"ChannelService.create_message() called when user is not a member of this private channel. This shouldn't happen.")
            raise exceptions.PermissionDenied("User is not a member of this private channel.")

        body = data["body"].strip()
        if not body:
            logger.warning(f"ChannelService.create_message() called when message content is empty. This shouldn't happen.")
            raise exceptions.ValidationError("Message content cannot be empty.")

        message = models.ChannelMessage.objects.create(
            channel=channel,
            sender=member,
            body=body,
        )

        logger.info(f"ChannelService.create_message() returning message: {message}")

        if channel.private:
            other_members = channel.members.exclude(id=member.id)
        else:
            other_members = game.members.exclude(id=member.id)
        
        user_ids = [m.user.id for m in other_members]
        notification_data = {
            "title": "New Message",
            "body": f"{member.user.username} sent a message in {channel.name}.",
            "type": "channel_message",
            "game_id": str(game_id),
            "channel_id": str(channel_id),
        }

        logger.info(f"ChannelService.create_message() adding task to notify users: {user_ids}")
        from .notification_service import NotificationService
        NotificationService(self.user).notify(user_ids, notification_data)

        logger.info(f"ChannelService.create_message() returning message: {message}")
        return message

    def list(self, game_id):
        logger.info(f"ChannelService.list() called with game_id: {game_id}")

        game = get_object_or_404(models.Game, id=game_id)
        member = game.members.filter(user=self.user).first()
        if not member:
            channels = game.channels.prefetch_related(
                "messages",
                "messages__sender",
                "messages__sender__user"
            ).filter(private=False)
        else:
            channels = game.channels.prefetch_related(
                "messages",
                "messages__sender",
                "messages__sender__user"
            ).filter(
                Q(private=False) | Q(members=member)
            ).distinct()

        # Annotate is_current_user for message senders
        for channel in channels:
            for message in channel.messages.all():
                message.sender.is_current_user = message.sender.user == self.user

        logger.info(f"ChannelService.list() returning channels: {channels}")
        return channels

    def retrieve(self, game_id, channel_id):
        logger.info(f"ChannelService.retrieve() called with game_id: {game_id}, channel_id: {channel_id}")

        game = get_object_or_404(models.Game, id=game_id)
        member = game.members.filter(user=self.user).first()
        if not member:
            logger.warning(f"ChannelService.retrieve() called when user is not a member of the game. This shouldn't happen.")
            raise exceptions.PermissionDenied("User is not a member of the game.")

        # Get channel only if it's public or user is a member
        queryset = game.channels.prefetch_related(
            "messages",
            "messages__sender",
            "messages__sender__user"
        ).filter(
            Q(private=False) | Q(members=member)
        ).distinct()
        channel = get_object_or_404(queryset, id=channel_id)

        # Annotate is_current_user for message senders
        for message in channel.messages.all():
            message.sender.is_current_user = message.sender.user == self.user

        logger.info(f"ChannelService.retrieve() returning channel: {channel}")
        return channel
