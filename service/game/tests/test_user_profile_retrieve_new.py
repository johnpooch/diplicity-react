import pytest
from django.urls import reverse
from rest_framework import status

viewname = "user-profile"

@pytest.mark.django_db
def test_retrieve_user_profile_success(authenticated_client, primary_user, primary_user_profile):
    """
    Test that an authenticated user can successfully retrieve their profile.
    """
    url = reverse(viewname)
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == primary_user_profile.name
    assert response.data["picture"] == primary_user_profile.picture
    assert response.data["username"] == primary_user.username
    assert response.data["email"] == primary_user.email

@pytest.mark.django_db
def test_retrieve_user_profile_unauthenticated(unauthenticated_client):
    """
    Test that unauthenticated users cannot retrieve a user profile.
    """
    url = reverse(viewname)
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 