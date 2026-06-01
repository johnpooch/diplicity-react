from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import DrawProposal
from .constants import DrawProposalStatus
from member.serializers import BaseMemberSerializer


class DrawVoteMemberSerializer(BaseMemberSerializer):
    nation = serializers.CharField(source="nation.name", allow_null=True)


class MyVoteSerializer(serializers.Serializer):
    included = serializers.BooleanField(read_only=True)
    accepted = serializers.BooleanField(read_only=True, allow_null=True)


class DrawProposalSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    created_by = DrawVoteMemberSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    accepted_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    included_member_ids = serializers.SerializerMethodField()
    my_vote = serializers.SerializerMethodField()
    phase_id = serializers.IntegerField(source="phase.id", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_accepted_count(self, obj) -> int:
        return sum(1 for v in obj.votes.all() if v.accepted is True)

    def get_rejected_count(self, obj) -> int:
        return sum(1 for v in obj.votes.all() if v.accepted is False)

    def get_pending_count(self, obj) -> int:
        return sum(1 for v in obj.votes.all() if v.accepted is None)

    def get_total_votes(self, obj) -> int:
        return len(list(obj.votes.all()))

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_included_member_ids(self, obj):
        return [v.member_id for v in obj.votes.all() if v.included]

    @extend_schema_field(MyVoteSerializer(allow_null=True))
    def get_my_vote(self, obj):
        current_member = self.context.get("current_game_member")
        if current_member is None:
            return None
        for vote in obj.votes.all():
            if vote.member_id == current_member.id:
                return {"included": vote.included, "accepted": vote.accepted}
        return None

    def validate(self, attrs):
        game = self.context["game"]
        current_member = self.context["current_game_member"]

        if game.sandbox:
            raise serializers.ValidationError(
                "Draw proposals are not allowed in sandbox games."
            )

        existing_proposal = DrawProposal.objects.active().filter(
            game=game,
            created_by=current_member,
            phase=game.current_phase,
        ).first()

        if existing_proposal:
            raise serializers.ValidationError(
                "You already have an active draw proposal for this phase."
            )

        return attrs

    def create(self, validated_data):
        game = self.context["game"]
        current_member = self.context["current_game_member"]

        return DrawProposal.objects.create_proposal(
            game=game,
            created_by=current_member,
        )


class DrawVoteUpdateSerializer(serializers.Serializer):
    accepted = serializers.BooleanField(required=True)

    def validate(self, attrs):
        proposal = self.instance
        current_member = self.context["current_game_member"]

        if proposal.status != DrawProposalStatus.PENDING:
            raise serializers.ValidationError(
                "Cannot vote on a proposal that is not pending."
            )

        vote = proposal.votes.filter(member=current_member).first()
        if not vote:
            raise serializers.ValidationError(
                "No vote record found for your membership."
            )

        if vote.accepted is not None:
            raise serializers.ValidationError(
                "You have already voted on this proposal."
            )

        return attrs

    def update(self, instance, validated_data):
        current_member = self.context["current_game_member"]

        vote = instance.votes.filter(member=current_member).first()
        vote.accepted = validated_data["accepted"]
        vote.save()

        try:
            del instance._prefetched_objects_cache
        except AttributeError:
            pass

        if instance.status == DrawProposalStatus.ACCEPTED:
            instance.process_acceptance()

        return instance
