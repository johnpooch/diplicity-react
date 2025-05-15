from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase


class TestUserProfileRetrieve(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("user-profile")

    def test_retrieve_user_profile_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.user.profile.name)
        self.assertEqual(response.data["picture"], self.user.profile.picture)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)

    def test_retrieve_user_profile_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
