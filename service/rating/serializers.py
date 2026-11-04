from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from common.serializers import OutputSerializer

from .loaders import LeaderboardEntryLoader
from .models import Rating


@extend_schema_serializer(component_name="LeaderboardEntry")
class LeaderboardEntryOutputSerializer(OutputSerializer):
    rank = serializers.IntegerField()
    name = serializers.CharField(source="user.profile.name")
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        loader = LeaderboardEntryLoader
        fields = ("rank", "user_id", "name", "picture", "rating")

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_picture(self, obj):
        return obj.user.profile.picture_url(self.context.get("request"))
