import pytest
from django.contrib.auth import get_user_model

from common.builders import Builder

User = get_user_model()

pytestmark = pytest.mark.django_db


class FailingBuilder(Builder):
    def build(self):
        User.objects.create(username=self.fields["username"])
        raise RuntimeError("halfway")


class UserBuilder(Builder):
    def build(self):
        return User.objects.create(username=self.fields["username"])


class TestBuilder:
    def test_returns_built_root(self):
        assert UserBuilder(username="built").run().username == "built"

    def test_failed_build_leaves_no_rows(self):
        with pytest.raises(RuntimeError):
            FailingBuilder(username="half-built").run()
        assert not User.objects.filter(username="half-built").exists()
