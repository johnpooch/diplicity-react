# Feature: Diplomacy Adjustment Phase Order Limits

**Date:** 2025-09-29
**Session:** Implement Diplomacy build/disband order count restrictions

## Summary
Implemented order count limitations for Diplomacy adjustment phases based on the difference between supply centers and units controlled by each nation, following official Diplomacy game rules.

## Problem Solved
Previously, users could create unlimited orders during adjustment phases, which violated core Diplomacy rules. The fundamental rule states: "Each nation can have as many units on the board as they control supply centers, no more, no less." This implementation ensures:

- **Build scenarios**: Nations with surplus supply centers can only build up to the surplus amount
- **Disband scenarios**: Nations with surplus units must disband exactly the surplus amount
- **Balanced scenarios**: Nations with equal supply centers and units cannot create any orders

## Implementation Details

### Key Files Modified
- `service/phase/models.py`: Added adjustment phase logic to PhaseState model
- `service/order/models.py`: Enhanced Order validation with defensive checks
- `service/phase/tests.py`: Added comprehensive PhaseState limit tests
- `service/order/tests.py`: Added Order validation limit tests

### Main Architectural Decisions
- **Two-layer protection**: UI restrictions + backend validation for defense in depth
- **Leveraged existing game logic**: Used `phase.options` dictionary for valid order locations rather than implementing home supply center logic
- **Progressive UI restriction**: When at limit, show only provinces with existing orders (allows editing)
- **Reusable calculation logic**: Centralized adjustment order limits in PhaseState model

### Core Methods Added
```python
# PhaseState model
def _is_adjustment_phase(self)
def max_allowed_adjustment_orders(self)
def orderable_provinces(self)  # Enhanced with limit logic

# Order model
def _count_existing_orders_for_phase_state(self)
def clean(self)  # Enhanced with validation
```

## Rationale
**UI-first approach chosen** because it provides better user experience by preventing invalid actions rather than showing errors after the fact. The `orderable_provinces` property was modified to return only provinces with existing orders when at the limit, allowing users to edit but not create new orders.

**Backend validation added** as a defensive measure to prevent bypassing limits through direct API calls or other means, ensuring data integrity regardless of entry point.

**Leveraged existing options system** rather than implementing home supply center logic because the game engine already handles complex location validation through the `phase.options` dictionary structure.

## Testing
- **14 comprehensive PhaseState tests** covering all adjustment scenarios
- **8 Order validation tests** ensuring backend protection
- **All existing tests pass** confirming no regressions in movement/retreat phases
- **Integration tested** with existing order creation flow

Test scenarios include:
- Build surplus scenarios (can build X units)
- Disband surplus scenarios (must disband X units)
- Balanced scenarios (no orders allowed)
- Order editing at limits
- Multiple order creation workflows
- Phase type detection and isolation

## Notes
**Future considerations**:
- The system currently uses string comparison for phase type detection (`PhaseType.ADJUSTMENT`)
- Order replacement logic works correctly with limits (delete + create maintains count)
- The implementation is backward compatible with all existing Movement and Retreat phase functionality

**Dependencies**:
- Requires `PhaseType.ADJUSTMENT` constant in common/constants.py
- Relies on existing supply center and unit tracking in Phase model
- Uses established Order creation workflow via serializers

**Performance**:
- Minimal impact as limit calculations only run for adjustment phases
- Database queries are optimized using existing related field patterns
- No additional migrations required