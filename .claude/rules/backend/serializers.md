---
paths:
  - "service/**/serializers.py"
---

# Serializers

Use the `serializers.Serializer` base class, not `ModelSerializer`, and declare every field explicitly. `ModelSerializer` hides the API contract and makes it easy to expose a field accidentally when a model changes.

```python
class GameListSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    can_join = serializers.SerializerMethodField()
    variant_id = serializers.CharField(source="variant.id", read_only=True)
    members = MemberSerializer(many=True, read_only=True)

    @extend_schema_field(serializers.BooleanField)
    def get_can_join(self, obj):
        return obj.can_join(self.context["request"].user)
```

Different operations get different serializers: `GameListSerializer`, `GameRetrieveSerializer`, `GameCreateSerializer`, `GamePauseSerializer`.

Validation: `validate_<field>` for anything that depends only on that field; `validate()` when the check needs another field's value. Placement decides the error shape clients see (`{"uid": [...]}` vs `non_field_errors`) — moving a check between them is an API change.

Context keys from mixins: `self.context["request"]`, `self.context["game"]` (`SelectedGameMixin`), `self.context["phase"]` (`SelectedPhaseMixin` / `CurrentPhaseMixin`), `self.context["channel"]` (`SelectedChannelMixin`), `self.context["current_game_member"]` (`CurrentGameMemberMixin`).

Do not use `SerializerMethodField` for a bare attribute pass-through — declare the field with `read_only=True` instead. Reserve `SerializerMethodField` for logic that genuinely depends on serializer context (e.g. `can_join`) or composes model properties (e.g. absolute URL from a model's path property plus `request.build_absolute_uri`).

**Review check:** `serializers.Serializer` base? all fields explicit, with `read_only=True` on computed fields? every `SerializerMethodField` annotated with `@extend_schema_field`? `to_representation` delegates to another serializer when returning a different shape?
