# Feature: Named Coast Parent Relationships

**Date:** 2025-09-28
**Session:** Named coast database modeling and API improvements

## Summary
Implemented formal parent-child relationships between main provinces and their named coasts (e.g., Spain → Spain (NC), Spain (SC)) to support improved map rendering logic for Diplomacy game provinces.

## Problem Solved
Previously, named coasts were identified only through ID parsing (e.g., `spa/nc` belongs to `spa`), which created brittle coupling between frontend and backend. This prevented proper context-aware map rendering where different province representations should be shown based on unit type and order creation step.

## Implementation Details
- **Database Schema**: Added `parent` ForeignKey field to Province model with `on_delete=PROTECT`
- **Data Migrations**:
  - `0007_add_parent_field.py` - Adds parent field to Province model
  - `0008_set_named_coast_parents_classical.py` - Sets relationships for Classical variant
  - `0009_set_named_coast_parents_italy_vs_germany.py` - Sets relationships for Italy vs Germany variant
- **API Updates**: Enhanced ProvinceSerializer with `parent_id` and `named_coast_ids` fields
- **Query Optimization**: Added `select_related('parent')` and `prefetch_related('named_coasts')` to GameQuerySet and PhaseState queries
- **DRF Spectacular**: Added `@extend_schema_field` annotation for proper OpenAPI schema generation

## Rationale
Chose formal foreign key relationships over ID-based parsing for several reasons:
- **Data Integrity**: Database enforces relationships and prevents orphaned records
- **Performance**: Enables efficient ORM queries with joins instead of multiple lookups
- **Maintainability**: Explicit relationships are clearer than implicit ID parsing
- **Flexibility**: Works for any variant with any naming convention, not just `/` separator
- **API Simplicity**: Frontend gets simple ID references instead of duplicated province data

## Testing
- Verified parent relationships work correctly for both Classical and Italy vs Germany variants
- Confirmed API serialization includes new fields with expected values
- Validated query optimization prevents N+1 problems
- All functional tests pass (performance test counts updated for new relationships)

## Notes
- Query performance tests required count adjustments due to additional relationship queries
- Foundation is now in place for implementing context-aware named coast rendering in frontend
- Future work: Frontend map rendering logic to use these relationships for proper province visibility