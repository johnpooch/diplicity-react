# Options: Design

## Goal

Implement `options.py` — a function that, given a `State` (which carries its `Variant`), returns the complete flat list of orders any player could legally submit for the current phase.

Output is a `List[OrderOption]` (the dataclass already in `domain.py`). One option = one fully-specified, individually-orderable legal order. The `{id, label}` wrapping in the example provided is presentational and would be applied by a serializer layer (variant labels live in the variant; `options.py` deals in ids only).

## Public API

```python
def get_options(state: State) -> List[OrderOption]: ...
```

- Scope: **per phase, all nations**. Callers filter by nation if they need a single player's options. This matches the user's "per phase" preference and the per-state-call shape of the engine.
- Input: `State` (with `variant`, `phase`, `units`, `supply_centers`, `contested_provinces`). Submitted `orders` on the state are ignored — options describe what *could* be submitted, not what was.
- Output: flat list of `OrderOption(source, order_type, target, aux, unit_type, named_coast)`.

Raises `NotImplementedError` for unsupported phase types (mirroring `Engine.adjudicate`).

## Architectural placement

Lives **outside the engine's eight-category rubric**, as a standalone module under `service/adjudicator/`. Reasons:

- The rubric in `service/adjudicator/CLAUDE.md` is explicitly about adjudication ("given orders, resolve them"). Options is the inverse direction ("given state, enumerate legal orders") and the rubric's eight categories don't naturally fit.
- The user's interim guidance confirmed this: live outside the rubric in its own module.

What `options.py` is allowed to do:

- Construct `AdjudicationState` directly from `State` (the engine's `_to_adjudication_state` boundary equivalent). Necessary because `LEGALITY_CHECKS` operate on `StateView`.
- Use the `StateView` interface for everything else.
- Construct `Order` subclass instances (`MoveOrder`, `SupportHoldOrder`, etc.) — but never dispatch them through reducers. They exist only as inputs to `LEGALITY_CHECKS`.
- Call `convoy_path_exists` from `convoy.py`.

What `options.py` may **not** do:

- Mutate state.
- Add methods or properties to `Order` / `View` / `Check` classes.
- Duplicate legality logic that lives in `LEGALITY_CHECKS`.

## Algorithm

**Core pattern**: for each `(unit, candidate-order-shape)`, construct the matching `Order` dataclass and run its `LEGALITY_CHECKS` against a `StateView`. Survivors become `OrderOption` entries.

Candidate generation is constrained per order type — see below — so the candidate-set isn't quadratic over locations. Each candidate runs ~2–7 checks.

### Movement phase

For each standing unit `u` of any nation, at `loc`:

| Order type | Candidates | Filter |
|---|---|---|
| Hold | one (the unit itself) | no checks (`LEGALITY_CHECKS = ()`) |
| Move | `loc → target` for every location id `target` in `variant.provinces ∪ variant.named_coasts` | `MoveOrder.LEGALITY_CHECKS`, plus convoy fallback (see below) |
| SupportHold | `loc → supports → supported_loc` for every standing unit's location | `SupportHoldOrder.LEGALITY_CHECKS` |
| SupportMove | `loc → supports → (mover_loc, target)` for every other standing unit `mover_loc` × every location `target` | `SupportMoveOrder.LEGALITY_CHECKS`, plus convoy fallback (see below) |
| Convoy | only if `u` is a Fleet in a sea province: `loc → convoy → (army_source, army_target)` for every standing army's parent × every coastal parent | `ConvoyOrder.LEGALITY_CHECKS` |

For the test variant (~10 locations, ~5 units) this is well under 10k candidate evaluations. For the classical variant the heavy candidate space is SupportMove (~22 supporters × 22 movers × ~75 targets ≈ 36k) and Convoy (~10 fleets × ~30 coastal parents² ≈ 9k). The check pipelines are short (~5 checks max) and pure-Python; expected runtime is well under a second.

### Retreat phase

For each dislodged unit `u` at `loc`:

| Order type | Candidates | Filter |
|---|---|---|
| Disband | one | no checks (`LEGALITY_CHECKS = ()`) |
| Retreat | `loc → target` for every location id | `RetreatOrder.LEGALITY_CHECKS` (reachable / unoccupied / not-attacker-origin / not-contested) |

### Adjustment phase

For each nation `n`:

If `n.allowed_builds() > 0`: for each owned supply center `sc_parent`:
- Generate Army build candidate at `sc_parent` with `unit_type=Army`.
- For Fleet candidates: if the parent has named coasts, generate one candidate per coast (location = coast id); else one candidate at the bare parent.
- Filter through `BuildOrder.LEGALITY_CHECKS` (SC ownership, home-center / modifier, occupancy, unit-type-vs-location coastalness, named-coast specificity).

If `n.required_disbands() > 0`: for each standing unit of `n`, generate one disband candidate filtered by `AdjustmentDisbandOrder.LEGALITY_CHECKS` (essentially "unit exists and is owned").

The build-count and disband-count limits are *not* applied at the options stage. Options enumerate what's *individually* legal; resolution-stage enforcement (`EnforceBuildLimits`, `EnforceDisbandLimits`) decides which subset of submitted orders survives. This matches godip, which decorates options with a `Filter: MAX:Build:N` marker rather than pruning.

## Convoy semantics

Two of the engine's `LEGALITY_CHECKS` consult `state.parsed_orders()` to decide whether an order is legal:

- `MoveTargetIsReachableCheck` rejects non-adjacent army moves; `MarkConvoyedMovesReachable` later un-rejects them based on **physical fleet positions** (no submitted-convoy requirement).
- `SupportMoveSupportedCanReachCheck` rejects support-move-of-army-via-convoy unless a matching `ConvoyOrder` is **submitted** (DATC 6.D.31).

For options the user has submitted nothing yet, so a naive run of these checks would reject convoy-touched options that should appear. The module's stance:

- For Move: fall back to `convoy_path_exists(view, source_parent, target_parent, sea_fleet_locs)` where `sea_fleet_locs` is every standing fleet in a sea province. This matches the engine's own re-marking pass exactly — options that get emitted via this fallback **will** be accepted by `Engine.adjudicate` when submitted alone.
- For SupportMove: same fallback (`convoy_path_exists` over physical fleets). This **diverges** from `Engine.adjudicate`: the engine still rejects support-move-of-convoyed-army when no convoy is submitted alongside. Options emitted via this path are godip-style "would be legal if you also submitted the convoy"; testing handles this — see "Testing" below.

This is the only intentional divergence between options and engine semantics. Documented inline at the call site.

## Output format

### Field-by-field shape

Matching the example output the user provided:

| Order | `source` | `order_type` | `target` | `aux` | `unit_type` | `named_coast` |
|---|---|---|---|---|---|---|
| Hold | unit_loc | `"Hold"` | `None` | `None` | `None` | `None` |
| Move | unit_loc | `"Move"` | dest (may be a coast id) | `None` | `None` | `None` |
| SupportHold | unit_loc | `"Support"` | supported_loc | supported_loc | `None` | `None` |
| SupportMove | unit_loc | `"Support"` | move_target | mover_source | `None` | `None` |
| Convoy | fleet_loc | `"Convoy"` | army_target | army_source | `None` | `None` |
| Retreat | unit_loc | `"Retreat"` | dest | `None` | `None` | `None` |
| Disband (retreat) | unit_loc | `"Disband"` | `None` | `None` | `None` | `None` |
| Build | build_loc (may be coast id) | `"Build"` | build_loc | `None` | `"Army"` / `"Fleet"` | `None` |
| Disband (adjustment) | unit_loc | `"Disband"` | `None` | `None` | `None` | `None` |

`unit_type` is `None` for orders pertaining to an existing unit (the type is implied by the source) and set explicitly only for Build (where the player chooses).

### Named-coast convention

Matches godip: **the coast id is placed directly in the location field** (`target` for moves, `source` for builds). The `OrderOption.named_coast` separate field is **always `None`** in this implementation; the field exists in the dataclass but is unused.

Consequences:
- Fleet move to a multi-coast destination → emit one option per reachable coast, each with `target = coast_id`.
- Army move to a multi-coast destination → emit one option with `target = parent_id` (armies ignore coasts, DATC 6.B.12).
- Fleet build at a multi-coast parent → emit one option per coast, each with `source = coast_id, target = coast_id`.

This is dedupe-free at the location level: parent and named-coast adjacencies are independent in the variant graph, so the legality check naturally enumerates exactly one option per reachable destination without explicit dedup.

### SupportHold format: divergence from wire format

The user's example encodes SupportHold as `target = aux = supported_loc`. The existing engine's parser encodes SupportHold as `target = None, aux = supported_loc` (confirmed via `tests.py:5383`).

The two formats coexist in the codebase:
- **Wire format** (what the engine parses): SupportHold has `target = None`.
- **Options format** (what the user's example shows): SupportHold has `target = aux = supported_loc`.

`options.py` will emit the **options format** (`target = aux = supported_loc`). Rationale:

- Matches the user-provided example exactly.
- Matches godip's serialization convention.
- Distinguishes SupportHold from SupportMove via a within-record predicate (`target == aux`) rather than via a separate field-presence convention.
- The frontend translates options → wire orders before submission; that translation step is the right place to drop `target` for SupportHold.

The translation rule is one line and lives in the frontend / test scaffolding:

```
if order_type == "Support" and target == aux:
    wire_target = None
else:
    wire_target = target
```

If we instead emitted the wire format directly (`target = None`), options would no longer match the user's example, and the frontend would have an inconsistency in the other direction (rendering SupportHold from a `target=None` record). Either choice forces a translation somewhere; the example-matching choice is more defensible.

Worth a quick confirm from the user before writing the code, but I'm 90% sure this is the intent.

## Testing

In `tests.py`, a new `# === Order options ===` section at the end. Tests use the existing `make_variant()` test scaffolding (small 8-province world with one multi-coast).

### Layer 1: Property — every emitted option is legal

For each option in `get_options(state)`:

1. Translate to a wire `RawOrder` (handles the SupportHold `target` rewrite described above).
2. For support-move options whose supported source is non-adjacent to the target (convoy-supported), additionally submit matching `ConvoyOrder`s for every fleet on a candidate convoy chain. This is the cost of the engine/options convoy divergence; documented and contained to the test helper.
3. Run `Engine().adjudicate(state_with_option)`.
4. Assert the option's source resolution is not `Status.ILLEGAL`.

Runs over a curated set of states (1–2 per phase) covering: single unit, multi-unit, multi-coast, dislodged retreats, build phase with vacancies, disband phase with surplus.

### Layer 2: Property — every legal singleton order is enumerated

For a small curated state, brute-force enumerate the Cartesian product of `(source, order_type, target, aux, unit_type)` over a constrained space:

- `source` ∈ each location with a unit (or, for builds, each owned SC)
- `order_type` ∈ phase-appropriate types
- `target`, `aux` ∈ all variant locations ∪ `{None}`
- `unit_type` ∈ `{Army, Fleet, None}` (only varied for builds)

For each tuple:
1. Build the wire `RawOrder`.
2. Run `Engine().adjudicate(state_with_one_order)`.
3. If the engine accepts it (`status != ILLEGAL`):
   - Translate the wire order back into the canonical option shape (apply the SupportHold rewrite in reverse).
   - Assert the canonical shape appears in `get_options(state)`.

For the test variant (10 locations, ~3 units) this is ~5000 iterations per fixture — tractable, runs in a few seconds. Larger variants would need pruning; we're not running this against classical.

Caveats:
- Skips convoy-supported support moves (engine rejects standalone; covered by targeted tests in Layer 3 instead).
- Skips the `via_convoy` wire flag because options don't model it.

### Layer 3: Targeted unit tests

One test per "interesting situation" — small fixture, exact assertion on option set membership. Coverage targets:

**Movement:**
- Army at coastal province → Hold, Move to each adjacent land/coastal, Move to each convoy-reachable coastal parent.
- Army at landlocked province → Hold, Move to each adjacent land.
- Fleet at sea → Hold, Move to each adjacent sea/coast.
- Fleet at coastal multi-coast parent → no parent-target options for sibling coasts (DATC 6.B.13 coastal crawl).
- Fleet adjacent to multi-coast destination → one Move option per reachable coast.
- SupportHold to adjacent unit-occupied province.
- SupportMove with adjacent mover.
- SupportMove with convoyed mover.
- Convoy of an army from one coast to another with a fleet chain.
- No Convoy options for coastal fleets (must be in sea).

**Retreat:**
- Dislodged unit's options exclude the attacker's source.
- Dislodged unit's options exclude occupied destinations.
- Dislodged unit's options exclude contested destinations.
- Disband always emitted regardless.

**Adjustment:**
- Build options at vacant owned home center: Army + Fleet (single-coast) / one option per coast (multi-coast).
- Build options excluded at occupied home center.
- Build options excluded at unowned SC.
- Build options excluded at non-home SC unless modifier is set.
- Build options excluded for nation with no allowed_builds.
- Fleet build excluded in landlocked SC.
- Disband options emitted only for nations with required_disbands > 0.

**Generic:**
- Empty state → empty options.
- Mixed-nation state → returns options for all nations' units (not filtered).
- Unsupported phase type → `NotImplementedError`.

### Layer 4: DATC option scenarios (optional, deferred)

Many DATC entries have an implicit "what are the legal orders here" preamble that we could repurpose. Useful but not required for the initial cut. Worth considering once Layers 1–3 are passing.

### Layer 5: Variant snapshot tests (optional, deferred)

Classical Spring 1901 / Fall 1901 / Build phase 1901 — assert option set equals a reference list. Either generated and reviewed once, or imported from the old Go adjudicator's output. Useful for confidence on real variants; not part of the initial cut.

## Module structure

```
options.py
  get_options(state)                         # public entry point — phase dispatcher

  # phase generators
  _movement_options(view)
  _retreat_options(view)
  _adjustment_options(view)

  # check helpers (convoy fallback wrappers)
  _move_is_orderable(view, order, sea_fleet_locs)
  _support_move_is_orderable(view, order, mover, sea_fleet_locs)

  # convoy-path predicates
  _move_has_convoy_path(view, order, sea_fleet_locs)
  _supported_can_convoy(view, order, mover, sea_fleet_locs)

  # subordinate option generators (called from movement_options)
  _support_options(view, supporter, source_loc, sea_fleet_locs)
  _convoy_options(view, unit, source_loc)
```

No classes — module-level functions only. None of the helpers cross category lines (they consume `StateView` + `Order` instances + the `sea_fleet_locs` tuple, and return option lists). Following the spirit of the rubric without inventing categories.

## Open questions worth confirming before code

1. **SupportHold representation.** Emit `target = aux = supported_loc` (matches user example, godip convention, requires frontend translation to wire format) — or emit `target = None, aux = supported_loc` (matches existing wire format, diverges from user example). My recommendation: match the user example. The example is the contract we have.

2. **Support-move via convoy.** Emit these options (matches godip, requires test helper to submit matching convoys) — or skip them (cleaner property-test surface, slight godip divergence). My recommendation: emit them. They're rare but real, and skipping them now would be a silent omission.

3. **Nation scoping of the entry point.** The user said "per phase," which I read as all-nations-per-phase. godip takes a `nation` argument. The all-nations form is a strict superset; per-nation can be derived by filtering. My recommendation: all-nations.

4. **Build/disband limit enforcement.** Not applied at options stage — emit individually-legal options, let the resolution-stage limit reducers handle the cap. godip does this with a `Filter: MAX:Build:N` marker. We have no equivalent marker on `OrderOption`. My recommendation: leave as plain options; if the frontend needs the cap surfaced, add an out-of-band field later.

5. **Anything special for the Variant's `adjudication_modifiers`?** Only one modifier is currently in scope (`allow-builds-in-non-home-centers`) and it's already honored by `BuildLocationIsHomeCenterCheck`. Re-using the check means we get this for free. No special handling needed.

If 1–5 are confirmed (or implicitly accepted), the module is well-specified and writing it is mechanical.
