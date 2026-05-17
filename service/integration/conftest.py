import os

import pytest
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from user_profile.models import UserProfile


@pytest.fixture(autouse=True)
def _shadow_strict(settings):
    """Opt-in strict shadow mode for the integration suite. With SHADOW_STRICT
    set in the environment, every resolve() turns a shadow divergence into a
    raised ShadowDivergenceError, so the integration tests enforce Python
    adjudicator correctness. Without it the suite stays green by default."""
    if os.getenv("SHADOW_STRICT"):
        settings.SHADOW_STRICT = True


@pytest.fixture(scope="session")
def _extra_users(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        users = []
        for i in range(4, 8):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="testpass123",
            )
            UserProfile.objects.create(user=user, name=f"User {i}", picture="")
            users.append(user)
        return users


@pytest.fixture(scope="session")
def authenticated_clients_4_through_7(_extra_users):
    clients = []
    for user in _extra_users:
        client = APIClient()
        client.force_authenticate(user=user)
        clients.append(client)
    return clients
