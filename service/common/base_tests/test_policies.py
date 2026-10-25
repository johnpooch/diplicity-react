from rest_framework import generics
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate

from common.policies import ALLOW, deny, allows


class Door:
    def __init__(self, decision):
        self.decision = decision

    def can_open(self, user):
        return self.decision


def _respond(decision):
    class DoorView(generics.GenericAPIView):
        permission_classes = [allows("can_open")]

        def get(self, request):
            door = Door(decision)
            self.check_object_permissions(request, door)
            return Response({})

    request = APIRequestFactory().get("/")
    force_authenticate(request, user=object())
    return DoorView.as_view()(request)


class TestAllows:
    def test_allowed_decision_passes(self):
        assert _respond(ALLOW).status_code == 200

    def test_denied_decision_returns_403_with_reason_as_code(self):
        response = _respond(deny("door_locked"))
        assert response.status_code == 403
        assert response.data["detail"].code == "door_locked"

    def test_denied_decision_without_reason_uses_default_code(self):
        response = _respond(deny())
        assert response.status_code == 403
        assert response.data["detail"].code == "permission_denied"
