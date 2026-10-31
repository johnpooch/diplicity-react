from rest_framework import serializers

from common.serializers import OutputSerializer

from .constants import ReportReason
from .loaders import ReportLoader
from .models import Report


class ReportReasonSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES, read_only=True)
    label = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class ReportMemberInputSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES)
    note = serializers.CharField(
        max_length=1000, allow_blank=True, required=False, default=""
    )

    def validate(self, attrs):
        if attrs["reason"] == ReportReason.OTHER and not attrs["note"].strip():
            raise serializers.ValidationError(
                {"note": "Add a note explaining what happened."}
            )
        return attrs


class ReportOutputSerializer(OutputSerializer):
    status = serializers.CharField()

    class Meta:
        model = Report
        loader = ReportLoader
        fields = ("id", "reported_member", "reason", "note", "status", "created_at")
