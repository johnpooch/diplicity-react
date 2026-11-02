from rest_framework import serializers


class EmptySerializer(serializers.Serializer):
    pass


class Actions(serializers.ListField):
    def __init__(self, **commands):
        self.policies = {key: command.policy for key, command in commands.items()}
        reasons = sorted(
            set().union(*(policy.reasons() for policy in self.policies.values()))
        )
        self.action_class = type(
            "Action",
            (serializers.Serializer,),
            {
                "key": serializers.ChoiceField(choices=list(commands)),
                "blocked_reason": serializers.ChoiceField(
                    choices=reasons, allow_null=True
                ),
            },
        )
        super().__init__(child=self.action_class(), source="*", read_only=True)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        self.action_class.__name__ = (
            type(parent).__name__.removesuffix("OutputSerializer") + "Action"
        )

    def to_representation(self, instance):
        actor = self.context["request"].user
        return [
            {"key": key, "blocked_reason": policy.decide(instance, actor).reason}
            for key, policy in self.policies.items()
        ]


class OutputSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields
