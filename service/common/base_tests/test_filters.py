import django_filters
import pytest
from django.contrib.auth import get_user_model
from django.http import QueryDict

from common.filters import FilterSet

User = get_user_model()

pytestmark = pytest.mark.django_db


class UserFilter(FilterSet):
    defaults = {"is_active": "true"}

    is_active = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = []


class TestFilterSetDefaults:
    def test_default_applies_when_parameter_is_absent(self, primary_user):
        inactive = User.objects.create(username="inactive", is_active=False)
        assert inactive not in UserFilter(QueryDict(), queryset=User.objects.all()).qs

    def test_parameter_overrides_default(self, primary_user):
        inactive = User.objects.create(username="inactive", is_active=False)
        assert list(UserFilter(QueryDict("is_active=false"), queryset=User.objects.all()).qs) == [inactive]
