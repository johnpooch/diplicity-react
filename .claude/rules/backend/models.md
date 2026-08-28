---
paths:
  - "service/**/models.py"
---

# Models

Two responsibilities: define fields, and define properties for convenient access to related data. All models inherit from `BaseModel` (`service/common/models.py`), which provides `created_at` and `updated_at`.

**Body order:** fields → `class Meta` → `@property` methods → other methods. Never place a property above `class Meta`.

**Encode identity with one discriminant; derive the rest.** Prefer a single `kind` (or similar enum) over parallel flags or “has related row” checks (`hasattr(user, "bot_profile")`). Convenience APIs are `@property` methods on the model (`is_bot`).

**Do not leave unused domain in the schema for a future feature.** If fields are not used yet, remove them and re-add when the feature lands. Absent beats switched-off scaffolding.

Query optimisation belongs on a custom QuerySet, never in a view:

```python
class GameQuerySet(models.QuerySet):
    def with_list_data(self):
        return self.select_related("variant").prefetch_related("members")

    def with_retrieve_data(self):
        return self.with_list_data().prefetch_related("phases")

class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def with_list_data(self):
        return self.get_queryset().with_list_data()

class Game(BaseModel):
    objects = GameManager()
```

```python
# BAD
class GameListView(generics.ListAPIView):
    def get_queryset(self):
        return Game.objects.all().select_related("variant").prefetch_related("members")

# GOOD
class GameListView(generics.ListAPIView):
    queryset = Game.objects.all().with_list_data()
```

Views pick the lightest QuerySet strategy sufficient for their serializer. Complex multi-model creation flows live in Manager methods, not in serializer `create()`.

Use `Prefetch` objects for complex prefetch strategies with custom querysets (e.g. `to_attr="template_phases"`). `GameQuerySet` holds the canonical patterns.

A QuerySet method must earn its place by encapsulating something a caller would otherwise get wrong — a prefetch strategy, a multi-clause access rule, a correlated annotation. A one-line `.filter(field=value)` wrapper is not that; call `.filter()` directly. Delete helpers with no callers rather than keeping them for a future one.

A queryset feeding a serializer must cover every relation that serializer touches, including the ones reached inside a `SerializerMethodField`. `BaseMemberSerializer` reads `user.profile`, and a nested `NationSerializer` reads `nation.flag` — miss either and every member costs extra queries. Assert the count in a test.

A user upload lives in its own model alongside a sha256 `content_hash` of the stored bytes, and is served by a hash-keyed view with `Cache-Control: immutable` rather than from a storage URL — the hash in the path is what makes the response cacheable forever. `NationFlag` and `UserProfilePicture` are the two examples. Binary payloads go through `MEDIA_ROOT`, which points at a mounted volume in production because the container filesystem is ephemeral; text payloads stay in a column.

**Review check:** `select_related` / `prefetch_related` on the QuerySet, not in views? Manager delegates QuerySet methods? complex creation in Manager methods? derived values as `@property`? inherits from `BaseModel`?
