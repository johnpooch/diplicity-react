from rest_framework import serializers

from common.constants import BundlePlatform, UpdateResponseKind
from update.models import Bundle


class UpdateCheckResponseSerializer(serializers.Serializer):
    version = serializers.CharField(required=False)
    url = serializers.CharField(required=False)
    checksum = serializers.CharField(required=False)
    kind = serializers.CharField(required=False)
    message = serializers.CharField(required=False)


class UpdateCheckSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=BundlePlatform.PLATFORM_CHOICES, write_only=True)
    version_build = serializers.CharField(write_only=True)
    version_name = serializers.CharField(write_only=True)

    def create(self, validated_data):
        bundle = Bundle.objects.latest_for(validated_data["platform"], validated_data["version_build"])
        if bundle is None or bundle.version == validated_data["version_name"]:
            return {
                "kind": UpdateResponseKind.UP_TO_DATE,
                "message": "No new bundle available.",
            }
        return {
            "version": bundle.version,
            "url": bundle.url,
            "checksum": bundle.checksum,
        }

    def to_representation(self, instance):
        return UpdateCheckResponseSerializer(instance).data
