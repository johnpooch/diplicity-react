# CLAUDE.md — Adjudicator architectural guide

This file describes the architecture of the Diplomacy adjudicator in `engine.py` and the rules a coding agent must follow when extending it. The architecture was designed deliberately; deviations from it will be rejected even if they produce working code.

**The optimization target is pattern consistency.** This codebase is structured so that the location and shape of any piece of code can be inferred mechanically from its category. If you find yourself wanting to write something that doesn't fit a category, the answer is to ask, not to improvise.

## Architectural model: pure Position-1 Redux

State is immutable. Every state transition is a named action dispatched against a pure reducer. Every derived value is computed by a method on a View. There are no exceptions to this. There is no mutation, no in-place update, no global state, no hidden flow of data.

The full data flow:

1. External `State` (from `.domain`) arrives at `Engine.adjudicate`.
2. The engine constructs an `AdjudicationState` (frozen dataclass) from it.
3. The phase resolver for `state.phase.type` declares a sequence of action classes.
4. The engine instantiates each action and calls `Engine.dispatch(state, action)`.
5. Dispatch wraps state in a `StateView`, looks up the registered `Reducer` for the action class, calls `reduce(view, action)`, and unwraps the resulting view's `.raw`.
6. After all actions in the sequence run, the engine builds one or two external `State` instances from the final `AdjudicationState` and returns them.

Reducers may read from state through the view interface, and produce a new state via `state.replace(...)`. They never mutate. Reducers never call other reducers. Reducers never dispatch new actions.

## The eight categories

Every class and function in `engine.py` belongs to exactly one of these categories. Each has a fixed shape, naming convention, and registration mechanism.

### State

A single frozen dataclass: `AdjudicationState`. Holds all the working state for one phase resolution. Lives in the `# === State ===` section.

- `@dataclass(frozen=True)`.
- Contains only data — no methods, no properties.
- Fields fall into three lifecycle categories, in this order: **inputs** (set at construction), **parsed forms** (populated by parse_* reducers), **resolution outputs** (populated by resolution reducers).
- Every field has a one-line comment indicating its lifecycle category and the reducer(s) that populate it.
- Sequence and map fields are immutable types: `Tuple[...]`, `frozenset`, etc. Never `List`, `Dict`, or `Set` on the state itself.
- Add new fields only when an existing field can't hold the data. If a new field is added, it must include the lifecycle comment and the dataclass default must produce a sensible empty value (`()`, `None`, etc.).

### Action

Frozen dataclasses, declared as inner classes of the `Actions` namespace. Live in the `# === Actions ===` section.

- `@dataclass(frozen=True)`.
- Inherit from the `Action` marker base.
- Inner class names are noun phrases describing the transition — `Actions.ParseMovementOrders`, `Actions.ApplyLegalityChecks`. No `Action` suffix on the inner class itself.
- Carry only the data needed for the transition. Most actions currently carry nothing — empty actions are still meaningful as named transitions.
- Class docstring describes what the transition does and is the same content as the matching reducer's docstring (kept consistent).

### Reducer

`Reducer` subclasses paired with exactly one Action class via the `ACTION` class attribute. Live in the `# === Reducers ===` section.

- Inherit from `Reducer`. Auto-registered into `_REDUCER_REGISTRY` via `__init_subclass__`. **No decorator.**
- Class name: `<ActionInnerClassName>Reducer` — e.g. `Actions.ParseMovementOrders` is paired with `ParseMovementOrdersReducer`.
- Class attribute: `ACTION = Actions.X` — declared before the `reduce` method.
- `reduce` is a `@classmethod` taking `(cls, state: StateView, action: Action)` and returning `StateView`.
- The class docstring describes what state fields are populated and from what.
- No `__init__`. No instance state. No instance methods. Reducers are classes only for category consistency; they are stateless.
- The primary entry point is the `reduce` classmethod. A reducer class may additionally declare private classmethod helpers (leading underscore, signature `(cls, state: StateView) -> StateView`) called only from its own `reduce`. Helpers follow the same constraints as `reduce` — access state through the View interface, return new state via `state.replace(...)`, never mutate. Helpers exist to decompose a single reducer's response into conceptually distinct substeps; they are never called from outside the reducer that owns them.
- `reduce` body **must** access state exclusively through the `StateView` interface. Never `state.raw.something`. Never reach around the view.
- `reduce` body **must** return state via `state.replace(...)`. Never construct an `AdjudicationState` directly.
- Reducers may not call other reducers. If a transition needs multiple steps, those are multiple actions in the phase resolver's `ACTIONS` tuple.

### View

Read-only wrappers that provide ergonomic, chainable access to derived state. Live in the `# === Views ===` section.

- One top-level: `StateView`. Sub-views are constructed via methods on `StateView`: `state.province(parent)`, `state.nation(nation)`, `state.units()`, `state.orders()`.
- Sub-view classes: `<Subject>View` — `ProvinceView`, `NationView`, `UnitsView`, `OrdersView`. Add new sub-views when a derivation is naturally about a domain entity not yet represented.
- Each View takes the underlying `AdjudicationState` in `__init__`, plus optionally one domain identifier (a province parent id, a nation, etc.).
- Views are stateless beyond construction. No caching, no memoization, no lazy fields. Every method call recomputes from the state.
- **Every View accessor is a method, not a property.** The single exception is `StateView.raw`, which is a property to signal that it bypasses the normal View interface. This exception is documented inline and should not be replicated on other accessors.
- A method returns one of three things: (a) a primitive or immutable collection (`bool`, `int`, `frozenset`, `tuple`), (b) a domain dataclass instance from `.domain` (`Unit`, `Province`, `Phase`, etc.), or (c) another View.
- A method returns a sub-View when the result is itself a domain entity you'd want to ask further questions of. A method returns a primitive when the result is a final answer.
- No method on a View may mutate state or return mutated state. The only state-producing method is `StateView.replace`, which constructs a new `AdjudicationState` and wraps it in a new `StateView`.
- Views never construct `AdjudicationState` directly (except `StateView.replace`). Views never construct Action instances.
- `StateView.raw` is used only by `Engine.dispatch` and `Engine._to_external_states`. Anywhere else accessing `.raw` is a smell.

### Check

Stateless predicates over `(StateView, Order)`. Live in the `# === Check classes ===` section, declared **before** Order classes so that `LEGALITY_CHECKS` lists can reference real class objects.

- Inherit from `Check`.
- Class name: `<Subject><Predicate>Check` — `RetreatTargetIsReachableCheck`, `BuildLocationIsHomeCenterCheck`.
- Class attribute: `MESSAGE: ClassVar[str]` — the user-facing failure message.
- `check` is a `@classmethod` taking `(cls, state: StateView, order: Order)` and returning `bool` — True means the order satisfies the rule, False means it fails.
- No `__init__`, no instance state, no instance methods.
- The class docstring is a one-liner describing the rule, typically citing the DATC reference (e.g. "Enforces DATC 6.H.1.").
- `check` body **must** access state exclusively through the `StateView` interface.
- Checks are composed into Order subclasses via the `LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]]` class attribute. They are never invoked directly outside `ApplyLegalityChecksReducer`.

### Order

Frozen dataclasses representing a player's instruction. Live in the `# === Order classes ===` section.

- `@dataclass(frozen=True)`.
- Inherit from the `Order` marker base.
- Class name: `<Type>Order` — `HoldOrder`, `RetreatOrder`, `BuildOrder`, `DisbandOrder`.
- Fields carry only the data describing what the player ordered.
- Class attribute: `LEGALITY_CHECKS: ClassVar[Tuple[Type[Check], ...]]` — declared even when empty (`()`).
- **No behavioral methods.** No `status`, no `failure_reason`, no `validate`, no `resolve`, no `moves_to`, no properties. Status and failure reasons live in `state.resolutions`; any computed question about orders is a method on an appropriate View, not on the Order.
- **Trivial identity accessors are permitted.** An accessor method on an Order class is permitted only if it returns data the order already carries as a field, reframed under a uniform name across subclasses that need the same accessor. It must not access `StateView`, must not touch the variant, must not derive anything. The canonical example is `source_province()`: it returns `self.source` for movement orders and `self.location` for adjustment orders, eliminating the isinstance ladder in `Engine._to_external_states`.

### PhaseResolver

A class that declares the action pipeline for a phase. Lives in the `# === Phase resolvers ===` section.

- Inherit from `PhaseResolver`. Auto-registered into `_PHASE_RESOLVER_REGISTRY` via `__init_subclass__`. **No decorator.**
- Class name: `<PhaseType>PhaseResolver` — `MovementPhaseResolver`, `RetreatPhaseResolver`, `AdjustmentPhaseResolver`.
- Class attribute: `PHASE_TYPE = Phase.X` — declared before `ACTIONS`.
- Class attribute: `ACTIONS: ClassVar[Tuple[Type[Action], ...]]` — a tuple of Action **classes** (not factories, not instances). The order is the dispatch order.
- No business logic. The resolver is pure composition. The default `actions_for` instantiates each Action class with no args.
- If a phase needs conditional pipelines or actions with state-derived payloads, override `actions_for(state)` directly to construct actions explicitly. Do not put logic in the resolver class beyond `actions_for`.
- Class docstring lists the pipeline steps in order with one-line summaries.

### Engine

The top-level orchestration class. Lives in the `# === Engine ===` section.

- `Engine.adjudicate(state)` — public entry point. Looks up the phase resolver, materialises its actions, dispatches each in turn.
- `Engine.dispatch(state, action)` — wraps state in `StateView`, looks up the reducer, calls `reduce`, unwraps `.raw`.
- `Engine._to_adjudication_state(state)` — converts external `State` to frozen `AdjudicationState`.
- `Engine._to_external_states(original, adj)` — converts the resolved `AdjudicationState` back into external `State` instances.
- These are the four methods on Engine. Do not add others without explicit instruction.

## The hard rules

These are not preferences. Code violating any of them is wrong.

1. **No mutation, anywhere.** No reassigning attributes on `AdjudicationState`, `Order`, `Action`, `Check`, `View`, or any frozen dataclass instance. State transitions happen exclusively via `state.replace(...)` returning a new `StateView`.

2. **No methods on Order classes.** No `validate`, no `resolve`, no `moves_to` property, no `__post_init__` doing logic. Orders are pure data plus the `LEGALITY_CHECKS` class attribute. Any logic about an order lives on a View or in a reducer.

3. **No standalone module-level functions for domain logic.** Selectors as standalone functions are forbidden — they are methods on Views. Helper functions named `_unit_at`, `_compute_thing`, `_helper` are forbidden. If a piece of logic doesn't fit a category, it indicates the category is wrong, not that a helper is needed.

4. **No utility classes.** No `OrderUtils`, `StateHelpers`, `ConvoyTools`. Behavior lives on the View that owns its primary data, or in a reducer.

5. **Reducer bodies access state only through views.** Never `state.raw.parsed_orders` when `state.parsed_orders()` exists. Never construct `AdjudicationState` directly when `state.replace(...)` exists. The single exception is `Engine._to_adjudication_state`, which is the boundary where external State enters the system.

6. **Check bodies access state only through views.** Same rule as reducers.

7. **No properties on Views.** All View accessors are methods. The single exception is `StateView.raw`. If you find yourself wanting a property on a View to "make access nicer," resist — uniform calling syntax is more valuable.

8. **No category mixing.** A class is exactly one of: State, Action, Reducer, View, Check, Order, PhaseResolver, Engine. A class that's part Check and part View is wrong. A class that's both an Action and a Reducer is wrong.

9. **No decorators for category registration.** Registration happens via `__init_subclass__` keyed on a class attribute (`ACTION` for Reducers, `PHASE_TYPE` for PhaseResolvers). Do not introduce `@reducer_for` or `@phase_resolver_for` decorators; they were removed deliberately.

10. **Every state field has a defined lifecycle.** If you add a state field, comment it inline as `input`, `parsed`, or `output`, and name the reducer(s) that populate it.

## Constructing frozen dataclass instances

Three patterns, one rule per case:

- **From scratch** (no source instance exists): use the full constructor — `Unit(nation=..., type=..., location=..., ...)`. List every field explicitly. This is appropriate when building a brand-new entity, like a freshly-built unit from a Build order.
- **Copy with changes** (a source instance exists, some fields differ): use `dataclasses.replace(source, field1=new1, field2=new2)`. Only pass the fields that actually change. Fields that should be reset to defaults (e.g. clearing `dislodged` and `dislodged_from` when a dislodged unit retreats) **must be passed explicitly** — `replace` carries forward every field not mentioned.
- **No changes**: pass the source instance through directly. Frozen dataclasses are safe to share by reference; constructing an identical copy is wasted work and visual noise.

This rule applies uniformly to `AdjudicationState`, `Unit`, `Order` subclasses, `Phase`, and any other frozen dataclass. `StateView.replace` is the wrapper form of this pattern for the state class specifically.

Re-listing every field when a source instance is available is the verbose anti-pattern this rule is here to prevent. If you find yourself writing `Unit(nation=u.nation, type=u.type, location=u.location, ...)`, that's a signal — use `replace(u, ...)` with only the fields that change.

## Iterative resolution

Most reducers transform state in a single pass: read current state, compute the result, return new state. One reducer in this codebase — `ResolveStrengthsAndCutsReducer` — performs *iterative* resolution: a fixed-point loop where each iteration tries to compute previously-unknown values based on what's now known, terminating when a full pass produces no new resolutions.

This pattern is justified by the *genuinely cyclic dependencies* in Diplomacy strength resolution: support cuts depend on which attackers succeed, attacker success depends on support strength, support strength depends on which cuts apply. There's no acyclic ordering that resolves these in a single pass.

Rules for iterative reducers:

- The iteration is internal to one reducer. It is not a top-level concept. There is no `Decision` category, no `decide()` method, no shared iteration mechanism.
- The iteration's body is decomposed into named private classmethod helpers — one per *kind* of value being resolved (`_try_resolve_support_cuts`, `_try_resolve_attack_strengths`, etc.). Each helper tries to compute its assigned values from current state and returns a new state.
- Helpers may themselves call further private classmethod helpers on the same reducer (`_try_resolve_clean_cycles` calls `_trace_cycle` and `_cycle_is_clean`). Multi-level helper nesting on one reducer is permitted; the rule is "helpers are called only from within this reducer," not "helpers are called only from `reduce`."
- Each iteration is a pure function: `(state) -> state`. No mutation of intermediate values. Each pass produces a new immutable state via `state.replace(...)`.
- The loop must be bounded by a `MAX_ITERATIONS` class constant. Exceeding it raises an exception — this indicates a bug, since correct code should always quiesce.
- After the loop terminates, any still-unresolved values are filled by `_apply_resolution_defaults` with explicit per-field defaults. Each default has a comment explaining what stall case it covers.

If you find yourself wanting iterative resolution for a *different* reducer, **stop and ask**. This pattern is currently sanctioned for one use case; adding more requires architectural review.

## How to add things

### Adding a new check

1. Decide which Order class needs it.
2. Write the Check class in the `# === Check classes ===` section, grouped near similar checks (with a sub-section comment if a new domain is being introduced).
3. Add it to the relevant Order class's `LEGALITY_CHECKS` tuple.
4. Add a test for the case the check rejects.

### Adding a new view accessor

1. Decide which View it belongs on. If it's about a province, `ProvinceView`. If it's about a nation, `NationView`. If it spans the whole state, `StateView`.
2. If no existing View fits, **stop and ask** before adding a new View class.
3. Add the method. Return type rule: primitive/collection for final answers, sub-View when the result is itself an entity worth asking questions of.
4. No caching, no memoization. The method recomputes every call.

### Adding a new reducer

1. Add the Action class in `Actions`, with a docstring describing the transition.
2. Add the Reducer subclass in the `# === Reducers ===` section, paired via `ACTION = Actions.X`. Auto-registers via `__init_subclass__`.
3. Add the action to the relevant PhaseResolver's `ACTIONS` tuple in the correct position.
4. Reducer body reads state through the View interface, returns via `state.replace(...)`.

### Decomposing a long reducer

If a `reduce` method visibly performs more than one **conceptually distinct** substep — typically meaning it produces multiple independent outputs, or its halves would make sense as separate operations — extract the substeps as private classmethod helpers on the same reducer class. The `reduce` body becomes a short recipe of helper calls.

Length alone is not a sufficient reason to decompose. A reducer that's long because it performs a single tightly-coupled operation (e.g. a multi-pass resolution where each pass depends on the previous) is fine as one method. The split should be motivated by separation of concerns, not by line count.

Helpers are private to the reducer — never called from elsewhere. If you find yourself wanting to share a helper across reducers, that's a signal — stop and ask. If the substeps are independently meaningful and would naturally be responses to different actions, **stop and ask** before decomposing — that may indicate the action itself should be split.

### Adding a new phase resolver

1. If a new phase type is being supported, add the `Phase.X` constant in `.domain` first (or use an existing one).
2. Add the PhaseResolver subclass in the `# === Phase resolvers ===` section with `PHASE_TYPE = Phase.X` and `ACTIONS = (...)`. Auto-registers via `__init_subclass__`.
3. Each action in `ACTIONS` must already exist as an Action class with a matching Reducer.

### Adding a new order type

1. Add the Order subclass in the `# === Order classes ===` section, with `LEGALITY_CHECKS` declared.
2. Add the relevant Check classes in the `# === Check classes ===` section, **above** the Order section.
3. Update the relevant parse_* reducer to recognize the new wire-format `OrderType` and construct the Order.
4. Update the relevant outcome reducer if the new order type produces state changes (e.g. moves a unit).

### Adding a new state field

1. Decide its lifecycle category (input / parsed / output).
2. Add it to `AdjudicationState` in the appropriate section, with a one-line lifecycle comment naming the populating reducer.
3. Use an immutable type (`Tuple`, `frozenset`) with an empty default.
4. Add a method on the appropriate View to access it through the view interface.

## When to stop and ask

Stop and ask before:

- Introducing a new category (anything that doesn't fit one of the eight).
- Introducing a new View class (when no existing sub-view fits a piece of derived logic).
- Adding a method to an Order, State, Action, or Check class beyond what the category allows.
- Adding a property to any View other than the existing `StateView.raw`.
- Mutating any frozen instance.
- Constructing `AdjudicationState` outside `Engine._to_adjudication_state` or `StateView.replace`.
- Adding a registration decorator instead of using `__init_subclass__`.
- Writing a helper function or utility class.
- Reaching into `state.raw` from anywhere other than `Engine.dispatch` and `Engine._to_external_states`.
- Sharing a private reducer helper across multiple reducers.
- Re-listing every field of a frozen dataclass when a source instance is available — use `replace(source, ...)` instead.
- Introducing iterative resolution in a reducer other than `ResolveStrengthsAndCutsReducer`.
- Introducing a `Decision` category, decision-graph object, or any class whose role is "represents one resolvable value in a fixed-point graph." The iterative loop in `ResolveStrengthsAndCutsReducer` is one reducer with private helpers, not a graph of objects.
- Splitting `AdjudicationState` into per-phase classes. The unified state class is deliberate; per-phase splits would require architectural review.

In all of these cases, the right move is to flag the friction point. The rubric is a hypothesis; if it doesn't fit the problem you're solving, that's information worth surfacing, not a problem to route around silently.

## What the file should look like

Section order, top to bottom:

```
# === Imports ===
# === Status constants ===
# === Marker base classes ===     (Order, Action, Check)
# === Check classes ===
# === Order classes ===
# === State ===                   (AdjudicationState)
# === Views ===                   (StateView, ProvinceView, NationView, UnitsView, OrdersView)
# === Actions ===                 (Actions namespace)
# === Reducers ===                (Reducer base + subclasses)
# === Phase resolvers ===         (PhaseResolver base + subclasses)
# === Engine ===
```

Within each section, declare in dependency order — things used earlier come first.

## Tests

Tests live in `tests_v2.py`. Each behavior gets a test. Test names should make the rule under test obvious without reading the body.

When extending the engine:

- Every new Check gets a test for the case it rejects.
- Every new Reducer gets a test verifying the state change it produces.
- Every new Order type gets tests covering its happy path and at least one illegal case.
- Every new Phase pipeline gets an end-to-end test through `Engine.adjudicate`.

Tests must continue to pass after every change. If a refactor changes test expectations, the refactor has gone beyond its stated scope.

## What success looks like

When extending this engine, the resulting file should still read as:

- A small number of Order classes, each one or two lines beyond the dataclass declaration plus its `LEGALITY_CHECKS` list.
- A list of Check classes, each ~5–10 lines (message, check method).
- One State class with clearly grouped fields and per-field lifecycle comments.
- One namespace of Action classes, most empty or with one or two fields.
- A list of Reducer classes, each short and obviously pure, accessing state through the View interface. Long reducers are decomposed into private helpers when their work is conceptually distinct; they remain single methods when their work is one tightly-coupled operation.
- Frozen dataclass copies use `dataclasses.replace(source, ...)` — full constructors appear only for fresh-from-scratch instances.
- A View hierarchy that grows by adding sub-Views or methods, never by adding ad-hoc helpers.
- Phase resolver classes that are essentially declarative pipelines.
- An Engine class with the same four methods.

If a `reduce` method or helper is longer than ~15 lines and is doing more than one conceptually distinct thing, suspect that it should be decomposed. If it's longer than ~15 lines and is doing one tightly-coupled thing, that's fine — leave it.

If you find yourself wanting to write a helper that crosses category lines, add a method to an Order, mutate something, re-list dataclass fields when a source exists, or invent a new category — stop and ask.
