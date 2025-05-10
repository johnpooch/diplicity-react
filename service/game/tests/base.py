from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from game import models

User = get_user_model()


class BaseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.variant = models.Variant.objects.create(
            id="classical",
            name="Classical",
        )
