from unittest.mock import Mock

import pytest
from django.test import RequestFactory
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from common.etag import if_none_match
from common.views import PrecomputedConditionalGetMixin


def _request(header=None):
    factory = RequestFactory()
    if header is None:
        return factory.get("/")
    return factory.get("/", HTTP_IF_NONE_MATCH=header)


class TestIfNoneMatch:

    def test_no_header_does_not_match(self):
        assert if_none_match(_request(), '"abc"') is False

    def test_strong_header_matches_strong_etag(self):
        assert if_none_match(_request('"abc"'), '"abc"') is True

    def test_weak_header_matches_strong_etag(self):
        assert if_none_match(_request('W/"abc"'), '"abc"') is True

    def test_weak_header_matches_weak_etag(self):
        assert if_none_match(_request('W/"abc"'), 'W/"abc"') is True

    def test_different_etag_does_not_match(self):
        assert if_none_match(_request('W/"abc"'), '"def"') is False

    def test_matches_any_entry_in_a_list(self):
        assert if_none_match(_request('W/"abc", "def"'), '"def"') is True

    def test_wildcard_matches(self):
        assert if_none_match(_request("*"), '"abc"') is True

    @pytest.mark.parametrize("header", ["", "not-an-etag"])
    def test_unparseable_header_does_not_match(self, header):
        assert if_none_match(_request(header), '"abc"') is False


def _precomputed_view(fingerprint, handler, permission_classes=(permissions.AllowAny,)):
    class HandlerView(APIView):
        def get(self, request):
            return handler()

    class FingerprintView(PrecomputedConditionalGetMixin, HandlerView):
        def get_fingerprint(self):
            return fingerprint

    FingerprintView.permission_classes = list(permission_classes)
    return FingerprintView.as_view()


def _get(view, header=None):
    factory = APIRequestFactory()
    if header is None:
        return view(factory.get("/"))
    return view(factory.get("/", HTTP_IF_NONE_MATCH=header))


class TestPrecomputedConditionalGetMixin:

    def test_fresh_request_delegates_to_the_handler_with_the_fingerprint_etag(self):
        handler = Mock(return_value=Response({"channels": []}))

        response = _get(_precomputed_view("abc", handler))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"channels": []}
        assert response["ETag"] == '"abc"'
        assert response["Cache-Control"] == "private, no-cache"
        handler.assert_called_once()

    @pytest.mark.parametrize("header", ['"abc"', 'W/"abc"'])
    def test_matching_etag_returns_304_without_running_the_handler(self, header):
        handler = Mock(return_value=Response({"channels": []}))

        response = _get(_precomputed_view("abc", handler), header)

        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.data is None
        assert response["ETag"] == '"abc"'
        assert response["Cache-Control"] == "private, no-cache"
        handler.assert_not_called()

    def test_changed_fingerprint_returns_200_with_the_new_etag(self):
        handler = Mock(return_value=Response({"channels": []}))

        response = _get(_precomputed_view("def", handler), '"abc"')

        assert response.status_code == status.HTTP_200_OK
        assert response["ETag"] == '"def"'
        handler.assert_called_once()

    def test_permissions_run_before_a_matching_etag_is_answered(self):
        handler = Mock(return_value=Response({"channels": []}))

        response = _get(
            _precomputed_view("abc", handler, (permissions.IsAuthenticated,)), '"abc"'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        handler.assert_not_called()
