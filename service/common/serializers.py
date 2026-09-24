from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    pass


class ExpectedPhaseSerializer(serializers.Serializer):
    expected_phase_id = serializers.IntegerField(write_only=True, required=False)

    def validate_expected_phase_id(self, value):
        if value != self.context["phase"].id:
            raise serializers.ValidationError("This phase is no longer the current phase.")
        return value
