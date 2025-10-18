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


class TestUserProfileUpdateView:

    @pytest.mark.django_db
    def test_update_user_profile_name_success(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        new_name = "Updated Name"
        response = authenticated_client.patch(url, {"name": new_name}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == new_name
        primary_user.profile.refresh_from_db()
        assert primary_user.profile.name == new_name

    @pytest.mark.django_db
    def test_update_user_profile_name_too_short(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "A"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_numbers(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name123"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_special_chars(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "Name@#$"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    @pytest.mark.django_db
    def test_update_user_profile_name_with_valid_chars(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        valid_names = ["Mary-Jane", "O'Brien", "Jean-Pierre", "María García"]

        for name in valid_names:
            response = authenticated_client.patch(url, {"name": name}, format="json")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["name"] == name

    @pytest.mark.django_db
    def test_update_user_profile_unauthenticated(self, unauthenticated_client):
        url = reverse("user-profile-update")
        response = unauthenticated_client.patch(url, {"name": "New Name"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_update_user_profile_strips_whitespace(self, authenticated_client, primary_user):
        url = reverse("user-profile-update")
        response = authenticated_client.patch(url, {"name": "  Trimmed Name  "}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Trimmed Name"
