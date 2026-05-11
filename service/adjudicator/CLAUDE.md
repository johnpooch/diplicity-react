# Adjudicator

Conventions specific to `service/adjudicator/`. Read alongside `docs/technical-design.md` (architecture) and `docs/implementation-plan.md` (phased build plan).

## The adjudicator is a pure-Python library

The Django service consumes the adjudicator. The adjudicator does not consume Django.

- **No `rest_framework` imports.** DRF serializers would duplicate `variant.schema.yaml` as Python classes — two sources of truth that will drift. Validation uses `jsonschema` against the YAML schema directly.
- **No ORM imports.** Domain types are frozen dataclasses in `domain.py`. The package must be importable without Django settings configured.
- The technical design positions this engine as something that could be extracted to a standalone module. Don't take dependencies that close that door.

## Mechanics, not presentation

The adjudicator returns ids, not labels. `OrderOption` fields are flat strings (`"bud"`, not `{"id": "bud", "label": "Budapest"}`). Anyone holding the variant resolves ids to labels in one pass; baking display strings into engine output doubles the payload and forces the engine to make rendering decisions.

If you find yourself adding `name` / `label` / `displayName` to a domain class or wire output, stop.

## Public surface is two functions

`__init__.py` re-exports `adjudicate` and `get_options`. Nothing else — not the `Engine`, not the domain types, not exception classes, not helper functions. Callers work with the dict wire format.

## Engine code style

`engine.py` is OO. Long procedural methods are the failure mode — the technical design specified Order subclasses carry behaviour, and that pattern has to hold as new phases arrive.

- **Order subclasses carry per-type behaviour, not just data.** Each subclass owns its legality check, its option enumeration, and (where applicable) its resolution. If you find yourself writing `isinstance(order, MoveOrder)` to decide what to do — or a Boolean method like `order.is_move()` that's morally the same check — the behaviour belongs on the class.
- **Use `abc.ABC` and `@abstractmethod` for engine base classes.** Forgetting to implement an abstract method becomes a class-load error, not a runtime surprise. The contract is also self-documenting.
- **No underscore prefix on engine classes.** Visibility is controlled by `__init__.py`'s re-exports, not by naming convention. `Order`, `MoveOrder`, `MovementPhaseResolver` — no leading underscores.
- **Status lives on the Order, not in a parallel dict.** A `Dict[str, str]` of per-province statuses kept in sync with a `Dict[str, Order]` of per-province orders is the procedural state-machine pattern. Give each Order a mutable `status` field; iterate over orders directly.
- **Model relationships as objects, not free-floating logic.** Bounce detection is inherently relational — it's about who's contending for a province. Build a `TargetConflict` (or similar) per contested location that owns its own resolution. The phase resolver coordinates; the conflict resolves itself. This sets up Phase 3 support-strength logic to live in one focused class rather than spreading across the resolver.
- **Phase resolvers decompose into named steps.** A phase-resolver method body should read as a sequence of method calls (`parse_orders`, `build_target_conflicts`, `resolve_conflicts`, `materialise`, …), not a 100-line procedural block. The natural shape is a per-phase resolver class instantiated per call, holding the scratch state for one resolution.
- **`OptionsBuilder` dispatches; it does not enumerate.** New order types extend a registry keyed by phase type, each contributing their own `options_for`. Adding Support in Phase 3 should not require editing `build()`.
- **Don't mutate inputs to simplify later passes.** Rewriting an order dict to fake a Hold so a later loop "just works" is the procedural shortcut. A resolution context records what happened to each order; the input is read-only.
- **Lookup and traversal questions belong on domain types.** `variant.adjacencies_of(location_id)` and `adjacency.allows(unit_type)` are methods, not free functions. A free function that takes the same first argument repeatedly is a method waiting to be promoted.

If a method in `engine.py` is longer than ~30 lines, name the conceptual blocks inside it — each is a method.

## Domain class conventions

- **Defaults are all-or-nothing per class.** Either every field has a default or none do. Don't split on "feels optional" intuition. The deserializer is the canonical constructor; if it always sets a field, the field doesn't need a default.
- **`Optional` reflects a real domain case.** `OrderOption.source` is `Optional[str]` because Build orders genuinely have no source unit. Don't use `Optional` to hedge against hypothetical flexibility.
- **Trust context for naming.** `SupplyCenter` reads fine inside `state.supply_centers: List[SupplyCenter]`; `SupplyCenterOwnership` is defensive over-naming.

## `variant.schema.yaml` is the contract

The schema lives at the repo root and is the source of truth for variant shape. If a constraint can be expressed in the schema, express it there. If it requires Python (engine-id allowlists, adjacency symmetry, named-coast pass-types), validate it in `serializers.py` immediately after schema validation.

Don't modify the schema unless explicitly asked — schema changes are tracked separately from engine work.

## Tests

DATC tests are end-to-end: call `adjudicate` / `get_options` with wire-format input and assert on wire-format output. Don't write unit tests against engine internals — the public surface is what gets tested.

Run tests via:

```bash
docker compose run --rm --workdir /app service python3 -m pytest service/adjudicator/tests.py -v
```
