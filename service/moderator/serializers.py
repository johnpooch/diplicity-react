from rest_framework import serializers

from common.serializers import OutputSerializer
from member.models import Member
from report.constants import ReportStatus

from .loaders import ModerationReportLoader
from .models import ModerationReport


class ModerationMemberOutputSerializer(OutputSerializer):
    name = serializers.CharField(source="user.profile.name", allow_null=True)
    nation = serializers.CharField(source="nation.name", allow_null=True)

    class Meta:
        model = Member
        fields = ("id", "user_id", "name", "nation")


class ModerationReportOutputSerializer(OutputSerializer):
    status = serializers.ChoiceField(choices=ReportStatus.STATUS_CHOICES)
    game_id = serializers.CharField(source="reporter.game_id")
    game_name = serializers.CharField(source="reporter.game.name")
    variant_name = serializers.CharField(source="reporter.game.variant.name")
    reporter = ModerationMemberOutputSerializer()
    reported = ModerationMemberOutputSerializer()

    class Meta:
        model = ModerationReport
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
        )
