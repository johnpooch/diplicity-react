import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from user_profile.models import UserProfile

User = get_user_model()


@pytest.fixture
def delete_user(db):
    def _create():
        user = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=user, name="Delete User")
        return user

    return _create


@pytest.fixture
def delete_client():
    def _create(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _create
