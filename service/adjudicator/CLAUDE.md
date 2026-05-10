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
