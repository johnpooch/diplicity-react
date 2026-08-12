import pytest
from datetime import timedelta
from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from channel.models import Channel, ChannelMember, ChannelMessage
from nation.models import Nation
from notification.models import Notification

from common.constants import GameStatus, PressType


def _channel_message_notifications():
    return Notification.objects.filter(event_type="channel_message")


@pytest.fixture
def no_press_active_game(db, primary_user, classical_variant, classical_england_nation):
    Game = apps.get_model("game", "Game")
    game = Game.objects.create(
        name="No Press Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
        press_type=PressType.NO_PRESS,
    )
    game.members.create(user=primary_user, nation=classical_england_nation)
    return game


@pytest.fixture
def no_press_active_game_with_channel(no_press_active_game):
    channel = Channel.objects.create(game=no_press_active_game, name="Public Press", private=False)
    channel.members.add(no_press_active_game.members.first())
    return no_press_active_game


@pytest.fixture
def no_press_completed_game(db, primary_user, classical_variant, classical_england_nation):
    Game = apps.get_model("game", "Game")
    Phase = apps.get_model("phase", "Phase")
    game = Game.objects.create(
        name="No Press Completed Game",
        variant=classical_variant,
        status=GameStatus.COMPLETED,
        press_type=PressType.NO_PRESS,
    )
    Phase.objects.create(
        game=game,
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status="Completed",
    )
    game.members.create(user=primary_user, nation=classical_england_nation)
    return game


@pytest.fixture
def no_press_completed_game_with_channel(no_press_completed_game, secondary_user, classical_france_nation):
    game = no_press_completed_game
    game.members.create(user=secondary_user, nation=classical_france_nation)
    channel = Channel.objects.create(game=game, name="Public Press", private=False)
    channel.members.add(game.members.first())
    return game


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
    def test_create_channel_name_longer_than_250_characters(
        self, authenticated_client, active_game_with_phase_state, classical_variant
    ):
        nations = [
            Nation.objects.create(
                nation_id=f"long-name-nation-{index:02d}",
                name=f"Nation With A Long Name {index:02d}",
                color="#000000",
                variant=classical_variant,
            )
            for index in range(12)
        ]
        members = [active_game_with_phase_state.members.create(nation=nation) for nation in nations]

        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [member.id for member in members]}
        response = authenticated_client.post(url, payload, format="json")

        expected_name = ", ".join(sorted(["England"] + [nation.name for nation in nations]))
        assert len(expected_name) > 250
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == expected_name

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
    def test_create_channel_pending_game(self, authenticated_client, pending_game_created_by_primary_user):
        url = reverse("channel-create", args=[pending_game_created_by_primary_user.id])
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

    @pytest.mark.django_db
    def test_create_channel_as_kicked_member_forbidden(
        self, authenticated_client_for_secondary_user, active_game_with_kicked_member
    ):
        game = active_game_with_kicked_member
        url = reverse("channel-create", args=[game.id])
        payload = {"member_ids": [game.members.get(kicked=False).id]}
        response = authenticated_client_for_secondary_user.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Channel.objects.filter(game=game).exists()

    @pytest.mark.django_db
    def test_active_no_press_game_blocks_channel_creation(
        self, authenticated_client, no_press_active_game
    ):
        url = reverse("channel-create", args=[no_press_active_game.id])
        payload = {"member_ids": []}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_completed_no_press_game_allows_channel_creation(
        self, authenticated_client, no_press_completed_game, secondary_user, classical_france_nation
    ):
        other_member = no_press_completed_game.members.create(
            user=secondary_user, nation=classical_france_nation
        )
        url = reverse("channel-create", args=[no_press_completed_game.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_full_press_active_game_allows_channel_creation(
        self, authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
    ):
        other_member = active_game_with_phase_state.members.create(
            user=secondary_user, nation=classical_france_nation
        )
        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


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
        game = active_game_with_channels
        public_channel = Channel.objects.get(game=game, name="Public Channel")
        ChannelMessage.objects.create(channel=public_channel, sender=game.members.first(), body="Public message")

        url = reverse("channel-list", args=[game.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        channel = next(ch for ch in response.data if ch["name"] == "Public Channel")
        assert channel["latest_message"]["sender"]["is_current_user"] is False

    @pytest.mark.django_db
    def test_list_channels_includes_latest_message_preview(self, authenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        private_channel = next(ch for ch in response.data if ch["name"] == "Private Member")
        assert private_channel["latest_message"]["body"] == "Test message"
        assert private_channel["latest_message"]["sender"]["is_current_user"] is True

        public_channel = next(ch for ch in response.data if ch["name"] == "Public Channel")
        assert public_channel["latest_message"] is None

    @pytest.mark.django_db
    def test_list_channels_preview_is_most_recent_message(self, authenticated_client, active_game_with_channels):
        game = active_game_with_channels
        private_channel = Channel.objects.get(game=game, name="Private Member")
        ChannelMessage.objects.create(channel=private_channel, sender=game.members.first(), body="Newer message")

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        channel = next(ch for ch in response.data if ch["name"] == "Private Member")
        assert channel["latest_message"]["body"] == "Newer message"

    @pytest.mark.django_db
    def test_list_channels_query_count_is_constant(
        self, authenticated_client, active_game_with_channels, django_assert_num_queries
    ):
        game = active_game_with_channels
        member = game.members.first()
        private_channel = Channel.objects.get(game=game, name="Private Member")
        public_channel = Channel.objects.get(game=game, name="Public Channel")
        for index in range(10):
            ChannelMessage.objects.create(channel=private_channel, sender=member, body=f"private {index}")
            ChannelMessage.objects.create(channel=public_channel, sender=member, body=f"public {index}")

        url = reverse("channel-list", args=[game.id])
        with django_assert_num_queries(4):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

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

    @pytest.mark.django_db
    def test_list_channels_allowed_for_pending_game(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user

        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["name"] == "Public Press"

    @pytest.mark.django_db
    def test_active_no_press_game_allows_channel_list(
        self, authenticated_client, no_press_active_game_with_channel
    ):
        url = reverse("channel-list", args=[no_press_active_game_with_channel.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK


class TestChannelRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_channel_with_messages(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == channel.id
        assert response.data["name"] == "Public Press"
        assert response.data["private"] is False
        bodies = [message["body"] for message in response.data["messages"]["results"]]
        assert bodies == ["Message 2", "Message 1"]
        assert response.data["messages"]["next"] is None

    @pytest.mark.django_db
    def test_retrieve_channel_messages_are_cursor_paginated(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")
        member = game.members.first()
        for index in range(25):
            ChannelMessage.objects.create(channel=channel, sender=member, body=f"Message {index + 3}")

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["messages"]["results"]) == 20
        assert response.data["messages"]["results"][0]["body"] == "Message 27"
        assert response.data["messages"]["next"] is not None

        next_response = authenticated_client.get(response.data["messages"]["next"])
        assert next_response.status_code == status.HTTP_200_OK
        assert len(next_response.data["messages"]["results"]) == 7
        assert next_response.data["messages"]["next"] is None

    @pytest.mark.django_db
    def test_retrieve_channel_query_count_independent_of_message_count(
        self, authenticated_client, game_with_public_channel_and_messages, django_assert_num_queries
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")
        member = game.members.first()
        for index in range(18):
            ChannelMessage.objects.create(channel=channel, sender=member, body=f"Message {index + 3}")

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        with django_assert_num_queries(5):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["messages"]["results"]) == 20

    @pytest.mark.django_db
    def test_retrieve_private_channel_as_non_member_forbidden(
        self, authenticated_client_for_secondary_user, active_game_with_private_channel
    ):
        game = active_game_with_private_channel
        channel = Channel.objects.get(game=game, private=True)

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        response = authenticated_client_for_secondary_user.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_retrieve_private_channel_unauthenticated_forbidden(
        self, unauthenticated_client, active_game_with_private_channel
    ):
        game = active_game_with_private_channel
        channel = Channel.objects.get(game=game, private=True)

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        response = unauthenticated_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_retrieve_public_channel_unauthenticated(
        self, unauthenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-retrieve", args=[game.id, channel.id])
        response = unauthenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for message in response.data["messages"]["results"]:
            assert message["sender"]["is_current_user"] is False

    @pytest.mark.django_db
    def test_retrieve_nonexistent_channel(self, authenticated_client, active_game_with_phase_state):
        url = reverse("channel-retrieve", args=[active_game_with_phase_state.id, 999])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_retrieve_channel_from_other_game_not_found(
        self, authenticated_client, game_with_public_channel_and_messages, game_factory
    ):
        channel = Channel.objects.get(game=game_with_public_channel_and_messages, name="Public Press")
        other_game = game_factory()

        url = reverse("channel-retrieve", args=[other_game.id, channel.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


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

    @pytest.mark.django_db
    def test_create_message_as_kicked_member_forbidden(
        self, authenticated_client_for_secondary_user, active_game_with_kicked_member, in_memory_procrastinate
    ):
        game = active_game_with_kicked_member
        channel = Channel.objects.create(game=game, name="Public Press", private=False)
        channel.members.add(game.members.get(kicked=True))

        url = reverse("channel-message-create", args=[game.id, channel.id])
        response = authenticated_client_for_secondary_user.post(url, {"body": "Still here"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not ChannelMessage.objects.filter(channel=channel).exists()

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

    @pytest.mark.django_db
    def test_message_create_allowed_for_pending_game_member(
        self, authenticated_client, pending_game_created_by_secondary_user, in_memory_procrastinate
    ):
        game = pending_game_created_by_secondary_user
        public_channel = game.get_public_press()
        authenticated_client.post(reverse("game-join", args=[game.id]))

        url = reverse("channel-message-create", args=[game.id, public_channel.id])
        response = authenticated_client.post(url, {"body": "Hello staging"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["sender"]["nation"] is None

    @pytest.mark.django_db
    def test_message_create_blocked_for_non_member_in_pending_game(
        self, authenticated_client_for_tertiary_user, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user
        public_channel = game.get_public_press()

        url = reverse("channel-message-create", args=[game.id, public_channel.id])
        response = authenticated_client_for_tertiary_user.post(url, {"body": "Nope"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_active_no_press_game_blocks_message_sending(
        self, authenticated_client, no_press_active_game_with_channel
    ):
        channel = Channel.objects.get(game=no_press_active_game_with_channel)
        url = reverse(
            "channel-message-create",
            args=[no_press_active_game_with_channel.id, channel.id],
        )
        payload = {"body": "This should be blocked"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_completed_no_press_game_allows_message_sending(
        self,
        authenticated_client,
        no_press_completed_game_with_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        channel = Channel.objects.get(game=no_press_completed_game_with_channel)
        url = reverse(
            "channel-message-create",
            args=[no_press_completed_game_with_channel.id, channel.id],
        )
        payload = {"body": "Debriefing after the game!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_full_press_game_allows_message_sending(
        self,
        authenticated_client,
        active_game_with_private_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse(
            "channel-message-create",
            args=[active_game_with_private_channel.id, channel.id],
        )
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestChannelMarkReadView:

    @pytest.mark.django_db
    def test_mark_read_success(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")
        primary_member = game.members.first()

        channel_member = ChannelMember.objects.get(member=primary_member, channel=channel)
        original_last_read_at = channel_member.last_read_at

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = authenticated_client.patch(url)

        assert response.status_code == status.HTTP_200_OK

        channel_member.refresh_from_db()
        assert channel_member.last_read_at > original_last_read_at

    @pytest.mark.django_db
    def test_mark_read_unauthenticated(self, unauthenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = unauthenticated_client.patch(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_mark_read_non_game_member(
        self, authenticated_client_for_tertiary_user, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response = authenticated_client_for_tertiary_user.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_mark_read_non_channel_member_private_channel(
        self, authenticated_client_for_secondary_user, active_game_with_private_channel
    ):
        game = active_game_with_private_channel
        private_channel = Channel.objects.get(game=game, private=True)

        url = reverse("channel-mark-read", args=[game.id, private_channel.id])
        response = authenticated_client_for_secondary_user.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_mark_read_idempotent(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        url = reverse("channel-mark-read", args=[game.id, channel.id])
        response1 = authenticated_client.patch(url)
        assert response1.status_code == status.HTTP_200_OK

        response2 = authenticated_client.patch(url)
        assert response2.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_mark_read_allowed_for_pending_game_member(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        game = pending_game_created_by_secondary_user
        public_channel = game.get_public_press()
        authenticated_client.post(reverse("game-join", args=[game.id]))

        url = reverse("channel-mark-read", args=[game.id, public_channel.id])
        response = authenticated_client.patch(url)

        assert response.status_code == status.HTTP_200_OK


class TestChannelUnreadRetrieveView:

    @pytest.mark.django_db
    def test_unread_count_for_game(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        url = reverse("game-channel-unread", args=[game.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_unread_count_single_query(
        self, authenticated_client, game_with_public_channel_and_messages, django_assert_num_queries
    ):
        game = game_with_public_channel_and_messages
        url = reverse("game-channel-unread", args=[game.id])
        with django_assert_num_queries(1):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_unread_count_unauthenticated(self, unauthenticated_client, game_with_public_channel_and_messages):
        url = reverse("game-channel-unread", args=[game_with_public_channel_and_messages.id])
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_own_messages_not_counted_as_unread(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        channel = Channel.objects.get(game=game, name="Public Press")
        ChannelMessage.objects.create(channel=channel, sender=primary_member, body="Own message")

        url = reverse("game-channel-unread", args=[game.id])
        response = authenticated_client.get(url)

        assert response.data["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_unread_count_resets_after_mark_read(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        authenticated_client.patch(reverse("channel-mark-read", args=[game.id, channel.id]))

        url = reverse("game-channel-unread", args=[game.id])
        response = authenticated_client.get(url)

        assert response.data["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_unread_count_sums_channels_independently(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        secondary_member = game.members.exclude(id=primary_member.id).first()

        private_channel = Channel.objects.create(game=game, name="Private Channel", private=True)
        private_channel.members.add(primary_member, secondary_member)

        ChannelMessage.objects.create(channel=private_channel, sender=secondary_member, body="Private msg")

        public_channel = Channel.objects.get(game=game, name="Public Press")
        authenticated_client.patch(reverse("channel-mark-read", args=[game.id, public_channel.id]))

        url = reverse("game-channel-unread", args=[game.id])
        response = authenticated_client.get(url)

        assert response.data["total_unread_message_count"] == 1

    @pytest.mark.django_db
    def test_unread_count_zero_for_non_member(
        self, authenticated_client_for_tertiary_user, game_with_public_channel_and_messages
    ):
        url = reverse("game-channel-unread", args=[game_with_public_channel_and_messages.id])
        response = authenticated_client_for_tertiary_user.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_unread_message_count"] == 0


class TestGameUnreadListView:

    @pytest.mark.django_db
    def test_lists_games_with_unread_counts(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        url = reverse("game-unread-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [{"game_id": game.id, "total_unread_message_count": 2}]

    @pytest.mark.django_db
    def test_omits_games_without_unread(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")
        authenticated_client.patch(reverse("channel-mark-read", args=[game.id, channel.id]))

        url = reverse("game-unread-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @pytest.mark.django_db
    def test_single_query(
        self, authenticated_client, game_with_public_channel_and_messages, django_assert_num_queries
    ):
        url = reverse("game-unread-list")
        with django_assert_num_queries(1):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client):
        response = unauthenticated_client.get(reverse("game-unread-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_own_messages_not_counted(self, authenticated_client, game_with_public_channel_and_messages):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        channel = Channel.objects.get(game=game, name="Public Press")
        ChannelMessage.objects.create(channel=channel, sender=primary_member, body="Own message")

        response = authenticated_client.get(reverse("game-unread-list"))

        assert response.data == [{"game_id": game.id, "total_unread_message_count": 2}]
