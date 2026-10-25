---
paths:
  - "service/**/*.py"
---

# Backend conventions (`service/`)

The service is large rather than complex, so almost all of it is built from a small set of named patterns. Each pattern is a base class with a few declarations, in a file named after the pattern. A reader should be able to tell what a piece of code does, and what it is allowed to do, from the file it is in and the class it extends. Code that does not fit a pattern is raised as a discussion in the PR description, not introduced as a new shape.

Two principles decide where logic goes. The backend makes every business decision and the response carries the decision itself, so the frontend only renders: a game response says whether the user can join, rather than giving the client the fields to work it out. And each layer has one responsibility, described in the sections below.

## App layout

An app adds each of these files only when it has something to put in it:

- `models.py` holds fields and derived properties.
- `query.py` holds the QuerySet and prefetch building blocks.
- `filters.py` holds FilterSets.
- `policies.py` holds the policy mixin.
- `lifecycle.py` holds state transitions.
- `builders.py` holds builders.
- `commands.py` holds commands.
- `loaders.py` holds loaders.
- `hydrators.py` holds hydrators.
- `timers.py` holds timers.
- `serializers.py`, `views.py`, `urls.py`, `tasks.py` and `admin.py` keep their usual Django and DRF meaning.
- `factories.py` holds factory_boy factories, and `tests/` holds the tests.

The base class for each pattern lives in `common/`, one module per pattern. Views, serializers, commands and URL routes live in the app that owns the model being acted on, even when the feature that triggers them belongs to another app. A parent app may `include()` another app's urlpatterns to keep a nested public path.

## Models

A model declares fields, then `class Meta`, then `@property` methods for derived values. Plain methods that calculate a value from the row and their arguments may follow the properties. A model method never writes: writes belong to lifecycle transitions, builders and commands. Behaviour that is not a fact about the row comes from mixins, each in its own file:

```python
class Game(GameLifecycle, GamePolicy, TimedModel, SuffixedSlugIdMixin, BaseModel):
    objects = GameManager()
```

Every model inherits from `BaseModel`, which provides `created_at` and `updated_at`.

A property reads related rows through `.all()` and derives what it needs in Python. It never calls `.filter()`, `.order_by()`, `.count()` or `.exists()` on a relation, because those bypass the prefetch cache and issue a query per instance. `.all()` reads the prefetch cache when one exists, so a property needs no "use the prefetched rows if present" branch. Loaders are responsible for the data being there.

Encode identity with one discriminant, such as a `kind` enum, rather than parallel flags or checks for a related row, and expose convenience checks as properties (`is_bot`). Record a state change as a nullable `<event>_at` timestamp read through a boolean property, not as a boolean field, because a timestamp records when as well as whether. Derive a value that other rows already determine instead of storing a copy that has to be kept in sync. Store a value only when nothing else can reproduce it.

A human-readable primary key comes from `SuffixedSlugIdMixin`, which builds a slug from a source field plus a short random suffix. The suffix means no id is ever issued twice, including after the row it belonged to is deleted. A recycled id would let a request holding a stale one act on an unrelated row.

Do not use signals for domain behaviour. Behaviour that follows from a save is declared on the model, as `TimedModel` does for timers, so it is visible where the model is defined.

Do not add manual tracing spans. Automatic instrumentation covers requests and queries.

A user upload lives in its own model with a sha256 `content_hash` of the stored bytes, and is served by a hash-keyed view with `Cache-Control: immutable`. Payloads are stored in Postgres, never on the filesystem, because the container filesystem is ephemeral and a mounted volume stops Railway from overlapping deploys. A binary payload goes in a separate one-to-one model so that querysets which `select_related` the upload for its hash do not load the bytes.

## QuerySets and managers

The QuerySet lives in `query.py`. The manager is `models.Manager.from_queryset(GameQuerySet)` and declares no methods of its own, so nothing is written twice.

QuerySet methods describe rows, never a consumer. A filter is a plain noun or adjective phrase with no prefix, such as `players()`, `musterable()`, `joined_by(user)` or `visible_to(user)`. An annotation is named `with_<field>()`, such as `with_unread_count(user)`. Nothing on a QuerySet is named after an endpoint or serializer; the shape a response needs is a loader's job.

A QuerySet method earns its place by encapsulating something a caller would otherwise get wrong: an access rule, a multi-clause condition, a correlated annotation. A one-line `.filter(field=value)` wrapper does not; call `.filter()` directly. Delete methods that have no callers.

Access rules, meaning which rows a user may see or act on, are QuerySet methods so that views, filters and tasks share one definition.

Prefetch strategies are built from module-level functions in `query.py` that return `Prefetch` objects, and loaders compose them. They are not chained QuerySet methods, because Django rejects the same lookup prefetched with two different querysets.

Never select a latest row per parent with a global subquery inside a `Prefetch`. The subquery is not correlated to the prefetched parents, so it scans every parent's children on every request. Prefetch the children and derive the latest ones in Python once the page is known, which is what hydrators are for.

## Filters

A FilterSet maps query parameters to QuerySet methods, one line per parameter. It holds no query logic of its own. Defaults, such as excluding sandbox games unless asked for, are declared in the FilterSet. Views never parse query parameters.

## Policies

Each model that has user-dependent decisions has a policy mixin in `policies.py`. A policy method takes the user and returns a `Decision`:

```python
@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str | None = None

    def __bool__(self):
        return self.allowed
```

A denied decision carries a reason constant when the user can be told why. Policy methods share a memoized `member_for(user)` rather than each scanning the game's members. A `Member` is not necessarily a player, so a policy checks `kind` wherever the distinction matters. Policy methods read only loaded data.

Each rule is written once, in the policy. Permission classes, serializer fields and the `actions` list all read the policy method. Serializer validation, FilterSets and the frontend do not re-implement a policy rule.

A permission for a policy rule is generated, never hand-written: `permission_classes = [IsAuthenticated, allows("can_pause")]`. The generated class resolves the object from the URL, and turns a denied decision into a 403 with the reason as the error code. Hand-written permission classes exist only for rules that do not belong to a model's policy, such as a user-level capability, and live in `common/permissions.py`.

A request that is not allowed because of the state of the resource is a denied decision and returns 403 with a reason. A request whose payload is invalid fails serializer validation and returns 400. Never check one condition in both places, because the status code then depends on which layer runs first.

## Lifecycle

State transitions are decorated methods in a lifecycle mixin in `lifecycle.py`. The state is the existing `status` field; there is no transition table.

```python
class GameLifecycle:
    @transition(source=(GameStatus.PENDING, GameStatus.MUSTERING), target=GameStatus.ACTIVE, stamp="started_at")
    def start(self):
        ...
```

The decorator refuses to run a transition whose source does not match, sets the target status and the `<event>_at` stamp, and saves the fields it changed. A change that is not a status change, such as pausing, uses a `guard` instead of a source and target. Policies ask whether a transition is available through the decorator rather than repeating its conditions.

A transition may write the rows its new state requires to be consistent. It knows nothing about the request: it takes no actor, emits no events, and schedules nothing. Timers react to the saved state.

## Builders

A builder constructs one consistent set of related rows. Builders live in `builders.py`, and each starting point is a named class method:

```python
GameBuilder.from_template(variant, **fields)
GameBuilder.from_phase(phase, **fields)
```

The `Builder` base class runs `build()` inside `transaction.atomic()`, so no builder manages its own transaction. A builder has no actor, checks no permissions, emits no events and runs no transitions. It returns the root instance. It does not stash related objects on the instance for the caller to pick up.

## Commands

Every write use case is a command in `commands.py`. A command extends a base class that owns the sequence: open a transaction, lock the target row with `select_for_update()`, re-check the policy decision against the locked row, perform the work, emit events, and return the instance.

```python
class PauseGame(GameCommand):
    decision = "can_pause"
    events = ["game_paused"]

    def perform(self, game):
        game.pause()
```

Commands call builders and transitions. They hold use-case policy that is not a user decision, such as capping how many sandbox games a user keeps. Only commands call `emit`. Models, builders, transitions, serializers and views never emit.

The lock and re-check matter most for deletes. Django cascades deletes in Python, so an unlocked delete collects children in one snapshot and removes them in another, and anything committed in between survives and makes the transaction fail at commit.

## Timers

A job that should run at a time derived from a row is a timer. A timer extends `Timer` in the app's `timers.py` and declares what varies: the task name, the field holding the job id, the job statuses that count as live, the QuerySet method that decides whether the row is eligible, an optional lock, and `run_at`.

```python
class MusterTimer(Timer):
    task = "game.start_if_mustered"
    job_id_field = "muster_job_id"
    live_statuses = (TODO, DOING)
    eligible = "musterable"

    def lock(self, game):
        return lock_for_game(game.pk)

    def run_at(self, game):
        return NOW if game.is_mustered() else game.muster_deadline
```

`run_at` returns a datetime, `NOW` to run immediately, or `None` when no job should exist. `Timer.sync()` reconciles procrastinate with that answer: it keeps a live job already scheduled for the same time, and otherwise cancels the current job, queues a new one and stores its id.

A model declares its timers with `timers = (...)` and mixes in `TimedModel`, which syncs them after each save. Code that changes other rows in a way that affects a timer, such as confirming orders, calls `instance.sync_timers()`.

Every task re-checks the state of its row and does nothing if the state no longer applies. That makes a stale job harmless, so cancelling is an optimisation rather than a correctness requirement.

## Loaders and hydrators

A loader declares how the data for one output serializer is loaded. It lives in `loaders.py` and declares a base queryset, built from the prefetch building blocks in `query.py`, and a list of hydrators:

```python
class GameListLoader(Loader):
    queryset = game_list_queryset
    hydrators = [LatestPhaseStates, CurrentBoard, UnreadCounts, CommitmentTotals]
```

The output serializer names its loader, and a view mixin runs it for retrieves, for each list page, and for the response a command returns. A write endpoint returning a serializer therefore loads exactly what the read endpoint for that serializer loads.

A hydrator attaches values to instances after the page is known, using one set-based query over the page. It lives in `hydrators.py` in the app that owns the data it reads, and it sets the value on every instance, zero included. Per-user and per-row values belong in hydrators rather than in annotations on a paginated queryset, because the base queryset is what filtering, ordering and the pagination count run over.

Serialization runs under `queries_disabled()`, so a query issued while rendering a response raises. A serializer never has a fallback query for data that was not loaded; the loader is fixed instead.

A polled GET mixes in `ConditionalGetMixin`, which hashes the rendered body into an ETag and answers an unchanged poll with an empty 304. A polled response must not contain values that change on their own between polls, such as a countdown in seconds. Where building the body is expensive, the view may answer from a precomputed fingerprint instead, and that fingerprint is derived from the loader: a hash of `.values()` over each queryset the loader declares, scoped as the response scopes them, plus the requester's id, the request host when the body holds absolute URLs, and the hydrated values. Bump the fingerprint's version salt when the serializer changes what it derives from the same rows. Each input to the fingerprint has a test that changing it returns a 200 with a new ETag.

A GET whose response depends only on a completed phase of a non-sandbox game mixes in `CompletedPhaseCacheMixin`, but only when the response is identical for every user. The client must tolerate the previous response shape for a week after a serializer change, because browsers do not revalidate within `max-age`.

## Serializers

An output serializer is a `ModelSerializer` with an explicit `fields` tuple, never `"__all__"`. Taking fields from the model gives the schema real enums and nullability, and the committed OpenAPI schema shows any newly exposed field in the PR diff.

A field backed by a policy method or another method that takes the user is a `ViewerField`, which calls the method with the requesting user and declares its schema type:

```python
can_leave = ViewerField(serializers.BooleanField(), anonymous=False)
```

A property is a plain read-only field with a `source`. `SerializerMethodField` is reserved for composing values that need serializer context, such as an absolute URL. Serializers make no business decisions; a value like an order status is a policy or model method exposed through a field.

Decisions reach the client as an `actions` list of `{key, blocked_reason}` built from policy decisions. New decisions are added as actions, not as new `can_*` booleans. Existing `can_*` fields stay, derived from the same `Decision`, until store metrics show the mobile builds that read them are gone. Shipped clients fail on an action key or blocked reason they do not know, so a new key ships only after a released client ignores unknown keys.

An output serializer may extend another when its response is a strict superset of the other's, as a retrieve response is of a list response.

An input serializer declares and validates the payload. It may be a `ModelSerializer` for its field declarations, but it never overrides `create()` or `update()` to run a workflow; the view passes the validated data to a command. Use `validate_<field>` for a check on one field and `validate()` for a check that needs several. The choice decides the error shape clients see, so moving a check between them is an API change.

Serializer class names become OpenAPI component names and generated type names, so renaming a serializer is a codegen change.

## Views

Views are DRF generic views made of declarations: permission classes, an input serializer, an output serializer, a command, a FilterSet, a pagination class. A view overrides no methods.

```python
class GamePauseView(CommandUpdateView):
    """Pause an active game."""

    permission_classes = [IsAuthenticated, allows("can_pause")]
    command = PauseGame
    output_serializer_class = GameRetrieveSerializer
```

The generic decides the method and status code: creating is a create view, changing an existing row is an update view whatever the operation is called, and removing a row is a destroy view. Every view has a docstring, because drf-spectacular extracts it into the schema. A view serving reads and writes on one path branches on `request.method in permissions.SAFE_METHODS`, never on `== "GET"`, because Django routes HEAD to the GET handler.

Ordinary CRUD uses the resource path: list and create on the collection, retrieve, update and delete on the instance. An operation beyond CRUD uses an explicit subpath, such as `…/join/`. Never delete a path that has shipped. The iOS and Android apps each bundle their own copy of the web app and call the paths it was generated against, so a removed path breaks every install until users update. A renamed path keeps the old one serving the same view through a subclass marked `@extend_schema(exclude=True)`, registered with a `-legacy` URL name and covered by a test that requests the literal old path.

## Tests

Tests are the behavioural spec of the service. Each app has a `tests/` package with one module per endpoint, and each module has one test class named after the endpoint. Test names state the guarantee: `test_manager_can_pause_active_game`, `test_player_cannot_pause_game`, `test_cannot_pause_paused_game`. Reading the output of `pytest --collect-only -q` should give an accurate account of how the service behaves.

A test arranges state with factories, acts through the API using `reverse()` and the shared client fixtures, and asserts on the response or on a later API read. It does not call models, QuerySets, commands or loaders directly, and does not assert on database rows the API does not expose. A test is a few lines long. When one needs more than a few lines of setup, the factory needs a trait.

Each app defines factory_boy factories in `factories.py`, and tests import them directly. States are traits, such as `GameFactory(active=True, paused=True)`. A trait for a state that the service reaches through a builder or transition goes through that builder or transition, with the adjudicator stubbed, so a factory cannot produce a state the service could not reach. Factories are for tests only and are never imported by production code.

`conftest.py` holds actors, meaning users and authenticated clients, and infrastructure fixtures such as the in-memory procrastinate app, `assert_notification` and immediate `on_commit`. It holds no scenario fixtures.

The base classes in `common/` are tested once, at their own entry points: the `Timer` reconcile behaviour, the command sequence, loaders running under `queries_disabled()`, `ViewerField` and `allows()`. App tests assert the behaviour these produce through the API and do not re-test the machinery. The same applies to apps with no views of their own, such as `notification`, `emit` and `email_service`.

Each read endpoint has a query-count test that compares two equivalent requests over different numbers of rows and asserts the counts are equal.

For each endpoint, walk the axes that change the outcome, one focused test per edge: each mode or configuration that alters behaviour, side effects and the absence of side effects, unauthenticated users and every distinct forbidden role, boundary inputs, missing resources, and the states that forbid the action. An action that causes a notification asserts it with `assert_notification`.

## Domain rules

A `Member` is a participant in a game, not necessarily a player. A game master holds a member row with no nation, no phase state and no seat counted against the variant. Anything that means player, such as seat counting, nation assignment, phase states, draws, victory and abandonment, goes through `players()`, and every new query over a game's members decides which it means.

A seat nobody is playing is vacant, whatever the reason. Civil disorder, removal and withdrawal all leave a seat vacant until it is replaced. Seat mechanics key off `vacant` and `occupied`, never off the departure fields directly. A replaced member is not vacant, because it no longer holds the seat, and is excluded with `not_replaced()`. `left_seat` is not the complement of `vacant`: a member in civil disorder or withdrawn is vacant but still holds the seat. Departure timestamps are never cleared, except that civil disorder is cleared when elimination lands in the same resolution. Civil disorder is permanent.

Commitment is an append-only log of events. An entry records only its kind, and its points come from the event constants. Totals and squares are sums over entries and are never stored. Write an event through `CommitmentEntry.objects.record()`, which skips private, sandbox and non-human members. Bands and shades come from the backend, never from the client. A player's lifetime total is hydrated per player, never annotated per member row.

## Operational constraints

Imports go at module top level. A genuine circular import is broken with `apps.get_model()`, and an inline import is called out in the PR description.

Constants live in `common/constants.py` and are referenced by class attribute, never by raw string.

Deploys overlap: the previous release keeps serving until the new container passes its health check, and the new container migrates before it serves. Add schema before code reads it. Drop or rename a column only in a deploy after the one that stops reading it; a field counts as read while it is in Django state, so dropping one takes two deploys, the first using `SeparateDatabaseAndState` and giving a `NOT NULL` column a database default. Add an index to a live table with `AddIndexConcurrently` in a migration with `atomic = False`.

`logger.error` creates a Sentry event against a small monthly quota, so reserve it for failures someone must act on and log expected outcomes at `warning` or below. Log with `%`-style arguments, never f-strings, because Sentry groups events by the unformatted template. Trace sampling lives in `project/sentry.py`. Honeycomb sampling is decided by trace ID identically in `project/otel_config.py` and `packages/web/src/observability.ts`, so change both together.

Player notifications go out over push only. Email is sent only in the authentication flow, with bodies in `email_service/templates.py`. Notification copy follows `.claude/rules/backend/notification-copy.md`, and codegen reproducibility is covered by `.claude/rules/backend/codegen.md`.
