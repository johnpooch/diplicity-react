import pytest
from datetime import timedelta
from unittest.mock import patch
from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory
from channel.models import Channel, ChannelMessage
from bot_profile.utils import get_bot_user
from game.models import Game
from game.serializers import GameRetrieveSerializer
from notification.models import Notification

from common.constants import GameStatus


def _channel_message_notifications():
    return Notification.objects.filter(event_type="channel_message")


class TestChannelCreateView:

    @pytest.mark.django_db
    def test_create_channel_success(
        self, authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
    ):
        other_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)

        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["name"] == "England, France"

    @pytest.mark.django_db
    def test_create_channel_unauthenticated(self, unauthenticated_client, active_game_with_phase_state):
        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": []}
        response = unauthenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_create_channel_invalid_member(self, authenticated_client, active_game_with_phase_state):
        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [999]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_channel_duplicate_members(
        self, authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
    ):
        other_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)

        Channel.objects.create(game=active_game_with_phase_state, name="England, France", private=True)

        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_channel_inactive_game(
        self, authenticated_client, classical_variant, primary_user, classical_england_nation
    ):
        Game = apps.get_model("game", "Game")

        inactive_game = Game.objects.create(
            name="Inactive Game",
            variant=classical_variant,
            status=GameStatus.PENDING,
        )
        inactive_game.members.create(user=primary_user, nation=classical_england_nation)

        url = reverse("channel-create", args=[inactive_game.id])
        payload = {"member_ids": []}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_channel_non_member(
        self, authenticated_client_for_secondary_user, active_game_with_phase_state, classical_france_nation
    ):
        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": []}
        response = authenticated_client_for_secondary_user.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_channel_sandbox_game_forbidden(self, authenticated_client, sandbox_game_factory):
        game = sandbox_game_factory()
        url = reverse("channel-create", args=[game.id])
        payload = {"member_ids": []}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChannelListView:

    @pytest.mark.django_db
    def test_list_channels_as_member(self, authenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) == 2

        channel_names = [channel["name"] for channel in response.data]
        assert "Private Member" in channel_names
        assert "Public Channel" in channel_names
        assert "Private Non-Member" not in channel_names

    @pytest.mark.django_db
    def test_list_channels_as_non_member(
        self, authenticated_client_for_tertiary_user, active_game_with_channels, classical_france_nation
    ):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client_for_tertiary_user.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) == 1
        channel = response.data[0]
        assert channel["name"] == "Public Channel"

    @pytest.mark.django_db
    def test_list_channels_unauthenticated(self, unauthenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Public Channel"

    @pytest.mark.django_db
    def test_list_channels_unauthenticated_is_current_user_false(self, unauthenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for channel in response.data:
            for msg in channel.get("messages", []):
                assert msg["sender"]["is_current_user"] is False

    @pytest.mark.django_db
    def test_list_channels_with_messages(self, authenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        private_channel = next(ch for ch in response.data if ch["name"] == "Private Member")
        assert len(private_channel["messages"]) == 1
        assert private_channel["messages"][0]["body"] == "Test message"
        assert private_channel["messages"][0]["sender"]["is_current_user"] == True

    @pytest.mark.django_db
    def test_list_channels_excludes_other_games_channels(
        self, authenticated_client, active_game_with_channels, classical_variant, primary_user, classical_england_nation
    ):
        Game = apps.get_model("game", "Game")

        other_game = Game.objects.create(
            name="Other Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        other_game.members.create(user=primary_user, nation=classical_england_nation)

        Channel.objects.create(game=other_game, name="Other Game Channel", private=False)

        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        channel_names = [channel["name"] for channel in response.data]
        assert "Other Game Channel" not in channel_names
        assert "Private Member" in channel_names
        assert "Public Channel" in channel_names


class TestChannelListOrdering:

    @pytest.mark.django_db
    def test_public_channel_first_even_with_older_activity(
        self, authenticated_client, active_game_with_phase_state
    ):
        game = active_game_with_phase_state
        member = game.members.first()

        public_channel = Channel.objects.create(game=game, name="Public Press", private=False)
        private_channel = Channel.objects.create(game=game, name="Private", private=True)
        private_channel.members.add(member)

        public_message = ChannelMessage.objects.create(channel=public_channel, sender=member, body="old")
        private_message = ChannelMessage.objects.create(channel=private_channel, sender=member, body="new")
        ChannelMessage.objects.filter(id=public_message.id).update(created_at=timezone.now() - timedelta(days=2))
        ChannelMessage.objects.filter(id=private_message.id).update(created_at=timezone.now())

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        names = [ch["name"] for ch in response.data]
        assert names == ["Public Press", "Private"]

    @pytest.mark.django_db
    def test_private_channels_sorted_by_most_recent_activity(
        self, authenticated_client, active_game_with_phase_state
    ):
        game = active_game_with_phase_state
        member = game.members.first()

        Channel.objects.create(game=game, name="Public Press", private=False)
        older = Channel.objects.create(game=game, name="Older", private=True)
        newer = Channel.objects.create(game=game, name="Newer", private=True)
        older.members.add(member)
        newer.members.add(member)

        older_message = ChannelMessage.objects.create(channel=older, sender=member, body="older")
        newer_message = ChannelMessage.objects.create(channel=newer, sender=member, body="newer")
        ChannelMessage.objects.filter(id=older_message.id).update(created_at=timezone.now() - timedelta(hours=1))
        ChannelMessage.objects.filter(id=newer_message.id).update(created_at=timezone.now())

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        names = [ch["name"] for ch in response.data]
        assert names == ["Public Press", "Newer", "Older"]

    @pytest.mark.django_db
    def test_channels_without_messages_sorted_last(
        self, authenticated_client, active_game_with_phase_state
    ):
        game = active_game_with_phase_state
        member = game.members.first()

        Channel.objects.create(game=game, name="Public Press", private=False)
        with_message = Channel.objects.create(game=game, name="With Message", private=True)
        without_message = Channel.objects.create(game=game, name="Without Message", private=True)
        with_message.members.add(member)
        without_message.members.add(member)

        ChannelMessage.objects.create(channel=with_message, sender=member, body="hello")

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        names = [ch["name"] for ch in response.data]
        assert names == ["Public Press", "With Message", "Without Message"]


class TestChannelMessageCreateView:

    @pytest.mark.django_db
    def test_create_message_in_private_channel_success(
        self,
        authenticated_client,
        active_game_with_private_channel,
        in_memory_procrastinate,
    ):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Author is the only channel member, so there is no one to notify.
        assert not _channel_message_notifications().exists()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_as_member_success(
        self,
        authenticated_client,
        active_game_with_public_channel,
        in_memory_procrastinate,
    ):
        public_channel = Channel.objects.get(game=active_game_with_public_channel, private=False)
        public_channel.members.add(active_game_with_public_channel.members.first())

        url = reverse("channel-message-create", args=[active_game_with_public_channel.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Author is the only game member, so there is no one to notify.
        assert not _channel_message_notifications().exists()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_without_explicit_members(
        self, authenticated_client, game_with_two_members, in_memory_procrastinate
    ):
        public_channel = Channel.objects.create(game=game_with_two_members, name="Public Press", private=False)
        sender_user_id = game_with_two_members.members.first().user_id

        url = reverse("channel-message-create", args=[game_with_two_members.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        notifications = _channel_message_notifications()
        assert notifications.count() == 1
        recipient_ids = list(notifications.values_list("recipient_id", flat=True))
        assert len(recipient_ids) == 1
        assert sender_user_id not in recipient_ids

    @pytest.mark.django_db
    def test_create_message_in_private_channel_notifies_only_channel_members(
        self,
        authenticated_client,
        game_with_two_members,
        in_memory_procrastinate,
        classical_england_nation,
    ):
        private_channel = Channel.objects.create(game=game_with_two_members, name="Private Channel", private=True)
        primary_member = game_with_two_members.members.get(nation=classical_england_nation)
        private_channel.members.add(primary_member)

        url = reverse("channel-message-create", args=[game_with_two_members.id, private_channel.id])
        payload = {"body": "Hello in private channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # The other game member is not in this private channel, so is not notified.
        assert not _channel_message_notifications().exists()

    @pytest.mark.django_db
    def test_create_message_in_private_channel_with_multiple_members(
        self,
        authenticated_client,
        game_with_two_members,
        in_memory_procrastinate,
        classical_england_nation,
        classical_france_nation,
    ):
        private_channel = Channel.objects.create(game=game_with_two_members, name="Private Channel", private=True)
        primary_member = game_with_two_members.members.get(nation=classical_england_nation)
        secondary_member = game_with_two_members.members.get(nation=classical_france_nation)
        private_channel.members.add(primary_member, secondary_member)

        url = reverse("channel-message-create", args=[game_with_two_members.id, private_channel.id])
        payload = {"body": "Hello in private channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        notifications = _channel_message_notifications()
        assert notifications.count() == 1
        assert list(notifications.values_list("recipient_id", flat=True)) == [secondary_member.user_id]

    @pytest.mark.django_db
    def test_create_message_in_public_channel_with_explicit_members_still_notifies_all(
        self,
        authenticated_client,
        game_with_two_members,
        in_memory_procrastinate,
        classical_england_nation,
        classical_france_nation,
    ):
        public_channel = Channel.objects.create(game=game_with_two_members, name="Public Press", private=False)
        primary_member = game_with_two_members.members.get(nation=classical_england_nation)
        secondary_member = game_with_two_members.members.get(nation=classical_france_nation)
        public_channel.members.add(primary_member, secondary_member)

        url = reverse("channel-message-create", args=[game_with_two_members.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        notifications = _channel_message_notifications()
        assert notifications.count() == 1
        assert list(notifications.values_list("recipient_id", flat=True)) == [secondary_member.user_id]

    @pytest.mark.django_db
    def test_create_message_in_private_channel_as_non_member_fails(
        self, authenticated_client_for_secondary_user, active_game_with_private_channel
    ):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "This should fail"}
        response = authenticated_client_for_secondary_user.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_message_empty_body(self, authenticated_client, active_game_with_private_channel):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": ""}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_message_whitespace_only_body(self, authenticated_client, active_game_with_private_channel):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "   "}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_message_unauthenticated(self, unauthenticated_client, active_game_with_private_channel):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "Hello, world!"}
        response = unauthenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_create_message_non_game_member(
        self, authenticated_client_for_tertiary_user, active_game_with_public_channel
    ):
        public_channel = Channel.objects.get(game=active_game_with_public_channel, private=False)
        url = reverse("channel-message-create", args=[active_game_with_public_channel.id, public_channel.id])
        payload = {"body": "This should fail"}
        response = authenticated_client_for_tertiary_user.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_message_nonexistent_channel(self, authenticated_client, active_game_with_phase_state):
        url = reverse("channel-message-create", args=[active_game_with_phase_state.id, 999])
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_create_message_sandbox_game_forbidden(self, authenticated_client, sandbox_game_with_channel):
        channel = Channel.objects.get(game=sandbox_game_with_channel)
        url = reverse("channel-message-create", args=[sandbox_game_with_channel.id, channel.id])
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChannelModels:

    @pytest.mark.django_db
    def test_channel_queryset_accessible_to_user_as_member(self, active_game_with_channels, primary_user):
        game = active_game_with_channels
        channels = Channel.objects.accessible_to_user(primary_user, game)

        assert channels.count() == 2
        channel_names = [ch.name for ch in channels]
        assert "Private Member" in channel_names
        assert "Public Channel" in channel_names
        assert "Private Non-Member" not in channel_names

    @pytest.mark.django_db
    def test_channel_queryset_accessible_to_user_as_non_member(self, active_game_with_channels, tertiary_user):
        game = active_game_with_channels
        channels = Channel.objects.accessible_to_user(tertiary_user, game)

        assert channels.count() == 1
        assert channels.first().name == "Public Channel"

    @pytest.mark.django_db
    def test_channel_queryset_with_related_data(self, active_game_with_channels):
        channels = Channel.objects.with_related_data()

        for channel in channels:
            for message in channel.messages.all():
                assert message.sender is not None

    @pytest.mark.django_db
    def test_channel_queryset_accessible_to_user_excludes_other_games(
        self, active_game_with_channels, primary_user, classical_variant, classical_england_nation
    ):
        Game = apps.get_model("game", "Game")

        other_game = Game.objects.create(
            name="Other Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        other_game.members.create(user=primary_user, nation=classical_england_nation)

        other_game_public_channel = Channel.objects.create(game=other_game, name="Other Game Public", private=False)
        other_game_private_channel = Channel.objects.create(game=other_game, name="Other Game Private", private=True)
        other_game_private_channel.members.add(other_game.members.first())

        channels = Channel.objects.accessible_to_user(primary_user, active_game_with_channels)

        channel_names = [ch.name for ch in channels]
        assert "Other Game Public" not in channel_names
        assert "Other Game Private" not in channel_names
        assert "Private Member" in channel_names
        assert "Public Channel" in channel_names


@pytest.fixture
def mock_immediate_on_commit():
    def immediate_on_commit(func):
        func()  # Execute immediately instead of deferring

    with patch("django.db.transaction.on_commit", side_effect=immediate_on_commit):
        yield


class TestChannelMarkReadView:

    @pytest.mark.django_db
    def test_mark_read_success(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")
        primary_member = game.members.first()

        from channel.models import ChannelMember
        channel_member = ChannelMember.objects.get(member=primary_member, channel=channel)
        original_last_read_at = channel_member.last_read_at

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        channel_member.refresh_from_db()
        assert channel_member.last_read_at > original_last_read_at

    @pytest.mark.django_db
    def test_mark_read_unauthenticated(self, unauthenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_mark_read_non_game_member(
        self, authenticated_client_for_tertiary_user, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = authenticated_client_for_tertiary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_mark_read_non_channel_member_private_channel(
        self, authenticated_client_for_secondary_user, active_game_with_private_channel
    ):
        game = active_game_with_private_channel
        private_channel = Channel.objects.get(game=game, private=True)

        url = reverse("channel-mark-read", args=[game.id, private_channel.id])
        response = authenticated_client_for_secondary_user.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_mark_read_idempotent(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response1 = authenticated_client.post(url)
        assert response1.status_code == status.HTTP_204_NO_CONTENT

        response2 = authenticated_client.post(url)
        assert response2.status_code == status.HTTP_204_NO_CONTENT


class TestChannelUnreadCount:

    @pytest.mark.django_db
    def test_channel_list_includes_unread_count(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        channel_data = next(ch for ch in response.data if ch["name"] == "Public Press")
        assert channel_data["unread_message_count"] == 2

    @pytest.mark.django_db
    def test_unread_count_resets_after_mark_read(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        mark_read_url = reverse("channel-mark-read", args=[game.id, channel.id])
        authenticated_client.post(mark_read_url)

        list_url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(list_url)

        channel_data = next(ch for ch in response.data if ch["name"] == "Public Press")
        assert channel_data["unread_message_count"] == 0

    @pytest.mark.django_db
    def test_unread_count_zero_for_anonymous(self, unauthenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        url = reverse("channel-list", args=[game.id])
        response = unauthenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for channel_data in response.data:
            assert channel_data["unread_message_count"] == 0

    @pytest.mark.django_db
    def test_own_messages_not_counted_as_unread(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        channel = Channel.objects.get(game=game, name="Public Press")
        ChannelMessage.objects.create(channel=channel, sender=primary_member, body="Own message")

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        channel_data = next(ch for ch in response.data if ch["name"] == "Public Press")
        assert channel_data["unread_message_count"] == 2

    @pytest.mark.django_db
    def test_unread_count_per_channel_independence(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        secondary_member = game.members.exclude(id=primary_member.id).first()

        private_channel = Channel.objects.create(game=game, name="Private Channel", private=True)
        private_channel.members.add(primary_member, secondary_member)

        ChannelMessage.objects.create(channel=private_channel, sender=secondary_member, body="Private msg")

        public_channel = Channel.objects.get(game=game, name="Public Press")
        mark_read_url = reverse("channel-mark-read", args=[game.id, public_channel.id])
        authenticated_client.post(mark_read_url)

        list_url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(list_url)

        public_data = next(ch for ch in response.data if ch["name"] == "Public Press")
        private_data = next(ch for ch in response.data if ch["name"] == "Private Channel")

        assert public_data["unread_message_count"] == 0
        assert private_data["unread_message_count"] == 1


class TestGameRetrieveUnreadCount:

    @pytest.mark.django_db
    def test_game_retrieve_includes_total_unread_count(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        url = reverse("game-retrieve", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_game_retrieve_unread_count_zero_for_anonymous(
        self, unauthenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        url = reverse("game-retrieve", args=[game.id])
        response = unauthenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_own_messages_not_counted_in_total_unread(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        channel = Channel.objects.get(game=game, name="Public Press")
        ChannelMessage.objects.create(channel=channel, sender=primary_member, body="Own message")

        url = reverse("game-retrieve", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_game_retrieve_unread_count_resets_after_mark_read(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        mark_read_url = reverse("channel-mark-read", args=[game.id, channel.id])
        authenticated_client.post(mark_read_url)

        url = reverse("game-retrieve", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_retrieve_serializer_computes_unread_without_annotation(
        self, game_with_public_channel_and_messages, primary_user
    ):
        game = Game.objects.get(pk=game_with_public_channel_and_messages.pk)
        request = APIRequestFactory().get("/")
        request.user = primary_user

        data = GameRetrieveSerializer(game, context={"request": request}).data

        assert data["total_unread_message_count"] == 2


@pytest.fixture
def active_game_with_bot_channel(active_game_with_phase_state, classical_france_nation):
    game = active_game_with_phase_state
    bot_member = game.members.create(user=get_bot_user(), nation=classical_france_nation)
    channel = Channel.objects.create(game=game, name="Bot Channel", private=True)
    channel.members.add(game.members.first(), bot_member)
    return game


class TestChannelMessageCharLimit:

    @pytest.mark.django_db
    def test_message_over_limit_rejected(
        self, authenticated_client, active_game_with_private_channel, in_memory_procrastinate, settings
    ):
        channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, channel.id])
        response = authenticated_client.post(
            url, {"body": "x" * (settings.CHAT_MESSAGE_MAX_CHARS + 1)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"{settings.CHAT_MESSAGE_MAX_CHARS} characters" in response.data["body"][0]

    @pytest.mark.django_db
    def test_message_at_limit_accepted(
        self, authenticated_client, active_game_with_private_channel, in_memory_procrastinate, settings
    ):
        channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, channel.id])
        response = authenticated_client.post(
            url, {"body": "x" * settings.CHAT_MESSAGE_MAX_CHARS}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED


class TestChannelMessagePhaseStamping:

    @pytest.mark.django_db
    def test_message_stamped_with_current_phase(
        self, authenticated_client, active_game_with_private_channel, in_memory_procrastinate
    ):
        game = active_game_with_private_channel
        channel = Channel.objects.get(game=game, private=True)
        url = reverse("channel-message-create", args=[game.id, channel.id])
        authenticated_client.post(url, {"body": "hello"}, format="json")

        message = channel.messages.get()
        assert message.phase_id == game.current_phase.id


class TestChannelMessageBotCap:

    @pytest.mark.django_db
    def test_cap_enforced_in_bot_channel(
        self, authenticated_client, active_game_with_bot_channel, in_memory_procrastinate, settings
    ):
        game = active_game_with_bot_channel
        channel = Channel.objects.get(game=game, name="Bot Channel")
        url = reverse("channel-message-create", args=[game.id, channel.id])

        for _ in range(settings.BOT_CHANNEL_MESSAGE_CAP):
            response = authenticated_client.post(url, {"body": "hello"}, format="json")
            assert response.status_code == status.HTTP_201_CREATED

        response = authenticated_client.post(url, {"body": "one too many"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "reached the limit" in response.data["non_field_errors"][0]

    @pytest.mark.django_db
    def test_no_cap_in_human_only_channel(
        self, authenticated_client, active_game_with_private_channel, in_memory_procrastinate, settings
    ):
        game = active_game_with_private_channel
        channel = Channel.objects.get(game=game, private=True)
        url = reverse("channel-message-create", args=[game.id, channel.id])

        for _ in range(settings.BOT_CHANNEL_MESSAGE_CAP + 3):
            response = authenticated_client.post(url, {"body": "hello"}, format="json")
            assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_cap_is_per_phase(
        self,
        authenticated_client,
        active_game_with_bot_channel,
        in_memory_procrastinate,
        settings,
        phase_factory,
    ):
        game = active_game_with_bot_channel
        channel = Channel.objects.get(game=game, name="Bot Channel")
        url = reverse("channel-message-create", args=[game.id, channel.id])

        for _ in range(settings.BOT_CHANNEL_MESSAGE_CAP):
            authenticated_client.post(url, {"body": "hello"}, format="json")
        blocked = authenticated_client.post(url, {"body": "blocked"}, format="json")
        assert blocked.status_code == status.HTTP_400_BAD_REQUEST

        phase_factory(game=game, ordinal=game.current_phase.ordinal + 1, season="Fall")
        allowed = authenticated_client.post(url, {"body": "new phase"}, format="json")
        assert allowed.status_code == status.HTTP_201_CREATED


class TestChannelListMessageLimit:

    @pytest.mark.django_db
    def test_bot_channel_exposes_limit_and_count(
        self, authenticated_client, active_game_with_bot_channel, primary_user, settings
    ):
        game = active_game_with_bot_channel
        channel = Channel.objects.get(game=game, name="Bot Channel")
        primary_member = game.members.get(user=primary_user)
        ChannelMessage.objects.create(
            channel=channel, sender=primary_member, body="hi", phase=game.current_phase
        )

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        data = next(ch for ch in response.data if ch["name"] == "Bot Channel")
        assert data["message_limit"] == settings.BOT_CHANNEL_MESSAGE_CAP
        assert data["member_message_count"] == 1

    @pytest.mark.django_db
    def test_human_only_channel_has_null_limit(
        self, authenticated_client, active_game_with_private_channel
    ):
        game = active_game_with_private_channel
        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        data = next(ch for ch in response.data if ch["name"] == "Private Channel")
        assert data["message_limit"] is None
        assert data["member_message_count"] is None


class TestChannelMemberAutoCreation:

    @pytest.mark.django_db
    def test_game_creation_creates_channel_member_for_creator(self, authenticated_client, classical_variant):
        from channel.models import ChannelMember
        from common.constants import NationAssignment, DeadlineMode

        url = reverse("game-create")
        payload = {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
        }
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        from django.apps import apps
        Game = apps.get_model("game", "Game")
        game = Game.objects.get(id=response.data["id"])
        public_channel = game.channels.get(private=False)
        creator_member = game.members.first()

        assert ChannelMember.objects.filter(member=creator_member, channel=public_channel).exists()

    @pytest.mark.django_db
    def test_member_join_creates_channel_members_for_public_channels(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        from channel.models import ChannelMember

        game = pending_game_created_by_secondary_user
        public_channel = Channel.objects.create(game=game, name="Public Press", private=False)

        url = reverse("game-join", args=[game.id])
        response = authenticated_client.post(url, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        new_member = game.members.filter(user__username="primaryuser").first()
        assert ChannelMember.objects.filter(member=new_member, channel=public_channel).exists()
