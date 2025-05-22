from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase
from unittest.mock import MagicMock, patch
from game import models


class TestChannelCreate(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)

    def create_request(self, game_id, payload):
        url = reverse("channel-create", args=[game_id])
        return self.client.post(url, payload, content_type="application/json")

    def test_create_channel_success(self):
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        other_member = self.game.members.create(user=self.other_user, nation="France")
        payload = {"members": [other_member.id]}
        response = self.create_request(self.game.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["name"], "England, France")

    def test_create_channel_unauthenticated(self):
        self.client.logout()
        payload = {"members": []}
        response = self.create_request(self.game.id, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_channel_invalid_member(self):
        payload = {"members": [999]}
        response = self.create_request(self.game.id, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestChannelMessageCreate(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        # Create a private channel
        self.private_channel = self.game.channels.create(
            name="Private Channel", private=True
        )
        self.private_channel.members.add(self.game.members.first())
        # Create a public channel
        self.public_channel = self.game.channels.create(
            name="Public Channel", private=False
        )
        # Add another user to the game but not to any channels
        self.other_member = self.game.members.create(
            user=self.other_user, nation="France"
        )

        # Mock the notify task
        self.notify_patcher = patch("game.tasks.notify_task")
        self.mock_notify = self.notify_patcher.start()

    def tearDown(self):
        self.notify_patcher.stop()
        super().tearDown()

    def create_request(self, game_id, channel_id, payload):
        url = reverse("channel-message-create", args=[game_id, channel_id])
        return self.client.post(url, payload, content_type="application/json")

    def test_create_message_in_private_channel_success(self):
        # Set up the member with a nation that exists in the variant
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        payload = {"body": "Hello, world!"}
        response = self.create_request(self.game.id, self.private_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = response.data["messages"][0]
        self.assertEqual(message["body"], payload["body"])
        self.assertEqual(message["sender"]["username"], self.user.username)
        self.assertIn("nation", message["sender"])
        self.assertEqual(message["sender"]["nation"]["name"], "England")
        self.assertTrue(message["sender"]["is_current_user"])

        # Verify the notify task was called with the correct arguments
        self.mock_notify.apply_async.assert_called_once()

    def test_create_message_in_public_channel_as_member_success(self):
        self.public_channel.members.add(self.game.members.first())
        payload = {"body": "Hello in public channel!"}
        response = self.create_request(self.game.id, self.public_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the notify task was called
        self.mock_notify.apply_async.assert_called_once()

    def test_create_message_in_public_channel_as_non_member_success(self):
        # Login as other user who is in game but not channel
        self.client.force_authenticate(user=self.other_user)
        payload = {"body": "Hello from non-member!"}
        response = self.create_request(self.game.id, self.public_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_message_in_private_channel_as_non_member_fails(self):
        # Login as other user who is in game but not channel
        self.client.force_authenticate(user=self.other_user)
        payload = {"body": "This should fail"}
        response = self.create_request(self.game.id, self.private_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_message_empty_body(self):
        payload = {"body": ""}
        response = self.create_request(self.game.id, self.private_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_message_unauthenticated(self):
        self.client.logout()
        payload = {"body": "Hello, world!"}
        response = self.create_request(self.game.id, self.private_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestChannelList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        # Create private channel where user is member
        self.private_member_channel = self.game.channels.create(
            name="Private Member", private=True
        )
        self.private_member_channel.members.add(self.game.members.first())
        # Create private channel where user is not member
        self.private_non_member_channel = self.game.channels.create(
            name="Private Non-Member", private=True
        )
        # Create public channel
        self.public_channel = self.game.channels.create(
            name="Public Channel", private=False
        )
        # Add another user
        self.other_member = self.game.members.create(
            user=self.other_user, nation="France"
        )

    def test_list_channels_as_member(self):
        # Set up the member with a nation that exists in the variant
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        # Create a message from current user
        message = self.private_member_channel.messages.create(
            sender=member, body="Test message"
        )

        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should see private channels they're member of and all public channels
        self.assertEqual(
            len(response.data), 2
        )  # private_member_channel + public_channel

        # Verify channel names
        channel_names = [channel["name"] for channel in response.data]
        self.assertIn("Private Member", channel_names)
        self.assertIn("Public Channel", channel_names)
        self.assertNotIn("Private Non-Member", channel_names)

        # Verify channel content
        for channel in response.data:
            # Find the channel we're looking at
            if channel["name"] == "Private Member":
                # Verify private channel content
                self.assertTrue(channel["private"])
                self.assertEqual(len(channel["messages"]), 1)
                message = channel["messages"][0]
                self.assertEqual(message["body"], "Test message")
                self.assertEqual(message["sender"]["username"], self.user.username)
                self.assertEqual(message["sender"]["nation"]["name"], "England")
                self.assertTrue(message["sender"]["is_current_user"])
            elif channel["name"] == "Public Channel":
                # Verify public channel content
                self.assertFalse(channel["private"])
                self.assertEqual(len(channel["messages"]), 0)

    def test_list_channels_as_non_member(self):
        # Login as other user
        self.client.force_authenticate(user=self.other_user)

        # Create some messages in different channels
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        # Add message to private member channel (should not be visible)
        self.private_member_channel.messages.create(
            sender=member, body="Private message"
        )

        # Add message to public channel (should be visible)
        self.public_channel.messages.create(sender=member, body="Public message")

        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only see public channels
        self.assertEqual(len(response.data), 1)
        channel = response.data[0]

        # Verify channel data
        self.assertEqual(channel["name"], "Public Channel")
        self.assertFalse(channel["private"])
        self.assertEqual(len(channel["messages"]), 1)

        # Verify message data
        message = channel["messages"][0]
        self.assertEqual(message["body"], "Public message")
        self.assertEqual(message["sender"]["username"], self.user.username)
        self.assertEqual(message["sender"]["nation"]["name"], "England")
        self.assertFalse(message["sender"]["is_current_user"])

    def test_list_channels_unauthenticated(self):
        self.client.logout()
        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
