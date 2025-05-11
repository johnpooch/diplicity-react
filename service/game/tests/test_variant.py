from django.urls import reverse
from rest_framework import status
from .base import BaseTestCase


class TestVariantList(BaseTestCase):
    def setUp(self):
        super().setUp()

    def create_request(self):
        url = reverse("variant-list")
        return self.client.get(url)

    def test_list_variants_success(self):
        response = self.create_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.variant.id)
        self.assertEqual(response.data[0]["name"], self.variant.name)

    def test_list_variants_unauthenticated(self):
        self.client.logout()
        response = self.create_request()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
