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
        self.channel = self.game.channels.create(name="Test Channel", private=True)
        self.channel.members.add(self.game.members.first())

    def create_request(self, game_id, channel_id, payload):
        url = reverse("channel-message-create", args=[game_id, channel_id])
        return self.client.post(url, payload, content_type="application/json")

    def test_create_message_success(self):
        payload = {"body": "Hello, world!"}
        response = self.create_request(self.game.id, self.channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = response.data["messages"][0]
        self.assertEqual(message["body"], payload["body"])
        self.assertEqual(message["sender"]["username"], self.user.username)

    def test_create_message_empty_body(self):
        payload = {"body": ""}
        response = self.create_request(self.game.id, self.channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_message_unauthenticated(self):
        self.client.logout()
        payload = {"body": "Hello, world!"}
        response = self.create_request(self.game.id, self.channel.id, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestChannelList(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Game 1", status=models.Game.ACTIVE)
        self.channel = self.game.channels.create(name="Test Channel", private=True)
        self.channel.members.add(self.game.members.first())

    def test_list_channels(self):
        url = reverse("channel-list", args=[self.game.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.channel.name)
