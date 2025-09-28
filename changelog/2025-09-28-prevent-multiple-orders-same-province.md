# Feature: Prevent Multiple Orders for Same Province

**Date:** 2025-09-28
**Session:** Order Creation Constraint Implementation

## Summary
Implemented a system to prevent users from creating multiple orders for the same source province during the same game phase. New orders for a province automatically replace any existing order for that province.

## Problem Solved
Previously, users could create multiple conflicting orders for the same province in a single phase, leading to ambiguous game states and potential confusion. This change enforces the Diplomacy game rule that each province can only have one order per phase.

## Implementation Details
- **Database constraint**: Added unique constraint on (`phase_state`, `source`) fields in Order model
- **Migration created**: `order/migrations/0002_add_unique_constraint_phase_state_source.py`
- **Manager methods added**:
  - `OrderQuerySet.for_source_in_phase()` - Filter orders by phase state and source
  - `OrderManager.delete_existing_for_source()` - Remove existing orders for a province
- **Logic updated**: Modified `OrderSerializer.create()` to delete existing orders only when saving complete orders
- **Files modified**:
  - `service/order/models.py` - Added constraint, QuerySet and Manager methods
  - `service/order/serializers.py` - Updated order creation logic
  - `service/order/tests.py` - Added comprehensive test coverage

## Rationale
**Database constraint approach** was chosen to provide fail-safe protection against race conditions and ensure data integrity at the database level.

**Delete-on-complete strategy** preserves the existing step-by-step order creation UX - partial orders don't disrupt existing complete orders, but completing an order replaces any existing order for that province.

**Alternative approaches considered**:
- Update-in-place: Would complicate the step-by-step creation workflow
- Validation-only: Wouldn't prevent race conditions
- Soft deletion: Would add unnecessary complexity

## Testing
- **Unit tests**: Added 5 new test methods covering order replacement scenarios
- **Manager method tests**: Verified new QuerySet and Manager methods work correctly
- **Integration tests**: Confirmed existing order creation workflow remains unchanged
- **Database constraint**: Verified unique constraint prevents duplicate orders at DB level

## Notes
- **Backward compatible**: No breaking changes to existing API endpoints
- **Performance**: Additional DELETE query only runs when saving complete orders
- **Race condition safe**: Database constraint provides ultimate protection
- **Future consideration**: Could extend this pattern to other game entities requiring uniqueness constraints