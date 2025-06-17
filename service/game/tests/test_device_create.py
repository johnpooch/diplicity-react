import pytest
from rest_framework import status
from fcm_django.models import FCMDevice

viewname = "device-create"

url = "/devices/"

@pytest.mark.django_db
def test_device_create_unauthenticated(unauthenticated_client):
    """
    Test that unauthenticated users cannot create a device.
    """
    payload = {"registration_id": "test_registration_id", "type": "web"}
    response = unauthenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_device_create_invalid_request(authenticated_client):
    """
    Test that creating a device with invalid request body returns 400.
    """
    response = authenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_device_create_success(authenticated_client):
    """
    Test that an authenticated user can successfully create a device.
    """
    payload = {"registration_id": "test_registration_id", "type": "web"}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["registration_id"] == payload["registration_id"]
    assert response.data["type"] == payload["type"]

@pytest.mark.django_db
def test_device_create_multiple_same_type(authenticated_client):
    """
    Test that creating multiple devices with the same type creates multiple active devices.
    """
    payload1 = {"registration_id": "test_registration_id_1", "type": "web"}
    payload2 = {"registration_id": "test_registration_id_2", "type": "web"}
    
    authenticated_client.post(url, payload1, format="json")
    authenticated_client.post(url, payload2, format="json")
    
    devices = FCMDevice.objects.filter(user=authenticated_client.handler._force_user, type="web")
    assert len(devices) == 2
    assert all(device.active for device in devices)

@pytest.mark.django_db
def test_device_create_same_registration_id(authenticated_client):
    """
    Test that creating devices with the same registration ID but different types creates only one device.
    """
    payload1 = {"registration_id": "test_registration_id", "type": "web"}
    payload2 = {"registration_id": "test_registration_id", "type": "android"}
    
    authenticated_client.post(url, payload1, format="json")
    authenticated_client.post(url, payload2, format="json")
    
    devices = FCMDevice.objects.filter(user=authenticated_client.handler._force_user)
    assert devices.count() == 1

@pytest.mark.django_db
def test_device_create_linked_to_user(authenticated_client):
    """
    Test that created device is linked to the authenticated user.
    """
    payload = {"registration_id": "test_registration_id", "type": "web"}
    authenticated_client.post(url, payload, format="json")
    
    device = FCMDevice.objects.get(user=authenticated_client.handler._force_user)
    assert device.user == authenticated_client.handler._force_user 