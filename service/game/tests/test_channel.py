from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase
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
        self.private_channel = self.game.channels.create(name="Private Channel", private=True)
        self.private_channel.members.add(self.game.members.first())
        # Create a public channel
        self.public_channel = self.game.channels.create(name="Public Channel", private=False)
        # Add another user to the game but not to any channels
        self.other_member = self.game.members.create(user=self.other_user, nation="France")

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

    def test_create_message_in_public_channel_as_member_success(self):
        self.public_channel.members.add(self.game.members.first())
        payload = {"body": "Hello in public channel!"}
        response = self.create_request(self.game.id, self.public_channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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
        self.private_member_channel = self.game.channels.create(name="Private Member", private=True)
        self.private_member_channel.members.add(self.game.members.first())
        # Create private channel where user is not member
        self.private_non_member_channel = self.game.channels.create(name="Private Non-Member", private=True)
        # Create public channel
        self.public_channel = self.game.channels.create(name="Public Channel", private=False)
        # Add another user
        self.other_member = self.game.members.create(user=self.other_user, nation="France")

    def test_list_channels_as_member(self):
        # Set up the member with a nation that exists in the variant
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        # Create a message from current user
        message = self.private_member_channel.messages.create(
            sender=member,
            body="Test message"
        )

        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see private channels they're member of and all public channels
        self.assertEqual(len(response.data), 2)  # private_member_channel + public_channel
        channel_names = [channel["name"] for channel in response.data]
        self.assertIn("Private Member", channel_names)
        self.assertIn("Public Channel", channel_names)
        self.assertNotIn("Private Non-Member", channel_names)

        # Verify nation data and is_current_user in messages
        for channel in response.data:
            for message in channel["messages"]:
                self.assertIn("nation", message["sender"])
                self.assertIn("is_current_user", message["sender"])
                if message["sender"]["username"] == self.user.username:
                    self.assertEqual(message["sender"]["nation"]["name"], "England")
                    self.assertTrue(message["sender"]["is_current_user"])
                else:
                    self.assertFalse(message["sender"]["is_current_user"])

    def test_list_channels_as_non_member(self):
        # Login as other user
        self.client.force_authenticate(user=self.other_user)
        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see public channels
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Public Channel")

    def test_retrieve_private_channel_as_member(self):
        # Set up the member with a nation that exists in the variant
        member = self.game.members.first()
        member.nation = "England"
        member.save()

        # Create a message from current user
        message = self.private_member_channel.messages.create(
            sender=member,
            body="Test message"
        )

        url = reverse("channel-detail", args=[self.game.id, self.private_member_channel.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Private Member")

        # Verify nation data and is_current_user in messages
        for message in response.data["messages"]:
            self.assertIn("nation", message["sender"])
            self.assertIn("is_current_user", message["sender"])
            if message["sender"]["username"] == self.user.username:
                self.assertEqual(message["sender"]["nation"]["name"], "England")
                self.assertTrue(message["sender"]["is_current_user"])
            else:
                self.assertFalse(message["sender"]["is_current_user"])

    def test_retrieve_private_channel_as_non_member_fails(self):
        url = reverse("channel-detail", args=[self.game.id, self.private_non_member_channel.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_public_channel_as_non_member(self):
        # Login as other user
        self.client.force_authenticate(user=self.other_user)
        url = reverse("channel-detail", args=[self.game.id, self.public_channel.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Public Channel")
