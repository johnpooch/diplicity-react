import copy

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import get_attribute


class EmptySerializer(serializers.Serializer):
    pass


@extend_schema_field(serializers.CharField(allow_null=True))
class AbsoluteUrlField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        kwargs.setdefault("allow_null", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get("request")
        if request is None or not value.startswith("/"):
            return value
        return request.build_absolute_uri(value)


class HydratedFieldMixin:
    def get_attribute(self, instance):
        return get_attribute(instance, self.source_attrs)


def derived(field, *mixins):
    field_class = type(field)
    schema_kwargs = {
        key: value for key, value in field._kwargs.items() if key != "read_only"
    }
    schema = field_class(*copy.deepcopy(field._args), **copy.deepcopy(schema_kwargs))
    field.__class__ = extend_schema_field(schema)(
        type(field_class.__name__, (*mixins, field_class), {})
    )
    return field


def hydrated(field):
    return derived(field, HydratedFieldMixin)


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
