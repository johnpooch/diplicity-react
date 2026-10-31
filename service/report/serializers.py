from rest_framework import serializers

from common.serializers import OutputSerializer
from member.models import Member

from .constants import ReportReason, ReportStatus
from .loaders import ModerationReportLoader, ReportLoader
from .models import Report


class ReportReasonSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES, read_only=True)
    label = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class ReportMemberInputSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES)
    note = serializers.CharField(max_length=1000)


class ReportOutputSerializer(OutputSerializer):
    status = serializers.CharField()

    class Meta:
        model = Report
        loader = ReportLoader
        fields = ("id", "reported", "reason", "note", "status", "created_at")


class ModerationMemberOutputSerializer(OutputSerializer):
    name = serializers.CharField(source="user.profile.name", allow_null=True)
    nation = serializers.CharField(source="nation.name", allow_null=True)

    class Meta:
        model = Member
        fields = ("id", "user_id", "name", "nation")


class ModerationReviewerOutputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    name = serializers.CharField(source="profile.name", read_only=True)


class ModerationReportOutputSerializer(OutputSerializer):
    status = serializers.ChoiceField(choices=ReportStatus.STATUS_CHOICES)
    game_id = serializers.CharField(source="reporter.game_id")
    game_name = serializers.CharField(source="reporter.game.name")
    variant_name = serializers.CharField(source="reporter.game.variant.name")
    reporter = ModerationMemberOutputSerializer()
    reported = ModerationMemberOutputSerializer()
    reviewed_by = ModerationReviewerOutputSerializer(
        source="review.reviewed_by", allow_null=True
    )

    class Meta:
        model = Report
        loader = ModerationReportLoader
        fields = (
            "id",
            "reason",
            "note",
            "status",
            "created_at",
            "game_id",
            "game_name",
            "variant_name",
            "reporter",
            "reported",
            "reviewed_by",
        )
