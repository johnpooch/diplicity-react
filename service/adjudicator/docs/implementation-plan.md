# Adjudicator: Implementation Plan

Companion to [technical-design.md](./technical-design.md). The technical design specifies *what* the adjudicator is; this document specifies *how it gets built*.

## Approach

Build the adjudicator in seven sequential phases. Each phase is a strict superset of the previous in capability and ends at a clearly defined milestone — typically one or more DATC sections passing. Phases are sized for a single review cycle: small enough to land cleanly, large enough to be meaningful progress.

Each phase is one branch and one PR, reviewed and merged before the next phase begins. Some refactoring of earlier phases as later ones expose corner cases is expected and welcome.

## Review process

- One phase per PR. Don't accumulate uncommitted phases; review burden compounds.
- Definition of done is concrete: the listed DATC sections passing, plus the phase's deliverables landed.
- Phase 1 deserves extra scrutiny — its decisions about the State model and test harness propagate to all six subsequent phases.
- Pre/post-hook infrastructure is *not* on this plan. It will be added when the first variant requires it.

## Phase 1 — Foundations

**Goal**: Stand up the package skeleton, public API, and test infrastructure. `adjudicate(variant, game_state)` returns the input unchanged (no orders processed); `get_options(variant, game_state)` returns an empty list.

**Deliverables**:
- `service/adjudicator/` package with `__init__.py`, `serializers.py`, `domain.py`, `engine.py`, `tests.py`
- Variant deserialisation against `variant.schema.yaml`, with hard-fail on unknown phase / order / unit type ids
- GameState deserialisation and serialisation
- Public API: `adjudicate` and `get_options` exported from `__init__.py`; engine internals private
- Test builder DSL at the top of `tests.py` — fixture loaders, assertion helpers, fluent setup

**DATC**: none. This phase exists to make later phases fast.

**Definition of done**:
- A test that calls `adjudicate(classical_variant, initial_game_state)` and gets the same state back
- A test that calls `get_options` and gets `[]`
- The builder DSL is good enough to write a 5-line DATC test in Phase 2

**Risk**: silently sets the shape every later phase relies on. State internals, the order base class, and the serialiser boundary all need careful review here.

## Phase 2 — Hold and Move

**Goal**: Hold orders (no-op resolution) and Move orders with bounce detection — multiple units to one province, head-to-head swaps without convoy.

**Deliverables**:
- `Order` base class and `HoldOrder`, `MoveOrder` subclasses
- Resolver dispatch keyed on phase type (Movement only, for now)
- Dependency-graph plumbing for cycle detection (skeletal — full use comes in Phase 3)
- `OptionsBuilder` produces Hold and Move options for the Movement phase

**DATC**: 6.A (basic checks).

**Definition of done**: all 6.A tests pass.

**Risk**: temptation to under-build the resolver because the cases are simple. The structure laid here gets reused for Support and Convoy; resist the shortcut.

## Phase 3 — Support and dislodgement

**Goal**: Strength calculation, support-cut rules, dislodge detection. Circular movement falls out naturally once the dependency graph carries real load.

**Deliverables**:
- `SupportOrder` (support-hold and support-move variants)
- Strength resolution accounting for cut supports
- Dislodge detection writing onto the resulting State
- Full use of the dependency graph for cycles
- `OptionsBuilder` extended with Support options

**DATC**: 6.C (circular movement), 6.D (supports and dislodges), 6.E (head-to-head and beleaguered).

**Definition of done**: all 6.C, 6.D, 6.E tests pass; 6.A tests still pass.

**Risk**: 6.D is the largest section and contains the trickiest convention calls (e.g. dislodging your own unit). Expect to iterate on dislodge detection when 6.E exposes corner cases.

## Phase 4 — Convoys

**Goal**: Single and multi-fleet convoys, disruption, and convoy paradoxes (Pandin's, Szykman, etc.).

**Deliverables**:
- `ConvoyOrder` and convoy resolution
- `ConvoyPathFinder` (graph search over adjacent fleets in sea provinces)
- Paradox handling in the dependency graph
- `OptionsBuilder` extended with Convoy options and convoy-aware Move options

**DATC**: 6.F (convoys), 6.G (convoying to adjacent and disruptions).

**Definition of done**: all 6.F, 6.G tests pass; all earlier sections still pass.

**Risk**: convoy paradoxes are where most adjudicators have historical bugs. Reference both `diplomacy/diplomacy` and `pydip` resolutions when DATC is ambiguous about which convention applies.

## Phase 5 — Coastal nuances and Retreat phase

**Goal**: Named-coast adjudication subtleties (a fleet at SPA/SC supports along the SC coast but not the NC coast, etc.), then layer the Retreat phase on top.

**Deliverables**:
- Named-coast support / move / convoy edge cases verified end-to-end
- Retreat phase resolver — restricted order set (`RetreatOrder`, `DisbandOrder`), separate conflict model (multiple units retreating to the same province)
- `OptionsBuilder` extended for Retreat phase output

**DATC**: 6.B (coastal issues), 6.H (retreats).

**Definition of done**: all 6.B, 6.H tests pass; all earlier sections still pass.

**Risk**: 6.B's named-coast subtleties are pervasive — passing 6.B may surface bugs in Phases 2–4. Treat regressions as real bugs in the named-coast model, not 6.B-specific patches.

## Phase 6 — Adjustment phase

**Goal**: Build/Disband legality, civil disorder default disbands, home-center vs. owned-center distinction.

**Deliverables**:
- Adjustment phase resolver (`BuildOrder`, `DisbandOrder`)
- Build legality logic — home center, currently owned, unoccupied, with `adjudicationModifiers` (e.g. `allow-builds-in-non-home-centers`) honoured
- Civil disorder default behaviour (auto-disband when no orders submitted)
- `OptionsBuilder` extended for Adjustment phase output (per-power, not per-unit)

**DATC**: 6.I (building), 6.J (civil disorder and disbands).

**Definition of done**: all 6.I, 6.J tests pass; all earlier sections still pass.

**Risk**: low. Mechanics are well-defined and the test set is small.

## Phase 7 — Empty-phase skipping and outcome

**Goal**: Auto-advance through empty phases (Retreat with no dislodgements, Adjustment with balanced SC/unit counts), and detect solo victory.

**Deliverables**:
- `adjudicate` returns a list of GameStates representing the full advance to the next phase requiring player input
- Skipped phases recorded with `resolutions = []` and `skipped = true`
- Solo victory detection after Adjustment phases; `outcome` set on the triggering GameState
- No GameStates generated after `outcome` is set

**DATC**: none directly, but every prior section's tests must keep passing.

**Definition of done**:
- A test that resolves a Movement phase with no dislodgements and verifies the returned list contains the resolved Movement GameState, the skipped Retreat, and the next playable Movement
- A test that resolves an Adjustment phase where one power crosses `soloVictorySupplyCenters` and verifies `outcome.reason == "solo"`
- All Phases 2–6 DATC tests still pass

**Risk**: low. Mostly orchestration over already-working primitives.

## After Phase 7

The adjudicator is feature-complete for canonical Diplomacy. Work that may follow but is not on this plan:

- Pre/post-hook infrastructure, added when the first variant requires it
- Schema followups listed in [technical-design.md](./technical-design.md#followups-schema) — `yearDelta`, adjacency symmetry, dominance priority direction, the `location` rename, `rules` field, `gameEndsYear`
- Migration of the existing backend from the godip HTTP client to the new in-process adjudicator
