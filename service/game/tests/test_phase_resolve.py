import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock

viewname = "phase-resolve"

@pytest.mark.django_db
def test_resolve_phases_success(unauthenticated_client):
    """
    Test that phase resolution can be triggered without authentication.
    """
    with patch('game.services.phase_service.PhaseService.resolve') as mock_resolve:
        mock_resolve.return_value = {
            "resolved": 2,
            "failed": 0
        }

        url = reverse(viewname)
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["resolved"] == 2
        assert response.data["failed"] == 0
        mock_resolve.assert_called_once()

@pytest.mark.django_db
def test_resolve_phases_with_failures(unauthenticated_client):
    """
    Test phase resolution with some failures.
    """
    with patch('game.services.phase_service.PhaseService.resolve') as mock_resolve:
        mock_resolve.return_value = {
            "resolved": 1,
            "failed": 1
        }

        url = reverse(viewname)
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["resolved"] == 1
        assert response.data["failed"] == 1

@pytest.mark.django_db
def test_resolve_phases_no_due_phases(unauthenticated_client):
    """
    Test phase resolution when no phases are due.
    """
    with patch('game.services.phase_service.PhaseService.resolve') as mock_resolve:
        mock_resolve.return_value = {
            "resolved": 0,
            "failed": 0
        }

        url = reverse(viewname)
        response = unauthenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["resolved"] == 0
        assert response.data["failed"] == 0