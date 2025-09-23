import pytest
from django.urls import reverse
from rest_framework import status


class TestUserProfileRetrieveView:

    @pytest.mark.django_db
    def test_retrieve_user_profile_success(self, authenticated_client, primary_user):
        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == primary_user.profile.name
        assert response.data["picture"] == primary_user.profile.picture
        assert response.data["username"] == primary_user.username
        assert response.data["email"] == primary_user.email

    @pytest.mark.django_db
    def test_retrieve_user_profile_unauthenticated(self, unauthenticated_client):
        url = reverse("user-profile")
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
