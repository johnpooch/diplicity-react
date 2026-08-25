from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class NationSerializer(serializers.Serializer):
    nation_id = serializers.CharField()
    name = serializers.CharField()
    color = serializers.CharField(read_only=True)
    non_playable = serializers.BooleanField()
    flag_url = serializers.SerializerMethodField()

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_flag_url(self, nation) -> str | None:
        path = nation.flag_path
        if path is None:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class NationFlagUploadSerializer(serializers.Serializer):
    flag = serializers.FileField(write_only=True)
