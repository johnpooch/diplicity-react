from rest_framework import serializers

from member.serializers import MemberSerializer


class VictorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    winning_phase_id = serializers.IntegerField(source="winning_phase.id", read_only=True)
    members = MemberSerializer(many=True, read_only=True)
