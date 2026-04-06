import pytest
from unittest.mock import patch
from django.apps import apps
from django.urls import reverse
from rest_framework import status
from channel.models import Channel

from common.constants import GameStatus


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
    def test_create_channel_sandbox_game_forbidden(self, authenticated_client, sandbox_game):
        url = reverse("channel-create", args=[sandbox_game.id])
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


class TestChannelMessageCreateView:

    @pytest.mark.django_db
    def test_create_message_in_private_channel_success(
        self,
        authenticated_client,
        active_game_with_private_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_notification_to_users.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_as_member_success(
        self,
        authenticated_client,
        active_game_with_public_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        public_channel = Channel.objects.get(game=active_game_with_public_channel, private=False)
        public_channel.members.add(active_game_with_public_channel.members.first())

        url = reverse("channel-message-create", args=[active_game_with_public_channel.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_notification_to_users.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_without_explicit_members(
        self, authenticated_client, game_with_two_members, mock_send_notification_to_users, mock_immediate_on_commit
    ):
        public_channel = Channel.objects.create(game=game_with_two_members, name="Public Press", private=False)

        url = reverse("channel-message-create", args=[game_with_two_members.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_notification_to_users.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_private_channel_notifies_only_channel_members(
        self,
        authenticated_client,
        game_with_two_members,
        mock_send_notification_to_users,
        classical_england_nation,
        mock_immediate_on_commit,
    ):
        private_channel = Channel.objects.create(game=game_with_two_members, name="Private Channel", private=True)
        primary_member = game_with_two_members.members.get(nation=classical_england_nation)
        private_channel.members.add(primary_member)

        url = reverse("channel-message-create", args=[game_with_two_members.id, private_channel.id])
        payload = {"body": "Hello in private channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_send_notification_to_users.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_private_channel_with_multiple_members(
        self,
        authenticated_client,
        game_with_two_members,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
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
        mock_send_notification_to_users.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_with_explicit_members_still_notifies_all(
        self,
        authenticated_client,
        game_with_two_members,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
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
        mock_send_notification_to_users.assert_called_once()

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
    def test_unread_count_per_channel_independence(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        secondary_member = game.members.exclude(id=primary_member.id).first()

        private_channel = Channel.objects.create(game=game, name="Private Channel", private=True)
        private_channel.members.add(primary_member, secondary_member)

        from channel.models import ChannelMessage
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
