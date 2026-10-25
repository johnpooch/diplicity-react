import re

from common.slugs import SuffixedSlugIdMixin


class TestSuffixedSlugIdMixin:
    def test_slug_is_built_from_source_with_suffix(self):
        assert re.fullmatch(r"the-big-war-[0-9a-f]{8}", SuffixedSlugIdMixin.suffixed_slug("  The Big War! "))

    def test_same_source_never_issues_the_same_id(self):
        assert SuffixedSlugIdMixin.suffixed_slug("War") != SuffixedSlugIdMixin.suffixed_slug("War")
