from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from common.serializers import OutputSerializer
from member.serializers import BaseMemberSerializer

from .loaders import DrawProposalLoader
from .models import DrawProposal


@extend_schema_serializer(component_name="SpikeDrawVoteMember")
class DrawVoteMemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(source="nation.name", allow_null=True)


@extend_schema_serializer(component_name="SpikeMyVote")
class MyVoteSerializer(serializers.Serializer):
    included = serializers.BooleanField(read_only=True)
    accepted = serializers.BooleanField(read_only=True, allow_null=True)


@extend_schema_serializer(component_name="SpikeDrawVoteUpdate")
class VoteDrawProposalInputSerializer(serializers.Serializer):
    accepted = serializers.BooleanField(required=True)


@extend_schema_serializer(component_name="SpikeDrawProposal")
class DrawProposalOutputSerializer(OutputSerializer):
    created_by = DrawVoteMemberSerializer()
    status = serializers.CharField()
    accepted_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    total_votes = serializers.IntegerField()
    included_member_ids = serializers.ListField(child=serializers.IntegerField())
    my_vote = serializers.SerializerMethodField()
    phase_id = serializers.IntegerField(source="phase.id")
    phase_name = serializers.CharField(source="phase.name")

    class Meta:
        model = DrawProposal
        loader = DrawProposalLoader
        fields = (
            "id",
            "created_by",
            "status",
            "accepted_count",
            "rejected_count",
            "pending_count",
            "total_votes",
            "included_member_ids",
            "my_vote",
            "phase_id",
            "phase_name",
            "created_at",
        )

    @extend_schema_field(MyVoteSerializer(allow_null=True))
    def get_my_vote(self, obj):
        current_member = self.context.get("current_game_member")
        if current_member is None:
            return None
        for vote in obj.votes.all():
            if vote.member_id == current_member.id:
                return {"included": vote.included, "accepted": vote.accepted}
        return None
