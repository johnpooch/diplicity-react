# Gap 03: Game-State Serialization and Tactical Annotations

## Gap statement

AI_Diplomacy gives the model a heavily annotated view of the board.
`ai_diplomacy/possible_order_context.py` builds an adjacency graph from the map
(`build_diplomacy_graph`), runs BFS over it (`bfs_shortest_path`), and emits, per unit: the
three nearest enemy units with full paths (`get_nearest_enemy_units`), the three nearest
supply centers not controlled by the power, with distance and path
(`get_nearest_uncontrolled_scs`, including "dist=0 — YOU ARE HERE, hold to capture!"), and
every adjacent province with its type, SC controller, occupying unit, and which units can
support or contest moves there (`_adjacent_territory_lines`). Movement, retreat, and
adjustment phases get different builders (`_generate_rich_order_context_movement` / `_retreat`
/ `_adjustment` — the adjustment builder leads with "Builds available: N"), and a condensed
per-unit summary groups each friendly support order under the move it aids
(`_generate_condensed_move_summary`). The board itself is serialized with per-power unit and
center counts and an `[ELIMINATED]` tag (`get_board_state`, `ai_diplomacy/utils.py`), and the
context template names the power being played and its home centers
(`ai_diplomacy/prompt_constructor.py`, `context_prompt.txt`).

Our shared context (`service/bot/context/builder.py`) is: phase name, units grouped by nation,
supply centers grouped by nation with counts, a flat indexed list of legal orders per source
unit (`with_orders`), and `max_orders` for adjustment phases (`with_phase_state`). There are
**no distances, no nearest-enemy or nearest-SC annotations, no adjacency information, and no
phase-type-specific framing** — the TDD explicitly calls for tactical annotations ("nearest
enemy units and supply centers (with distances), adjacent territories, and which units can
move or support there", see **Context** in `TECHNICAL_DESIGN.md`) but none exist. The prompt
also never tells the bot **which nation it is playing**: `select_orders_system.txt` says "You
are playing a game of Diplomacy" and the model must infer its identity from which units have
legal orders. The adjacency data needed for annotations already exists in the database
(`Province.adjacencies`, `service/province/models.py:19`) but is not exposed by any serializer
(`service/province/serializers.py`, `service/variant/serializers.py`).

Status: board/units/SC/options serialization is **built and working**; tactical annotations
and nation identity are **described in the TDD but not implemented**.

## Why it matters

This is the highest-leverage tactical-quality gap. A ~24B model cannot reliably re-derive map
geometry from a unit list; AI_Diplomacy's design assumes the harness does the pathfinding so
the model reasons over pre-computed threats and targets. Without "nearest uncontrolled SC:
BUL, dist=1", a cheap model picks plausible-sounding but aimless moves. Because these
annotations live in the **shared** context block (identical for every bot in the game), they
are also the main content the prompt-caching strategy (Gap 10) amortizes.

Depends on: nothing. Feeds Gaps 04 (order prompts), 09 (negotiation context), 10 (caching).

## Proposed approach

**Expose adjacencies over the API.** Adjacency is public map knowledge available to any
player, so exposing it respects the player-via-API boundary. Add to
`VariantProvinceSerializer` (`service/variant/serializers.py`):

```python
adjacencies = serializers.ListField(child=serializers.CharField(), read_only=True)
type = serializers.CharField(read_only=True)
supply_center = serializers.BooleanField(read_only=True)
```

The variant payload is fetched once per game and is static, so payload growth is irrelevant;
`PhaseRetrieveSerializer` and the per-phase payloads are untouched. Codegen must be re-run
(`docker compose up codegen`) since the schema changes, followed by `npx tsc -b --noEmit` in
`packages/web`.

**Fetch and graph on the bot side.** `service/bot/api_client.py` gains `get_variant(variant_id)`
against the existing variant endpoint; `fetch_context` (`service/bot/context/fetch.py`) adds
the variant to `ContextData` (the game payload already carries the variant id). A new
`service/bot/context/map.py` provides:

```python
def build_graph(provinces) -> dict[str, list[str]]
def shortest_distances(graph, start_id) -> dict[str, int]
def nearest_enemy_units(data, graph, unit, n=3) -> list[tuple[str, int]]
def nearest_uncapped_supply_centers(data, graph, unit, n=3) -> list[tuple[str, int]]
```

One simplification versus AI_Diplomacy: a single undirected province graph rather than
per-unit-type (army/fleet) graphs. `Province.adjacencies` is symmetric
(`service/province/tests.py:51`) but not typed by unit; distances become "map distance" rather
than "moves for this unit type". That is acceptable for orientation-level annotations and
avoids re-deriving godip movement rules in the bot; the legal-order list remains the source of
truth for what a unit can actually do. Full paths are also dropped — distance plus first-step
provinces (derivable from the legal move options we already list) carry most of the signal at
a fraction of the tokens.

**Extend the shared context.** In `service/bot/context/builder.py`:

- `with_game_state` adds per-nation unit/SC counts to the existing grouping (cheap, mirrors
  `get_board_state`).
- New `with_tactical_annotations()` emits, per own unit:

```
Unit A bud:
  Adjacent: tri (SC: Austria, occupied A tri Austria), ser (SC: unowned, empty), rum (SC: unowned, occupied A rum Russia)
  Nearest enemy units: A rum (Russia, dist 1), F bla (Russia, dist 2)
  Nearest uncontrolled supply centers: ser (unowned, dist 1), rum (Russia, dist 1)
```

- New phase-type framing in `with_phase_state`, mirroring AI_Diplomacy's adjustment/retreat
  builders: `Builds available: N` / `Disbands required: N` for adjustment (derivable from
  `max_orders` plus whether options are Build or Disband), and a dislodged-units line for
  retreats (units already carry `dislodged`, see `UnitDict` in `service/bot/types.py`).

Ordering inside every section must be deterministic (sorted by province id) so the block is
byte-identical across bots and calls within a phase — a hard requirement for Gap 10.

**Name the nation in the private context.** New `with_identity()` on the builder appending
`You are playing <nation>.` to the private sections, sourced from the bot's phase state
(`phase_states` in `ContextData` already includes the member and orderable provinces —
`service/phase/serializers.py:18`). It goes in the private block because it differs per bot;
Gap 06 later folds it into the persona block.

## Cost impact

No new LLM calls. The shared block grows from roughly 300–600 tokens (classical, mid-game) to
an estimated 1,500–3,000 tokens once per-unit annotations are added — the single biggest input
increase in this plan. Two mitigations: annotations cap at n=3 per category (as in
AI_Diplomacy) with no paths, and the whole block sits in the cacheable shared prefix, so under
Gap 10 the marginal cost per additional bot/call in the same phase is the ~10% cache-read
rate. Without caching, at seven bots × two critical calls this is ~40k extra input tokens per
phase — still around €0.04/phase at Haiku-class input pricing and proportionally less on the
Qwen target, but it is the reason Gap 10 should land soon after this doc.

## Scope boundaries

Out of scope here:

- Message/negotiation history serialization — Gap 05.
- Persona/diary/goals blocks in the private context — Gaps 06–08.
- `cache_control` markers and shared-prefix mechanics — Gap 10 (this doc only guarantees
  determinism).
- The TDD's future "shared game analysis" LLM summary — deferred in the TDD itself.
- Frontend changes beyond regenerated types (no UI consumes adjacencies yet).

## Testing notes

- `service/variant/tests/`: variant endpoint returns `adjacencies` for classical provinces
  (assert a known adjacency, e.g. `stp` ↔ `mos`, matching `service/province/tests.py:34`).
- `service/bot/tests.py`, `TestContextBuilder`: feed a small fixture graph and assert the
  rendered annotation lines — nearest-SC distance, adjacency occupancy tags, adjustment
  framing (`Builds available: 1` for the `active_build`-style scenario), and that two builds
  of the same data render byte-identical output.
- Unit tests for `context/map.py`: BFS distances on a 4-province fixture, tie-breaking by
  province id, `n` capping.
- `service/integration/test_bot.py`: the existing `test_bot_game_starts_on_creation_and_plays_phase`
  keeps passing; add an assertion that `plan` still submits orders when the variant endpoint
  returns provinces without adjacencies (annotations degrade to nothing rather than failing).

## Open questions

- Is a single untyped graph good enough, or do fleet-only sea routes distort distances badly
  enough (e.g. armies "one step" across a sea province) to justify typed graphs? Typed graphs
  require encoding unit-type traversal rules per province type, which `Province.type` supports
  (`land`/`sea`/`coast`) at moderate extra complexity.
- Should annotations appear for enemy units too (AI_Diplomacy annotates only the acting
  power's units)? More tokens for marginal value; recommend own units only until transcripts
  show the model missing obvious threats.
