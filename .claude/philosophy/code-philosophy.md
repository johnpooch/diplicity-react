# Code Philosophy

## Purpose

This document is a **rubric for AI agents** that implement code and review PRs for the Diplicity React codebase. It defines what makes code well-written in this specific project, with examples drawn from actual files.

It complements `CLAUDE.md` (the developer reference) by adding **evaluative framing** — good/bad examples, common mistakes, and judgment criteria. Where `CLAUDE.md` prescribes "use the Suspense wrapper pattern", this document explains what a well-executed Suspense wrapper looks like and how to judge whether a PR got it right.

Agents should use this rubric when running:
- `/implement-issue` — to write code that meets the bar
- `/review-pr` — to evaluate whether submitted code meets the bar
- `/address-pr-feedback` — to understand the standard being applied
- `/learn-from-pr-review` — to extract principles from human feedback

---

## Core Tenets

These five principles govern all code decisions in this codebase. When in doubt, fall back to these.

### 1. Match existing patterns

The codebase has established conventions for every layer. New code should be indistinguishable from existing code in style and structure. If the existing pattern seems wrong, raise it as a discussion — don't silently deviate.

**Test:** Could a reviewer tell which code is new and which is existing, purely by style? If yes, the new code doesn't match.

### 2. Simplicity is correctness

The right amount of code is the minimum needed for the current requirement. Do not add abstractions, configurability, error handling, or features that aren't needed today. Three similar lines of code is better than a premature helper function.

**Test:** Can any line, function, or file be removed without breaking an acceptance criterion? If yes, it shouldn't be there.

### 3. Observable over internal

Code quality is judged by what it produces (API responses, rendered UI, test assertions) not by internal cleverness. A serializer that returns the right data with explicit field declarations is better than a "clever" one that auto-generates fields.

**Test:** Do the tests assert on observable outcomes (HTTP responses, rendered text, navigation) rather than internal state?

### 4. Evidence over assertion

Every code change should be justified by evidence: a failing test that now passes, a user flow that now works, a performance regression that's resolved. "I think this is better" is not justification.

**Test:** Can the reviewer see the evidence for why this change is correct (test output, before/after, linked issue)?

### 5. Fix, don't suppress

When the linter, type checker, or test framework flags an issue, fix the root cause. Never suppress with `eslint-disable`, `@ts-ignore`, `# noqa`, or `pytest.mark.skip`. The only exception is the well-documented mutation-in-useEffect pattern (see CLAUDE.md).

**Test:** Are there any new suppression comments in the diff? If yes, they need justification.

---

## Part 1: Frontend Patterns

### 1.1 Component Structure

#### Suspense wrapper pattern

Every screen that fetches data uses this two-component pattern: an inner component that assumes data is available, and an outer Suspense wrapper that handles loading and errors.

**Canonical example** (abbreviated from `packages/web/src/screens/Home/MyGames.tsx`):

```tsx
// Inner component — data is guaranteed by Suspense
const MyGames: React.FC = () => {
  const { data: games } = useGamesListSuspense({ mine: true });
  const { data: variants } = useVariantsListSuspense();

  // Data is guaranteed — no optional chaining needed
  games.map(game => ...);

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Component body */}
    </div>
  );
};

// Outer wrapper — handles loading and errors
const MyGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" showUserAvatar />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <MyGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

// Export the wrapper as the public API
export { MyGamesSuspense as MyGames };
```

**What to check in review:**
- Does the inner component use `useXxxSuspense` hooks (not `useXxx`)?
- Is the outer wrapper present with `ScreenContainer`, `ScreenHeader`, `QueryErrorBoundary`, and `Suspense`?
- Is the wrapper exported with the screen name?
- Is the `Suspense` fallback an empty div (not a spinner or skeleton — keep it minimal)?
- Is `QueryErrorBoundary` wrapping `Suspense` (not inside it)?

**Common mistake:**

```tsx
// BAD — missing QueryErrorBoundary
const MyScreenSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="My Screen" />
    <Suspense fallback={<div></div>}>
      <MyScreen />
    </Suspense>
  </ScreenContainer>
);
```

Without `QueryErrorBoundary`, query errors crash the entire page instead of showing the "Try Again" UI in the content area.

#### Prop interfaces

Always provide explicit interface definitions for component props. Infer types for everything else.

```tsx
// GOOD — explicit prop interface, inferred locals
interface GameCardProps {
  game: GameList;
  variant: Variant;
}

const GameCard: React.FC<GameCardProps> = ({ game, variant }) => {
  const playerCount = game.members.length; // inferred as number
  // ...
};
```

```tsx
// BAD — inline prop type
const GameCard: React.FC<{ game: GameList; variant: Variant }> = ({ game, variant }) => {
  // ...
};
```

#### Inline sub-components

Components used in only one place should be defined inline in the same file, not extracted to separate files. The `CreateGame.tsx` file demonstrates this well — `VariantSelector`, `GameMetadataTable`, `CreateStandardGameForm`, and `CreateSandboxGameForm` are all defined in the same file because they're only used there.

**When to extract:** Only when a component is used in two or more screens.

### 1.2 State Management

#### State hierarchy

State has a strict hierarchy. Every piece of state should live at the highest appropriate level:

1. **Backend** — source of truth for all domain data. Never cache domain data in local state.
2. **URL** — navigation state, selected tabs, filters. Use `useSearchParams` and `useParams`.
3. **Local state** — pure UI concerns only (e.g., `isEditingName`, form input before submission).

**What to check in review:**
- Is any domain data stored in `useState`? It should come from React Query.
- Is any navigation-relevant state in `useState`? It should be in the URL.
- Is there a `useEffect` that syncs state? It's probably state that should be derived.

**Good example** — `MyGames.tsx` uses local state for tab selection because it's a pure UI concern (abbreviated):

```tsx
const [selectedStatus, setSelectedStatus] = useState<Status>(() => {
  const firstStatusWithGames = statusPriority.find(status =>
    games.some(game => game.status === status)
  );
  return firstStatusWithGames ?? "active";
});
```

**Good example** — `CreateGame.tsx` puts tab state in the URL because it's shareable (pattern from that file):

```tsx
const [searchParams] = useSearchParams();
// Tab state derived from URL query param
const initialTab = searchParams.get("sandbox") === "true" ? "sandbox" : "standard";
```

#### Mutation dependency gotcha

This is the **single most dangerous footgun** in the frontend codebase. See `CLAUDE.md` — "Mutations in useEffect Dependencies" for the canonical good/bad examples.

**Why this matters for review:** The mutation object from `useXxxMutation()` gets a new reference on every state transition (idle → pending → success/error). Including it in a `useEffect` dependency array creates an infinite loop that is silent in development and catastrophic in production.

This is the **one case** where an `eslint-disable` comment is acceptable. The comment must explain why (`-- mutateAsync is stable`).

**What to check in review:**
- Is any mutation object (not `mutateAsync`) in a `useEffect` dependency array?
- If `mutateAsync` is used inside `useEffect`, is the mutation object excluded from deps with an explanatory eslint-disable comment?

### 1.3 Data Fetching

#### Suspense hooks only

Always use `useXxxSuspense` hooks for reads. Never use the non-suspense variants (`useXxx` without `Suspense`). The Suspense hooks integrate with the Suspense wrapper pattern, guaranteeing data is available in the component.

```tsx
// GOOD
const { data: games } = useGamesListSuspense({ mine: true });
games.map(game => ...); // data is guaranteed

// BAD — non-suspense hook
const { data: games, isLoading } = useGamesList({ mine: true });
if (isLoading) return <Spinner />;
games?.map(game => ...); // must handle undefined
```

#### No optional chaining on Suspense data

Data from Suspense hooks is guaranteed to exist. Optional chaining signals that the developer doesn't trust the Suspense boundary, and it hides potential bugs.

```tsx
// GOOD
const { data: variants } = useVariantsListSuspense();
const variant = variants.find(v => v.id === game.variantId);

// BAD — unnecessary guard
const { data: variants } = useVariantsListSuspense();
const variant = variants?.find(v => v.id === game.variantId);
```

#### Entity data from URL params

When a component needs data for an entity identified by a URL parameter, use `useRequiredParams` and fetch directly. Do not pass data through Context or props from a parent.

```tsx
// GOOD
const { gameId } = useRequiredParams<{ gameId: string }>();
const { data: game } = useGameRetrieveSuspense(gameId);

// BAD — receiving game data through Context
const { game } = useGameContext();
```

React Query handles deduplication — multiple components fetching the same game by ID will share a single request.

### 1.4 Hook Design

Custom hooks live in `packages/web/src/hooks/` and should only be created when:
1. **The same logic is needed in multiple components** (not just "it feels like a hook")
2. **The hook encapsulates a genuine concern** (not just a one-liner wrapper)

Current custom hooks:
- `useRequiredParams` — type-safe route params
- `useMapData` — map rendering data composition
- `use-mobile` — responsive breakpoint detection

**What to check in review:**
- Is the new hook used in more than one place? If not, inline the logic.
- Does the hook do more than wrap a single call? If not, just use the underlying call directly.
- Is the hook in `/hooks/` and exported from the index?

For data fetching, prefer using generated hooks directly (`useGameRetrieveSuspense`, `useGamesListSuspense`) rather than wrapping them in custom hooks.

### 1.5 Forms

All forms use React Hook Form with Zod validation. The canonical example is `CreateGame.tsx`.

**Pattern:**

```tsx
// 1. Define schema
const schema = z.object({
  name: z.string().min(1, "Game name is required"),
  variantId: z.string().min(1, "Please select a variant"),
});

// 2. Derive type from schema
type FormValues = z.infer<typeof schema>;

// 3. Create form with zodResolver
const form = useForm<FormValues>({
  resolver: zodResolver(schema),
  defaultValues: { name: "", variantId: "" },
});

// 4. Use FormField for each field
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="name"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Game Name</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  </form>
</Form>
```

**What to check in review:**
- Is Zod used for validation (not manual validation)?
- Is the type derived from the schema with `z.infer` (not manually duplicated)?
- Does every `FormField` include `FormItem`, `FormLabel`, `FormControl`, and `FormMessage`?
- Is the submit handler wrapped in `form.handleSubmit`?
- Are `defaultValues` provided for all fields?

### 1.6 UI and Styling

#### Component library

Use shadcn/ui components over raw HTML. The codebase uses:
- `Button`, `Input`, `Select`, `Checkbox`, `Tabs` — form elements
- `ScreenContainer`, `ScreenHeader`, `ScreenCard` — page structure
- `Notice` — empty states (see `packages/web/src/components/Notice.tsx`)
- `QueryErrorBoundary` — error handling (see `packages/web/src/components/QueryErrorBoundary.tsx`)

Icons come from `lucide-react`. Do not import from other icon libraries.

#### Tailwind minimalism

Only add Tailwind classes that do something. Question every class:

```tsx
// GOOD — minimal, every class earns its place
<div className="space-y-4">

// BAD — redundant classes
<div className="flex flex-row items-stretch min-w-0 space-y-4">
```

Trust component defaults. shadcn/ui components have sensible defaults — only override when necessary:

```tsx
// BAD — redundant size override on an icon Button
<Button variant="ghost" size="icon" className="h-8 w-8">
  <Settings className="h-4 w-4" />
</Button>

// GOOD — let size="icon" handle dimensions
<Button variant="ghost" size="icon">
  <Settings />
</Button>
```

**What to check in review:**
- Are there Tailwind classes that don't change anything?
- Are icon sizes specified when the default is correct?
- Are there spacing classes where a parent `gap` or `space-y` already handles spacing?

#### Empty states

Use the `Notice` component for empty states. It provides a consistent look with an icon, title, message, and optional actions.

```tsx
// GOOD — using Notice for empty state
<Notice
  title="No staging games"
  message="Go to Find Games to join a game."
  icon={Inbox}
/>

// BAD — ad-hoc empty state
<div className="text-center text-muted-foreground p-8">
  <p>No games found</p>
</div>
```

### 1.7 Testing

Tests use Vitest + Testing Library. Test observable behaviour, not implementation details.

**What to check in review:**
- Do tests assert on rendered output (text, elements) rather than internal state?
- Do tests use `screen.getByText`, `screen.getByRole` (not `container.querySelector`)?
- Are tests structured with clear arrange/act/assert?
- Are similar test cases grouped with `it.each` where appropriate?
- Is each test in its own file, not grouped into a single large test file?

### 1.8 Layout and Routing

Layouts are applied at the **router level**, not within screens. Screens return content only.

```tsx
// GOOD — screen returns content, layout is at router level
const OrdersScreen: React.FC = () => {
  return (
    <div className="flex flex-col h-full">
      <GameDetailAppBar title={<PhaseSelect />} />
      <div className="flex-1 overflow-y-auto">
        <Panel>...</Panel>
      </div>
    </div>
  );
};

// BAD — screen wraps itself in a layout
const OrdersScreen: React.FC = () => {
  return (
    <GameDetailLayout>  {/* Layout should be at router level */}
      <Panel>...</Panel>
    </GameDetailLayout>
  );
};
```

**In Storybook stories**, wrap screens in their layout for proper rendering:

```tsx
const meta = {
  render: () => (
    <GameDetailLayout>
      <OrdersScreen />
    </GameDetailLayout>
  ),
};
```

### 1.9 Error Handling and User Feedback

#### Query errors

Use `QueryErrorBoundary` to handle query errors. It integrates with React Query's error reset mechanism so "Try Again" refetches failed queries.

The boundary goes **outside** `Suspense` — this keeps the screen header visible when an error occurs.

#### Mutation feedback

Show toast feedback for user-triggered mutations:

```tsx
// GOOD — toast on success and error
const handleCreate = async (data: FormValues) => {
  try {
    await createGameMutation.mutateAsync({ data });
    toast.success("Game created successfully");
    navigate(`/game-info/${game.id}`);
  } catch {
    toast.error("Failed to create game");
  }
};
```

**Skip toasts** when the UI provides immediate visual feedback (e.g., a checkbox toggling).

**What to check in review:**
- Does every user-triggered mutation have error handling?
- Are success toasts used for non-obvious outcomes (creation, deletion)?
- Are error toasts present for all `catch` paths?
- Is `mutateAsync` used (not `mutate`) so errors propagate to the try/catch?

---

## Part 2: Backend Patterns

### 2.1 App Structure

Each Django app is responsible for a single domain concept. The standard file layout is:

```
service/<app_name>/
├── models.py          # Data models with QuerySet + Manager
├── serializers.py     # DRF serializers (base Serializer class)
├── views.py           # API views (DRF generics)
├── urls.py            # URL routing
├── conftest.py        # Test fixtures (factory functions)
├── tests.py           # Test cases (or tests/ directory)
├── admin.py           # Django admin
└── utils.py           # Helpers (when needed)
```

**What to check in review:**
- Does the new code live in the correct app?
- Does the app follow the standard file layout?
- Is business logic in the right file? (Models for domain logic, serializers for request orchestration, views remain thin)

### 2.2 Models

#### BaseModel

All models inherit from `BaseModel` (`service/common/models.py`), which provides `created_at` and `updated_at` timestamps.

```python
from common.models import BaseModel

class Game(BaseModel):
    # fields...
```

#### QuerySet → Manager → Model pattern

This is the canonical data access pattern. **Canonical example** (abbreviated from `service/game/models.py`):

```python
class GameQuerySet(models.QuerySet):
    def with_list_data(self):
        # Lightweight prefetches for list endpoints
        return self.select_related("variant", "victory").prefetch_related(
            members_prefetch, victory_members_prefetch, "phases",
        )

    def with_retrieve_data(self):
        # Includes phase_states for single-object retrieval
        return self.select_related("variant", "victory").prefetch_related(...)

    def with_related_data(self):
        # Heaviest — includes units, supply centers, template phases
        # Used after game creation to return fully populated data
        return self.select_related("victory").prefetch_related(...)

class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    # Delegate all QuerySet methods
    def with_list_data(self):
        return self.get_queryset().with_list_data()

    def with_retrieve_data(self):
        return self.get_queryset().with_retrieve_data()

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    # Complex creation logic lives in the Manager
    def create_from_template(self, variant, **kwargs):
        game = self.create(variant=variant, **kwargs)
        # Creates phase, units, supply centers from template
        return game

    def clone_from_phase(self, source_phase, name):
        # Creates a sandbox clone from an existing phase
        game = self.create(variant=source_phase.game.variant, ...)
        return game

class Game(BaseModel):
    objects = GameManager()

    @property
    def current_phase(self):
        phases = list(self.phases.all())
        return phases[-1] if phases else None

    @property
    def is_paused(self):
        return self.paused_at is not None
```

**Key observations:**
- The QuerySet has multiple prefetch strategies of increasing weight (`with_list_data` < `with_retrieve_data` < `with_related_data`). Views choose the lightest strategy sufficient for their serializer.
- The Manager has two creation methods (`create_from_template`, `clone_from_phase`) that encapsulate complex multi-model setup logic.

**What to check in review:**
- Are query optimizations (`select_related`, `prefetch_related`) in the QuerySet, not in views or serializers?
- Does the Manager delegate QuerySet methods?
- Are complex creation flows in Manager methods (not in serializer `create()`)?
- Are derived values exposed as `@property` on the model?
- Does the model inherit from `BaseModel`?

**Common mistake:**

```python
# BAD — select_related in the view
class GameListView(generics.ListAPIView):
    def get_queryset(self):
        return Game.objects.all().select_related("variant").prefetch_related("members")

# GOOD — use the QuerySet method
class GameListView(generics.ListAPIView):
    def get_queryset(self):
        return Game.objects.all().with_list_data()
```

### 2.3 Serializers

#### Serializer base class, not ModelSerializer

All serializers use `serializers.Serializer` with explicit field declarations. Never use `ModelSerializer`.

**Canonical example:** `service/game/serializers.py`

```python
# GOOD — explicit fields, Serializer base, @extend_schema_field on method fields
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

# BAD — auto-generated fields, ModelSerializer base
class GameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"
```

**Why:** Explicit field declarations make the API contract visible in the code. `ModelSerializer` hides the contract behind model introspection, which makes it easy to accidentally expose fields or break the frontend when a model changes.

#### Multiple serializers per model

Different API operations get different serializers. The `Game` model has:
- `GameListSerializer` — for listing games (lightweight)
- `GameRetrieveSerializer` — for retrieving a single game (includes `phase_confirmed`)
- `GameCreateSerializer` — for creating games (writable fields + validation)
- `GamePauseSerializer` — for pausing a game (validation + update logic)

**What to check in review:**
- Is the serializer using `serializers.Serializer` (not `ModelSerializer`)?
- Are all fields explicitly declared?
- Are read-only fields marked with `read_only=True`?
- Are `SerializerMethodField`s annotated with `@extend_schema_field` for OpenAPI generation?
- Does `to_representation` delegate to another serializer when returning a different shape (e.g., `GameCreateSerializer` returns `GameRetrieveSerializer` data)?

#### Validation

Field-level validation uses `validate_<field_name>` methods. Cross-field validation uses `validate()`.

```python
# GOOD — field-level validation
def validate_variant_id(self, value):
    if not Variant.objects.filter(id=value).exists():
        raise serializers.ValidationError("Variant with this ID does not exist.")
    return value

# GOOD — cross-field validation
def validate(self, attrs):
    if attrs["deadline_mode"] == DeadlineMode.FIXED_TIME:
        if not attrs.get("fixed_deadline_time"):
            raise serializers.ValidationError({
                "fixed_deadline_time": "Required when deadline_mode is 'fixed_time'."
            })
    return attrs
```

#### Context from views

Serializers receive context from views via `get_serializer_context()` (provided by view mixins). Common context keys:
- `self.context["request"]` — the DRF request object
- `self.context["game"]` — from `SelectedGameMixin`
- `self.context["phase"]` — from `SelectedPhaseMixin` or `CurrentPhaseMixin`
- `self.context["channel"]` — from `SelectedChannelMixin`
- `self.context["current_game_member"]` — from `CurrentGameMemberMixin`

### 2.4 Views

Views should be thin, delegating to serializers and managers. **Canonical example:** `service/game/views.py`

```python
# GOOD — thin view, delegates everything to serializer and queryset
class GameRetrieveView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameRetrieveSerializer
    queryset = Game.objects.all().with_retrieve_data()

    def get_object(self):
        return get_object_or_404(self.queryset, id=self.kwargs.get("game_id"))


# GOOD — thin view with mixin for context
class GamePauseView(SelectedGameMixin, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMaster]
    serializer_class = GamePauseSerializer

    def get_object(self):
        return self.get_game()
```

**What to check in review:**
- Is the view using a DRF generic (not a raw `APIView`)?
- Are permission classes declared (not checked in the view body)?
- Is the view thin (no business logic)?
- Are view mixins used for shared context (not duplicated `get_object` logic)?
- Is the queryset optimized (using QuerySet methods like `with_list_data()`)?

**Common mistake:**

```python
# BAD — business logic in the view
class GamePauseView(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        game = self.get_object()
        if game.is_paused:
            return Response({"error": "Already paused"}, status=400)
        game.pause()
        # Notification logic here...
        return Response(GameRetrieveSerializer(game).data)
```

The validation and update logic should be in the serializer. The view should only set up permissions and delegate.

### 2.5 Permissions

Custom permission classes live in `service/common/permissions.py`. Each class checks exactly one thing.

**Canonical example:**

```python
class IsActiveGame(BasePermission):
    message = "This game is not active."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        return game.status == GameStatus.ACTIVE


class IsGameMaster(BasePermission):
    message = "Only the Game Master can perform this action."

    def has_permission(self, request, view):
        game_id = view.kwargs.get("game_id")
        game = get_object_or_404(Game, id=game_id)
        member = game.members.filter(user=request.user).first()
        if not member:
            self.message = "User is not a member of the game."
            return False
        if not member.is_game_master:
            self.message = "Only the Game Master can perform this action."
            return False
        return True
```

**Key patterns:**
- Each permission has a descriptive `message` attribute for the error response
- Permissions can update `self.message` for more specific error messages
- Permissions are composed in view `permission_classes` lists: `[IsAuthenticated, IsActiveGame, IsGameMaster]`

**Existing permission classes** (check these before creating new ones):

| Class | Checks |
|---|---|
| `IsActiveGame` | Game status is `ACTIVE` |
| `IsActiveOrCompletedGame` | Game status is `ACTIVE`, `COMPLETED`, or `ABANDONED` |
| `IsPendingGame` | Game status is `PENDING` |
| `IsGameMember` | User is a member of the game |
| `IsNotGameMember` | User is NOT a member of the game |
| `IsActiveGameMember` | User is a non-eliminated, non-kicked member |
| `IsGameMaster` | User is the game master |
| `IsChannelMember` | User is a member of the channel (public channels always pass) |
| `IsSpaceAvailable` | Game has fewer members than variant nations |
| `IsCurrentPhaseActive` | Current phase status is `ACTIVE` |
| `IsUserPhaseStateExists` | User has a phase state for the current phase |
| `IsSandboxGame` / `IsNotSandboxGame` | Game is / is not a sandbox |

**What to check in review:**
- Does the permission class check exactly one concept?
- Does it have a clear `message`?
- Is it composed with other permissions in the view, not duplicating checks?
- Does an existing permission class already cover this check? (see table above)

### 2.6 Testing

#### Factory fixtures

Test fixtures in `conftest.py` return callable factory functions. **Canonical example:** `service/game/conftest.py`

```python
@pytest.fixture
def pending_game_with_gm(db, primary_user, classical_variant, base_pending_phase):
    def _create(gm_user=None):
        if gm_user is None:
            gm_user = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Game with GM",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        game.members.create(user=gm_user, is_game_master=True)
        return game
    return _create
```

**Key patterns:**
- Fixtures return functions, not objects — this allows parameterization in tests
- Default parameters use existing fixtures (`primary_user`)
- Fixtures use the same manager methods as production code (`create_from_template`)
- Complex setup (like starting a game with mocked adjudication) is encapsulated in fixtures

**Note:** Fixtures for active games require significantly more setup — creating multiple users in a loop, mocking the adjudication service with `patch.object`, and calling `game.start()`. See `active_game_with_gm` in `service/game/conftest.py` for the full pattern.

#### API endpoint testing

Tests focus on the API contract, not internal methods. Test:
- **Success paths** — correct request produces correct response
- **Permission checks** — unauthenticated/unauthorized requests are rejected
- **Validation errors** — invalid data produces appropriate error responses
- **Edge cases** — boundary conditions, empty states
- **Performance** — N+1 query checks with `assertNumQueries` or similar

**What to check in review:**
- Are tests testing API endpoints (not calling model methods directly)?
- Do tests use the `api_client` fixture?
- Do tests check response status codes AND response body?
- Are permission tests present for endpoints that require specific permissions?
- Are fixtures in `conftest.py` (not in the test file)?

### 2.7 Constants

Constants use class-based definitions with `CHOICES` tuples. **Canonical example:** `service/common/constants.py`

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

**What to check in review:**
- Are constants defined as class attributes (not module-level variables or enums)?
- Is there a `*_CHOICES` tuple for use in model field definitions?
- Are constants referenced by class attribute (e.g., `GameStatus.ACTIVE`) not by string value (e.g., `"active"`)?

### 2.8 Database and Transactions

#### Atomic transactions

Use `transaction.atomic()` for operations that create multiple related objects. **Example from** `GameCreateSerializer.create()`:

```python
def create(self, validated_data):
    with transaction.atomic():
        game = Game.objects.create_from_template(variant, ...)
        game.members.create(user=request.user, is_game_master=True)
        game.channels.create(name="Public Press", private=False)
    return Game.objects.all().with_related_data().get(id=game.id)
```

#### Post-commit actions

Use `transaction.on_commit()` for side effects that should only happen after a successful commit (e.g., sending notifications). **Example from** `game/serializers.py`:

```python
def send_gm_action_notification(game, title, body, notification_type):
    def _send():
        notification_utils.send_notification_to_users(...)
    transaction.on_commit(_send)
```

#### Prefetch optimization

Use `Prefetch` objects for complex prefetch strategies. The `GameQuerySet` shows multiple patterns:

```python
# Simple prefetch
self.prefetch_related("phases")

# Prefetch with select_related on the related model
members_prefetch = Prefetch(
    "members",
    queryset=Member.objects.select_related("nation", "user__profile"),
)

# Prefetch with custom queryset
template_phase_prefetch = Prefetch(
    "variant__phases",
    queryset=Phase.objects.filter(game=None, status=PhaseStatus.TEMPLATE),
    to_attr="template_phases",
)
```

#### Circular imports

When circular imports are unavoidable, use `apps.get_model()` at **module level** (not inside methods):

```python
# GOOD — at module level in common/views.py
from django.apps import apps
Game = apps.get_model("game", "Game")
Phase = apps.get_model("phase", "Phase")

# BAD — inline import inside a method
class SomeView(APIView):
    def get(self, request):
        from game.models import Game  # Don't do this
```

### 2.9 Code Style

#### No docstrings or comments

The codebase convention is no docstrings and no comments. Code should be self-explanatory through clear naming and structure.

```python
# BAD — unnecessary docstring
class GamePauseSerializer(serializers.Serializer):
    """Serializer for pausing a game."""

    def validate(self, attrs):
        """Validate that the game is not already paused."""
        if self.instance.is_paused:
            raise serializers.ValidationError("Game is already paused")
        return attrs

# GOOD — no docstrings
class GamePauseSerializer(serializers.Serializer):
    def validate(self, attrs):
        if self.instance.is_paused:
            raise serializers.ValidationError("Game is already paused")
        return attrs
```

**Exception:** DRF view docstrings are acceptable because DRF Spectacular extracts them into the OpenAPI schema as endpoint descriptions.

#### Imports at the top

All imports must be at the top of the file. No inline imports inside methods. There are a few legacy exceptions in the codebase (`import random` in `Game.start()`, `Unit`/`SupplyCenter` imports in `GameManager.create_from_template()`, `PhaseStatus` import in `IsCurrentPhaseActive`) — do not add new inline imports following these patterns. New code must always import at the top.

---

## Part 3: Cross-Cutting Concerns

### Simplicity over cleverness

Prefer the straightforward approach over the clever one. If a piece of code requires a comment to explain, it's probably too clever.

```python
# BAD — clever but obscure
members_by_nation = {m.nation_id: m for m in members if m.nation_id}
ordered_members = [members_by_nation[n.id] for n in nations if n.id in members_by_nation]

# GOOD — straightforward
for member, nation in zip(members, nations):
    member.nation = nation
```

### Type safety and lint discipline

- **Frontend:** TypeScript strict mode. Never use `any`. The one existing `any` in `CreateGame.tsx` (`Control<any>`) is a known compromise for the `VariantSelector` component — do not add more.
- **Backend:** No type annotations enforced, but use them when they clarify intent (e.g., `duration_to_seconds(duration: Optional[str]) -> Optional[int]`).
- **Linting:** Fix all lint violations. Never suppress with `eslint-disable`, `@ts-ignore`, or `# noqa`. The only exception is the mutation-in-useEffect pattern documented in CLAUDE.md.

### Evidence-based changes

Every change must be justifiable by evidence. Before making a change, verify:
1. The issue describes the problem with current vs desired behaviour
2. The acceptance criteria define how to verify the fix
3. Tests demonstrate the fix works

Do not make changes "because it seems better" or "for consistency" unless the issue specifically calls for it.

### Generated code boundary

Files in `packages/web/src/api/generated/` are auto-generated by orval. **Never edit them manually.** Changes to the API must flow through:

1. Backend serializer/view changes
2. `docker compose up codegen` to regenerate the OpenAPI schema and TypeScript client
3. Frontend code uses the newly generated hooks and types

**What to check in review:**
- Are there changes to files in `src/api/generated/`? If so, they should only appear as the result of running codegen (not hand-edits).
- Does the PR include codegen output when backend API shape changed?

### Release communication

User-facing changes must have a `RELEASE_NOTES.md` entry. Internal refactors, code cleanup, and developer-only changes do not.

**User-facing:** New features, behaviour changes, bug fixes that affect gameplay, UI changes.
**Not user-facing:** Performance improvements invisible to users, internal refactors, dev tooling changes, test additions.

### Full-stack consistency

Backend and frontend must agree on the data contract. Key patterns:
- **camelCase conversion** — the API uses middleware to convert between Python `snake_case` and JavaScript `camelCase`. Serializer field names are `snake_case` in Python and arrive as `camelCase` in TypeScript.
- **Codegen flow** — backend changes → `docker compose up codegen` → frontend types updated. Never hand-edit types to match backend changes.
- **Enum values** — constants in `service/common/constants.py` define the valid values. The frontend receives these as string literals through generated types.

---

## PR Review Checklist

### Frontend

- [ ] New screens use the Suspense wrapper pattern (`ScreenContainer` + `ScreenHeader` + `QueryErrorBoundary` + `Suspense`)
- [ ] Data fetching uses `useXxxSuspense` hooks (not non-suspense variants)
- [ ] No optional chaining on Suspense-guaranteed data
- [ ] No mutation objects in `useEffect` dependency arrays (unless with documented eslint-disable)
- [ ] State lives at the appropriate level (backend → URL → local)
- [ ] Forms use React Hook Form + Zod with the `FormField` pattern
- [ ] UI uses shadcn/ui components (not raw HTML elements)
- [ ] Tailwind classes are minimal — no redundant classes
- [ ] Empty states use the `Notice` component
- [ ] Mutation handlers have try/catch with toast feedback
- [ ] `mutateAsync` used (not `mutate`) for proper error propagation
- [ ] No new files in `src/api/generated/` that are hand-edits
- [ ] Component props have explicit interface definitions
- [ ] Components under 200 lines
- [ ] No unnecessary `useEffect` — prefer derived state and event handlers
- [ ] No `any` types
- [ ] No lint suppressions (except the mutation dependency exception)

### Backend

- [ ] Serializers use `serializers.Serializer` base (not `ModelSerializer`)
- [ ] All serializer fields are explicitly declared
- [ ] `SerializerMethodField`s have `@extend_schema_field` annotations
- [ ] Views use DRF generic views (not raw `APIView`)
- [ ] Views are thin — no business logic in the view body
- [ ] Permission classes are declared and each checks one thing
- [ ] View mixins used for shared context (not duplicated `get_object` logic)
- [ ] Query optimizations in QuerySet methods (not in views)
- [ ] Models inherit from `BaseModel`
- [ ] Constants use class-based pattern with `CHOICES` tuple
- [ ] Multi-object creation uses `transaction.atomic()`
- [ ] Side effects use `transaction.on_commit()`
- [ ] Imports at the top of file (no inline imports)
- [ ] No docstrings or comments (except DRF view docstrings for OpenAPI)
- [ ] Circular imports resolved with `apps.get_model()` at module level
- [ ] Test fixtures are factory functions in `conftest.py`
- [ ] Tests focus on API endpoints (not internal methods)
- [ ] Tests check permissions, validation, and edge cases

### Cross-Cutting

- [ ] Codegen has been run if backend API shape changed
- [ ] RELEASE_NOTES.md updated for user-facing changes
- [ ] No changes to auto-generated files that aren't from codegen
- [ ] Evidence supports the change (linked issue, test results, before/after)
- [ ] No scope creep — only changes related to the issue
- [ ] No premature abstractions or unnecessary error handling
- [ ] No backwards-compatibility hacks (renamed unused vars, re-exports, etc.)
