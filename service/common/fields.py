from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from rest_framework import serializers

from common.policies import Decision

_UNSET = object()


class ViewerField(serializers.Field):
    def __init__(self, field, anonymous=_UNSET, **kwargs):
        self.field = field
        self.anonymous = anonymous
        super().__init__(read_only=True, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        self.field.bind(field_name, parent)

    def get_attribute(self, instance):
        user = self.context["request"].user
        if not user.is_authenticated and self.anonymous is not _UNSET:
            return self.anonymous
        value = self.value_for(instance, user)
        if isinstance(value, Decision):
            return value.allowed
        return value

    def value_for(self, instance, user):
        return getattr(instance, self.source)(user)

    def to_representation(self, value):
        return self.field.to_representation(value)


class ActionsField(ViewerField):
    def __init__(self, keys, child, **kwargs):
        self.keys = keys
        super().__init__(child(many=True), anonymous=[], **kwargs)

    def value_for(self, instance, user):
        return [
            {"key": key, "blocked_reason": None}
            for key in self.keys
            if getattr(instance, instance.action_decisions[key])(user)
        ]


class ViewerFieldExtension(OpenApiSerializerFieldExtension):
    target_class = ViewerField
    match_subclasses = True

    def map_serializer_field(self, auto_schema, direction):
        return auto_schema._map_serializer_field(self.target.field, direction)
