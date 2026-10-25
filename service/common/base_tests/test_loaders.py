import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from common.hydrators import Hydrator
from common.loaders import Loader
from common.serializers import queries_disabled

User = get_user_model()

pytestmark = pytest.mark.django_db


class Greeting(Hydrator):
    attribute = "greeting"
    default = "nobody greeted"

    def values(self, users):
        return {users[0].pk: f"hello {self.user.pk}"}


def all_users():
    return User.objects.order_by("pk")


class UserLoader(Loader):
    queryset = all_users
    hydrators = [Greeting]


class TestLoader:
    def test_queryset_comes_from_declared_function(self, primary_user):
        assert list(UserLoader(AnonymousUser()).get_queryset()) == list(all_users())

    def test_hydrators_set_value_on_every_instance(self, primary_user, secondary_user):
        users = UserLoader(primary_user).hydrate([primary_user, secondary_user])
        assert [user.greeting for user in users] == [f"hello {primary_user.pk}", "nobody greeted"]

    def test_load_returns_hydrated_instance(self, primary_user):
        user = UserLoader(primary_user).load(primary_user.pk)
        assert user.greeting == f"hello {primary_user.pk}"

    def test_viewer_profile_is_loaded_for_rendering(self, primary_user):
        viewer = User.objects.get(pk=primary_user.pk)
        UserLoader(viewer).hydrate([])
        with queries_disabled():
            assert viewer.profile.name == "Primary User"
