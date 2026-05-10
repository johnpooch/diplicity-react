# Adjudicator: Technical Design

## Goals

Replace the Go-based `godip` adjudicator (currently called over HTTP) with a Python adjudicator collocated with the Django backend. Two problems drive this:

1. **Variant friction.** New variants in `godip` require a Go code change and a redeploy. Variants should be data — published as JSON conforming to the canonical variant schema — and runnable without any code change.
2. **Stored options.** The current backend persists options (legal orders per unit) as state, which can drift from the underlying game state. Options should be derived from state at read time, never stored.

Secondary goals: clean testability (DATC suite as input/output fixtures), no network hop, and a stable public API that doesn't leak implementation.

## Architecture

Two pure functions, both `(Variant, GameState) → X`, sharing a deserialiser:

```
Adjudicate flow:
  (Variant, GameState) → Deserialize → State → [Preprocess] → Resolve → [Postprocess] → Serialize → list of GameStates

Options flow:
  (Variant, GameState) → Deserialize → State → GetOptions → Serialize → Options
```

`State` is the rich internal domain (Province, Nation, NamedCoast, Order, Unit, …) — not the wire format. Deserialisation is the only place that knows the JSON schema; the engine sees only domain objects.

Both functions are stateless: same inputs always produce same outputs. No caching, no shared state between calls.

`adjudicate` returns a *list* of GameStates because it auto-advances through empty phases — Retreat phases with no dislodgements, Adjustment phases with balanced SC/unit counts. The list ends at the next phase requiring player input, or at the game's end.

## File Layout

```
service/adjudicator/
├── __init__.py    # public API: adjudicate, get_options
├── serializers.py # Variant/GameState ↔ State; Options/GameState wire formats
├── domain.py      # State, Province, Nation, Unit, Order subclasses, ...
├── engine.py      # Engine, Resolver, OptionsBuilder, hook registries
├── tests.py       # End-to-end DATC tests with builder DSL at the top
└── docs/          # Design documents
```

`models.py` is deliberately avoided. Django scans every app's `models.py` for ORM models at startup; non-Django classes there mislead readers and may confuse Django's app registry. Domain objects live in `domain.py` instead.

## Public API

```python
from adjudicator import adjudicate, get_options

new_state = adjudicate(variant, game_state)
options    = get_options(variant, game_state)
```

These are the only symbols re-exported from `__init__.py`. Engine internals (Resolver, OrderType, ConvoyPathFinder, …) are not part of the public surface. The boundary keeps the rest of the Django service from coupling to internals that may change.

## Engine Internals

OO; classes co-located in `engine.py`. The file will be long; sectioned by class with `# === ClassName ===` headers. Splitting into multiple files is deferred until the file is genuinely hard to navigate, since the classes are tightly coupled and pre-splitting causes import gymnastics.

Expected classes:

- **Engine** — top-level orchestrator; the public API delegates to this
- **Resolver** — phase dispatch (Movement / Retreat / Adjustment)
- **Order** + subclasses (`Move`, `Hold`, `Support`, `Convoy`, `Build`, `Disband`, `Retreat`) — each implements `.resolve(state)` and `.options(state)`
- **ConvoyPathFinder** — graph search over adjacent fleets in sea provinces
- **DependencyGraph** — paradox resolution (Kruijswijk-style)
- **OptionsBuilder** — produces the flat option list from a State

## Variant Schema

The schema lives at the repo root: `variant.schema.yaml`. Variants are self-contained JSON documents — no inheritance / `USE` semantics. The cost of duplicating "standard"-shaped data across near-clones is small; the benefit of "what does this variant compute to" being trivially answerable is large.

The schema is split between **open extension points** and **engine-recognised behaviours**.

### Open extension points

The schema accepts arbitrary data here; new variants extend without schema change.

- `nations`, `provinces`, `adjacencies`, `namedCoasts`
- `dominanceRules`
- `adjudicationModifiers` (open vocabulary, fail on unknown)
- `unitTypes`, `phaseTypes`, `orderTypes` — top-level arrays declaring what the variant uses
- `decorativeElements`, `textElements`, per-province `path`/`labels`
- Per-variant unit and flag SVG paths, declared on `unitTypes` entries and `nations` entries respectively

### Engine-recognised behaviours

The engine implements a fixed set keyed by id:

- Phase types: `Movement`, `Retreat`, `Adjustment`
- Order types: `Move`, `Hold`, `Support`, `Convoy`, `Build`, `Disband`, `Retreat`
- Unit types: `Army`, `Fleet`

A variant may declare phase / order / unit types whose ids the engine doesn't implement. The schema accepts this; the engine rejects it at load time with a clear error.

This separates **what the schema can describe** from **what this engine can run**. The schema stays permissive and stable; the engine grows behaviours on its own clock. Adding a new id to the engine doesn't require a schema bump.

## GameState Schema

Each `GameState` represents a single phase. Three fields drive the lifecycle:

- `resolutions` — `null` for unresolved phases; populated (possibly empty) for resolved ones.
- `skipped` — `true` for phases the adjudicator advanced through automatically (Retreat with no dislodged units, Adjustment with balanced SC/unit counts). Skipped phases have `resolutions = []`.
- `outcome` — `null` until the game ends. When a power reaches `soloVictorySupplyCenters`, the adjudicator sets this on the GameState that triggered it. No subsequent GameStates are generated.

`adjudicate(variant, game_state_N)` returns a list:
- `game_state_N` updated with `resolutions` populated
- Zero or more skipped intermediate GameStates with `resolutions = []` and `skipped = true`
- `game_state_M` — the next phase requiring player input, with `resolutions = null` — *or* a GameState carrying `outcome` if the game ended in this resolution

The "current playable phase" is the latest GameState with `resolutions = null` and no preceding `outcome`. Skipped phases are immutable historical records; clients may render or hide them at their discretion.

### Outcome

```yaml
outcome:
  winners: [france]    # array to support future draw scenarios
  reason: solo         # the only reason the adjudicator detects on its own
  year: 1908
```

The adjudicator only sets `outcome.reason = "solo"`. Other endings (draw by vote, concession, year-limit) are set externally by the Django service, not the adjudicator. The adjudicator must check for solo victory after each Adjustment phase resolution.

## Options Output

Flat list, one entry per legal order. Each field is an id (string) or null:

```json
{
  "source":     "bud",
  "orderType":  "Move",
  "target":     "gal",
  "aux":        null,
  "unitType":   null,
  "namedCoast": null
}
```

Field semantics by order type:

| Order type    | source            | target                       | aux                    | unitType        |
|---------------|-------------------|------------------------------|------------------------|-----------------|
| Hold          | unit's province   | null                         | null                   | null            |
| Move          | unit's province   | destination                  | null                   | null            |
| Support hold  | unit's province   | supported unit's province    | supported unit's province | null         |
| Support move  | unit's province   | destination                  | supported unit's province | null         |
| Convoy        | fleet's province  | destination                  | army being convoyed    | null            |
| Build         | null              | province to build in         | null                   | Army or Fleet   |
| Disband       | unit's province   | null                         | null                   | null            |
| Retreat       | dislodged unit    | retreat destination, or null | null                   | null            |

Labels (`"Budapest"`, `"Galicia"`, …) are not part of the adjudicator's output. Anyone holding the variant — the Django service, the frontend — can resolve ids to labels in a single pass; baking labels into the option list would double the payload and force the engine to make rendering decisions (e.g., how to format `"stp/sc"` for display).

## Pre/Post-Processing Hooks

Modifiers in `adjudicationModifiers` may register Python callables that run before or after resolution. This is the engine's only extension mechanism for behaviours that don't fit the closed adjudicator core.

```python
@postprocess("neutral-units-hold")
def auto_hold_neutral_units(state: State) -> None:
    for unit in state.neutral_units:
        state.set_order(unit, HoldOrder())
```

Pipeline:

```
Deserialize → State
  → run preprocess hooks for each modifier in variant.adjudicationModifiers
  → Resolve
  → run postprocess hooks
  → Serialize
```

### Conventions

- Hooks are pure functions on `State`. No I/O, no shared state, no side effects beyond the State they're given.
- Unknown modifier tags fail variant load (already enforced by the schema).
- Default to one tag per concrete behaviour. Parameterise (variant-side config) only when two hooks would otherwise duplicate.
- Hook ordering: explicit `priority: int` on registration, lower runs first. Stable secondary sort by tag id.

### What hooks can do

- Mid-game terrain mutation (year-triggered adjacency changes)
- Neutral-unit auto-orders (Empires & Coalitions style)
- Custom victory conditions
- Year-end scoring side effects
- Conditional dominance logic that doesn't fit `dominanceRules`

### What hooks cannot do

- Add new phase types — hooks run *around* resolution, not *as* resolution
- Add new order types — the resolver dispatches by order type id
- Override core resolution logic — hooks see the State, not the resolver internals

If a variant needs something hooks can't express, it is a different rule family. It warrants either a deliberate engine extension (paired with a schema-version bump) or rejection.

## Decisions Log

| Decision | Rationale |
|---|---|
| Python adjudicator collocated with Django backend | Eliminate network hop; share types and tests across the backend |
| Variants as data, not code | Allow new variants to ship without backend redeploy |
| Options derived at read time, not stored | Prevent options/state drift; state is the only source of truth |
| Self-contained variants (no inheritance) | Simpler debugging; duplication cost is small |
| OO internals; single sectioned `engine.py` | Diplomacy adjudication has natural classes; pre-splitting forces import gymnastics |
| `domain.py`, not `models.py` | Avoid collision with Django model autoloader |
| Phase-result GameState model | "Blank resolutions" naturally identifies current playable phase |
| Flat options list with full labels | Simpler frontend rendering; verbosity acceptable |
| Pre/post-processing hooks tied to modifier tags | Captures rare custom behaviours without polluting the core resolver |
| Schema permissive, engine constrained | `phaseTypes`, `orderTypes`, `unitTypes` are top-level extension points; engine rejects unknown ids at load |
| Public API is two functions only | `adjudicate` and `get_options`; engine internals are private |
| Tests are end-to-end only | DATC suite as input/output fixtures with a builder DSL; no unit tests against internals |
| Auto-advance through empty phases | Avoids godip's behaviour of materialising Retreat / Adjustment phases that have no orders to receive. Skipped phases are still recorded as immutable history with `skipped = true` |
| Solo victory carried on GameState | Adjudicator detects solo victory after Adjustment and sets `outcome`. Other endings (draws, concessions) are set externally by the Django service |

## Followups (Schema)

These are known small fixes worth landing before the schema fossilises:

- `phaseProgression.transitions[].to.yearDelta` — change from `enum [0, 1]` to `integer, minimum: 0` so multi-year cycles (Hundred-style) are expressible.
- Adjacency symmetry — auto-mirror in the loader instead of leaving it as a soft convention. Asymmetric adjacency lists are a future-bug pit.
- `DominanceRule.priority` direction — pin down whether higher or lower wins; document on the field description.
- `initialState.units.province` — rename to `location`, since the field accepts a province *or* a named-coast id.
- Optional `rules` field — player-facing variant rules prose, separate from the catalogue `description`.
- Optional `gameEndsYear: integer` — for variants with fixed end years (Hundred).
- Lift `phaseTypes` and `orderTypes` to top-level arrays alongside `unitTypes`, with engine-recognised ids documented separately from the schema.

## Out of Scope

The engine deliberately does not support:

- Variants requiring novel phase types beyond Movement / Retreat / Adjustment
- Variants requiring novel order types beyond the canonical seven
- Variants requiring novel unit types with custom resolution interactions (e.g. multi-army Carrier convoys, stealth submarines)
- Event-driven engine changes that go beyond what pre/post-hooks can express

These are not bugs. They are the constraint that lets this engine implement canonical Diplomacy correctly. A variant that needs them is a different rule family and warrants a different schema and engine.
