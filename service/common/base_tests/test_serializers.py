import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.serializers import OutputSerializer, QueriesDisabled, queries_disabled

User = get_user_model()

pytestmark = pytest.mark.django_db


class UserSerializer(OutputSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("username", "member_count")

    def get_member_count(self, user):
        return User.objects.count()


class UsernameSerializer(OutputSerializer):
    class Meta:
        model = User
        fields = ("username",)


class TestQueriesDisabled:
    def test_query_inside_block_raises(self):
        with pytest.raises(QueriesDisabled), queries_disabled():
            User.objects.count()

    def test_queries_run_again_after_block(self):
        with queries_disabled():
            pass
        assert User.objects.count() >= 0

    def test_rendering_output_serializer_refuses_queries(self, primary_user):
        with pytest.raises(QueriesDisabled):
            UserSerializer(primary_user).data

    def test_rendering_output_list_refuses_queries(self, primary_user):
        with pytest.raises(QueriesDisabled):
            UserSerializer([primary_user], many=True).data

    def test_rendering_loaded_data_succeeds(self, primary_user):
        assert UsernameSerializer([primary_user], many=True).data == [{"username": primary_user.username}]
