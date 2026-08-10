import pytest
from django.test import RequestFactory

from common.etag import if_none_match


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
