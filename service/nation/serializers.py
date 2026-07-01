from typing import Optional

from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.colorblind import apply_colorblind_palette
from .models import Nation, NationFlag


class NationSerializer(serializers.Serializer):
    nation_id = serializers.CharField()
    name = serializers.CharField()
    color = serializers.SerializerMethodField()
    non_playable = serializers.BooleanField()
    flag_url = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_color(self, nation) -> str:
        mode = self.context.get("colorblind_mode")
        return apply_colorblind_palette(nation.color, mode)

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_flag_url(self, nation) -> Optional[str]:
        try:
            flag = nation.flag
        except NationFlag.DoesNotExist:
            return None
        path = reverse(
            "nation-flag-svg",
            kwargs={
                "variant_id": nation.variant_id,
                "nation_id": nation.nation_id,
                "content_hash": flag.content_hash,
            },
        )
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path


class NationFlagUploadSerializer(serializers.Serializer):
    flag = serializers.FileField(write_only=True)
