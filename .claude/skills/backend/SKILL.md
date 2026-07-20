---
name: backend
description: Django backend guidance for diplicity-react — views, serializers, models, permissions, constants, transactions, and codegen. Use when implementing or reviewing backend features, modifying the Django service, or debugging API behavior.
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

# Backend Development (`/service/`)

## Architecture

- **Framework**: Django + Django REST Framework
- **API**: RESTful with automatic `snake_case` → `camelCase` conversion
- **Auth**: JWT tokens + Google OAuth
- **DB**: PostgreSQL
- **Background tasks**: Management commands for game resolution

## Style Guide

### Comments

Do not add docstrings or comments — including in tests. Do not annotate assertions to explain their values. When a query-count assertion changes, update the number only.

### Imports

Always place imports at the top of the file. No inline imports inside methods.

For circular imports, use `apps.get_model()` at module level:
```python
from django.apps import apps
Phase = apps.get_model("phase", "Phase")
```

### Business logic location

- **Managers**: complex creation/modification logic (e.g. `Game.objects.create_from_template()`)
- **Serializers**: orchestrate manager calls, handle request-specific logic and validation
- **Views**: thin — only permissions and delegation

### App structure

Each app contains: `models.py`, `serializers.py`, `views.py`, `urls.py`, `conftest.py`, `tests.py`, `admin.py`, `utils.py` (when needed).

## Views

Use DRF generic views. Declare permission classes. Use mixins from `common.views` for shared context. Keep the view body empty of business logic.

```python
# GOOD
class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameRetrieveSerializer
    queryset = Game.objects.all().with_retrieve_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))

class GamePauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GamePauseSerializer

    def get_object(self):
        return self.get_game()

# BAD - business logic in the view body
class GamePauseView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        game = self.get_object()
        if game.is_paused:
            return Response({"error": "Already paused"}, status=400)
        ...
```

**Review check:** using a DRF generic (not raw `APIView`)? permission classes declared (not checked in view body)? view is thin? mixins used for shared context? queryset uses a QuerySet method (`with_list_data()`, etc.)?

## Serializers

Use `serializers.Serializer` base class (not `ModelSerializer`). Declare all fields explicitly.

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

`ModelSerializer` hides the API contract and makes it easy to accidentally expose fields when a model changes. Explicit fields make the contract visible.

Different operations get different serializers: `GameListSerializer`, `GameRetrieveSerializer`, `GameCreateSerializer`, `GamePauseSerializer`, etc.

Validation: `validate_<field>` for field-level, `validate()` for cross-field.

Common context keys from mixins: `self.context["request"]`, `self.context["game"]` (`SelectedGameMixin`), `self.context["phase"]` (`SelectedPhaseMixin`/`CurrentPhaseMixin`), `self.context["channel"]` (`SelectedChannelMixin`), `self.context["current_game_member"]` (`CurrentGameMemberMixin`).

**Review check:** `serializers.Serializer` base? all fields explicitly declared with `read_only=True` on computed fields? `SerializerMethodField`s annotated with `@extend_schema_field`? `to_representation` delegates to another serializer when returning a different shape?

## Models

Two responsibilities: define fields; define properties for convenient access to related data.

**Body order:** fields → `class Meta` → `@property` methods → other methods. Never place a property above `class Meta`.

Query optimisation goes on a custom QuerySet:

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

All models inherit from `BaseModel` (`service/common/models.py`), which provides `created_at` and `updated_at`.

Views pick the lightest QuerySet strategy sufficient for their serializer. Complex multi-model creation flows live in Manager methods (not in serializer `create()`).

**Common mistake — query optimisation in the view:**
```python
# BAD
class GameListView(generics.ListAPIView):
    def get_queryset(self):
        return Game.objects.all().select_related("variant").prefetch_related("members")

# GOOD
class GameListView(generics.ListAPIView):
    queryset = Game.objects.all().with_list_data()
```

**Review check:** `select_related`/`prefetch_related` in QuerySet (not views)? Manager delegates QuerySet methods? complex creation in Manager methods? derived values as `@property`? inherits from `BaseModel`?

## Permissions

Custom permissions live in `service/common/permissions.py`. Each class checks exactly one thing and has a descriptive `message`.

```python
class IsGameMaster(BasePermission):
    message = "Only the Game Master can perform this action."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False
        return member.is_game_master
```

**Check existing classes before creating a new one:**

| Class | Checks |
|---|---|
| `IsActiveGame` | Game status is `ACTIVE` |
| `IsActiveOrCompletedGame` | Status is `ACTIVE`, `COMPLETED`, or `ABANDONED` |
| `IsPendingGame` | Status is `PENDING` |
| `IsGameMember` / `IsNotGameMember` | User is / is not a member |
| `IsActiveGameMember` | Non-eliminated, non-kicked member |
| `IsGameMaster` | User is the game master |
| `IsChannelMember` | Member of the channel (public channels always pass) |
| `IsSpaceAvailable` | Fewer members than variant nations |
| `IsCurrentPhaseActive` | Current phase status is `ACTIVE` |
| `IsUserPhaseStateExists` | User has a phase state for the current phase |
| `IsSandboxGame` / `IsNotSandboxGame` | Game is / is not a sandbox |

**Review check:** checks exactly one concept? composed with other permissions in the view? existing class already covers this?

## Constants

```python
class GameStatus:
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (ABANDONED, "Abandoned"),
    )
```

Reference by class attribute (`GameStatus.ACTIVE`), never by raw string (`"active"`). Constants live in `service/common/constants.py`.

## Database and Transactions

Use `transaction.atomic()` when creating multiple related objects. Use `transaction.on_commit()` for side effects that should only run after a successful commit (e.g. notifications).

```python
def create(self, validated_data):
    with transaction.atomic():
        game = Game.objects.create_from_template(variant, ...)
        game.members.create(user=request.user, is_game_master=True)
        game.channels.create(name="Public Press", private=False)
    return Game.objects.all().with_related_data().get(id=game.id)
```

Use `Prefetch` objects for complex prefetch strategies with custom querysets (e.g. `to_attr="template_phases"`). See `GameQuerySet` for canonical patterns.

## Notifications

Player-facing notifications are triggered from signals, not imperatively. All triggering lives in `notification/signals.py`, expressed with `@on_` transition decorators from `notification/decorators.py` — a `pre_save` capture helper remembers the prior field value, and a decorator fires the receiver only on the transition it names. This mirrors `agent/signals.py` (`capture_phase_status` + `@on_phase_activated`); each receiver reads as "on this transition, notify these recipients with this copy."

```python
pre_save.connect(capture_phase_status, sender=Phase)

@receiver(post_save, sender=Phase)
@on_phase_resolved
def send_phase_resolved_notification(sender, instance, created, **kwargs):
    ...
```

Two rules the pattern depends on:

- **Bulk writes emit no signals.** `bulk_update`, `bulk_create` (partially), and queryset `.delete()` bypass `pre_save`/`post_save`, so any notification wired to those transitions silently never fires. Save per-instance, or emit an explicit signal, whenever the write must notify.
- **Time-based notifications are signal-armed, not swept.** A notification derived from a persisted timestamp (e.g. a deadline) should be scheduled via `schedule_at` when that timestamp is set and re-evaluated at fire time (see `phase/signals.py::arm_deadline_resolution`), not polled by an every-minute cron. Reserve `@app.periodic` sweeps for genuinely open-ended work with no triggering row.

## API Codegen

The OpenAPI schema and TypeScript client are auto-generated:
```bash
docker compose up codegen
```

This runs `manage.py spectacular` + `orval`. To reproduce the committed output byte-for-byte, the generating environment must match production config:
- `DJANGO_DEBUG` must be **off** (otherwise `/api/test-sentry/` is added)
- `FIREBASE_PROJECT_ID` must be **set** (otherwise `/devices/` and `FCMDevice` are removed)

A clean `git diff` in a cloud session (no Firebase, DEBUG off) shows only the `/devices/` + `FCMDevice` removal — that's environmental, not a stale-checkout signal.

After codegen, always run `npx tsc -b --noEmit` in `packages/web` to catch downstream type errors. When codegen adds required fields to an existing type, grep `src/` for inline objects of that type (especially `src/mocks/` and test files) and add the new fields.
