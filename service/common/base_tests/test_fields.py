from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from common.fields import ActionsField, ViewerField
from common.policies import ALLOW, deny


class Viewer:
    is_authenticated = True
    pk = 7


class Room:
    action_decisions = {"enter": "can_enter", "paint": "can_paint"}

    def greeting(self, user):
        return f"hello {user.pk}"

    def can_enter(self, user):
        return ALLOW

    def can_paint(self, user):
        return deny("not_owner")


class ActionSerializer(serializers.Serializer):
    key = serializers.CharField()
    blocked_reason = serializers.CharField(allow_null=True)


class RoomSerializer(serializers.Serializer):
    greeting = ViewerField(serializers.CharField(), anonymous="hello stranger")
    welcome = ViewerField(serializers.CharField(), source="greeting")
    can_enter = ViewerField(serializers.BooleanField(), anonymous=False)
    actions = ActionsField(("enter", "paint"), ActionSerializer)


def _render(user):
    request = APIRequestFactory().get("/")
    request.user = user
    return RoomSerializer(Room(), context={"request": request}).data


class TestViewerField:
    def test_calls_method_with_requesting_user(self):
        assert _render(Viewer())["greeting"] == "hello 7"

    def test_reads_method_named_by_source(self):
        assert _render(Viewer())["welcome"] == "hello 7"

    def test_returns_anonymous_value_without_calling_method(self):
        assert _render(AnonymousUser())["greeting"] == "hello stranger"

    def test_calls_method_for_anonymous_user_without_anonymous_value(self):
        assert _render(AnonymousUser())["welcome"] == "hello None"

    def test_renders_decision_as_boolean(self):
        assert _render(Viewer())["can_enter"] is True


class TestActionsField:
    def test_lists_only_allowed_actions(self):
        assert _render(Viewer())["actions"] == [{"key": "enter", "blocked_reason": None}]

    def test_anonymous_user_has_no_actions(self):
        assert _render(AnonymousUser())["actions"] == []
