from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import DrawProposal, DrawVote
from .constants import DrawProposalStatus


class DrawVoteMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="user.profile.name")
    picture = serializers.CharField(source="user.profile.picture", allow_null=True)
    nation = serializers.CharField(source="nation.name", allow_null=True)
    is_current_user = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField)
    def get_is_current_user(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.user == request.user
        return False


class DrawVoteSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    member = DrawVoteMemberSerializer(read_only=True)
    included = serializers.BooleanField(read_only=True)
    accepted = serializers.BooleanField(read_only=True, allow_null=True)


class DrawProposalSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    created_by = DrawVoteMemberSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    combined_sc_count = serializers.IntegerField(read_only=True)
    victory_threshold = serializers.IntegerField(read_only=True)
    votes = DrawVoteSerializer(many=True, read_only=True)
    phase_id = serializers.IntegerField(source="phase.id", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    included_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        write_only=True,
    )

    def validate_included_member_ids(self, value):
        game = self.context["game"]
        current_member = self.context["current_game_member"]

        if current_member.id not in value:
            raise serializers.ValidationError(
                "You must include yourself in the draw proposal."
            )

        if len(value) < 2:
            raise serializers.ValidationError(
                "A draw proposal must include at least 2 players."
            )

        active_members = game.members.filter(eliminated=False, kicked=False)
        active_member_ids = set(active_members.values_list("id", flat=True))

        for member_id in value:
            if member_id not in active_member_ids:
                raise serializers.ValidationError(
                    f"Member {member_id} is not an active member of the game."
                )

        return value

    def validate(self, attrs):
        game = self.context["game"]
        current_member = self.context["current_game_member"]
        included_member_ids = attrs.get("included_member_ids", [])

        if game.sandbox:
            raise serializers.ValidationError(
                "Draw proposals are not allowed in sandbox games."
            )

        current_phase = game.current_phase
        existing_proposal = DrawProposal.objects.active().filter(
            game=game,
            created_by=current_member,
            phase=current_phase,
        ).first()

        if existing_proposal:
            raise serializers.ValidationError(
                "You already have an active draw proposal for this phase."
            )

        included_members = game.members.filter(id__in=included_member_ids)
        phase = current_phase
        included_nations = [m.nation for m in included_members]
        combined_sc_count = phase.supply_centers.filter(
            nation__in=included_nations
        ).count()

        victory_threshold = game.variant.solo_victory_sc_count
        if combined_sc_count < victory_threshold:
            raise serializers.ValidationError(
                f"Combined SC count ({combined_sc_count}) must be at least "
                f"the victory threshold ({victory_threshold})."
            )

        return attrs

    def create(self, validated_data):
        game = self.context["game"]
        current_member = self.context["current_game_member"]
        included_member_ids = validated_data["included_member_ids"]

        return DrawProposal.objects.create_proposal(
            game=game,
            created_by=current_member,
            included_member_ids=included_member_ids,
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
