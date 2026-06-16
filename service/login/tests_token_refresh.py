import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
def test_token_refresh_with_deleted_user_returns_401(unauthenticated_client):
    user = User.objects.create_user(
        username="tobedeleted@example.com",
        email="tobedeleted@example.com",
        password="testpass123",
    )
    refresh = RefreshToken.for_user(user)
    user.delete()

    url = reverse("token-refresh")
    response = unauthenticated_client.post(
        url, {"refresh": str(refresh)}, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
