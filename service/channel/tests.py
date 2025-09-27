import pytest
from django.urls import reverse
from rest_framework import status
from channel.models import Channel


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
        from django.apps import apps

        Game = apps.get_model("game", "Game")

        inactive_game = Game.objects.create(
            name="Inactive Game",
            variant=classical_variant,
            status=Game.PENDING,
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
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_list_channels_with_messages(self, authenticated_client, active_game_with_channels):
        url = reverse("channel-list", args=[active_game_with_channels.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        private_channel = next(ch for ch in response.data if ch["name"] == "Private Member")
        assert len(private_channel["messages"]) == 1
        assert private_channel["messages"][0]["body"] == "Test message"
        assert private_channel["messages"][0]["sender"]["is_current_user"] == True


class TestChannelMessageCreateView:

    @pytest.mark.django_db
    def test_create_message_in_private_channel_success(
        self, authenticated_client, active_game_with_private_channel, mock_notify_task
    ):
        private_channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse("channel-message-create", args=[active_game_with_private_channel.id, private_channel.id])
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")

        print(response.data)

        assert response.status_code == status.HTTP_201_CREATED
        mock_notify_task.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_as_member_success(
        self, authenticated_client, active_game_with_public_channel, mock_notify_task
    ):
        public_channel = Channel.objects.get(game=active_game_with_public_channel, private=False)
        public_channel.members.add(active_game_with_public_channel.members.first())

        url = reverse("channel-message-create", args=[active_game_with_public_channel.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_notify_task.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_without_explicit_members(
        self, authenticated_client, game_with_two_members, mock_notify_task
    ):
        public_channel = Channel.objects.create(game=game_with_two_members, name="Public Press", private=False)

        url = reverse("channel-message-create", args=[game_with_two_members.id, public_channel.id])
        payload = {"body": "Hello in public channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_notify_task.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_private_channel_notifies_only_channel_members(
        self, authenticated_client, game_with_two_members, mock_notify_task, classical_england_nation
    ):
        private_channel = Channel.objects.create(game=game_with_two_members, name="Private Channel", private=True)
        primary_member = game_with_two_members.members.get(nation=classical_england_nation)
        private_channel.members.add(primary_member)

        url = reverse("channel-message-create", args=[game_with_two_members.id, private_channel.id])
        payload = {"body": "Hello in private channel!"}
        response = authenticated_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_notify_task.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_private_channel_with_multiple_members(
        self,
        authenticated_client,
        game_with_two_members,
        mock_notify_task,
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
        mock_notify_task.assert_called_once()

    @pytest.mark.django_db
    def test_create_message_in_public_channel_with_explicit_members_still_notifies_all(
        self,
        authenticated_client,
        game_with_two_members,
        mock_notify_task,
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
        mock_notify_task.assert_called_once()

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
