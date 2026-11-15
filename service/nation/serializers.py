from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.serializers import AbsoluteUrlField


@extend_schema_field(serializers.URLField(allow_null=True))
class FlagUrlField(AbsoluteUrlField):
    pass


class NationSerializer(serializers.Serializer):
    nation_id = serializers.CharField()
    name = serializers.CharField()
    color = serializers.CharField(read_only=True)
    non_playable = serializers.BooleanField()
    flag_url = FlagUrlField(source="flag_path")


class NationFlagUploadSerializer(serializers.Serializer):
    flag = serializers.FileField(write_only=True)
