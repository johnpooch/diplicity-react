from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.serializers import Actions, OutputSerializer
from member.models import Member

from .constants import ReportReason, ReportStatus
from .loaders import ModerationReportLoader, ReportLoader
from .models import Report, ReportReview
from .policies import CanViewReportedGamePolicy


class ReportReasonSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES, read_only=True)
    label = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class ReportMemberInputSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReportReason.REASON_CHOICES)
    note = serializers.CharField(max_length=1000)


class ReportDecisionInputSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=1000, allow_blank=True, default="")


class ReportApproveInputSerializer(ReportDecisionInputSerializer):
    reason = serializers.ChoiceField(
        choices=ReportReason.REASON_CHOICES, required=False
    )


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


class ModerationReviewOutputSerializer(OutputSerializer):
    reviewed_by = ModerationReviewerOutputSerializer()

    class Meta:
        model = ReportReview
        fields = ("reviewed_by", "note", "created_at")


class ModerationReportOutputSerializer(OutputSerializer):
    status = serializers.ChoiceField(choices=ReportStatus.STATUS_CHOICES)
    game_id = serializers.CharField(source="reporter.game_id")
    game_name = serializers.CharField(source="reporter.game.name")
    variant_name = serializers.CharField(source="reporter.game.variant.name")
    reporter = ModerationMemberOutputSerializer()
    reported = ModerationMemberOutputSerializer()
    review = ModerationReviewOutputSerializer(allow_null=True)
    assigned_to = ModerationReviewerOutputSerializer(allow_null=True)
    actions = Actions(
        assign=Report.objects.assign,
        unassign=Report.objects.unassign,
        approve=Report.objects.approve,
        reject=Report.objects.reject,
    )
    can_view_game = serializers.SerializerMethodField()

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
            "review",
            "assigned_to",
            "actions",
            "can_view_game",
        )

    @extend_schema_field(serializers.BooleanField)
    def get_can_view_game(self, report):
        return CanViewReportedGamePolicy.decide(
            report, self.context["request"].user
        ).allowed
