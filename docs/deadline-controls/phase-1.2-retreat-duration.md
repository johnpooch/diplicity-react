# Implementation Phase 1.2: Separate Retreat/Adjustment Duration

## Overview

**Goal:** Allow games to have a different duration for retreat and adjustment phases than for movement phases.

**Current State:** Phase 1.1 is complete. The system has:
- `movement_phase_duration` field on the Game model
- Duration options: 1h, 12h, 24h, 48h, 3 days, 4 days, 1 week, 2 weeks
- All phase types (Movement, Retreat, Adjustment) use the same duration
- Frontend `DeadlineSummary` component already supports `retreatPhaseDuration` prop

**What Phase 1.2 Adds:**
- `retreat_phase_duration` field on Game (nullable, defaults to movement duration)
- Phase resolution uses correct duration based on phase type
- Create game form has collapsed "Advanced duration options" section
- Retreat/adjustment phases can have shorter deadlines than movement phases

**Related Issue:** [#162 - Epic: Flexible Deadlines & Game Master Controls](https://github.com/johnpooch/diplicity-react/issues/162)

---

## Implementation Tasks

### Task 0: Extract Duration Utility Function

Refactor existing `duration_map` to a shared utility to avoid code duplication.

**File to modify:** `service/common/constants.py`

**Changes:**

Add utility function after `MovementPhaseDuration` class:
```python
def duration_to_seconds(duration: str | None) -> int | None:
    """Convert a duration string to seconds. Returns None if duration is None."""
    if duration is None:
        return None
    duration_map = {
        MovementPhaseDuration.ONE_HOUR: 1 * 60 * 60,
        MovementPhaseDuration.TWELVE_HOURS: 12 * 60 * 60,
        MovementPhaseDuration.TWENTY_FOUR_HOURS: 24 * 60 * 60,
        MovementPhaseDuration.FORTY_EIGHT_HOURS: 48 * 60 * 60,
        MovementPhaseDuration.THREE_DAYS: 3 * 24 * 60 * 60,
        MovementPhaseDuration.FOUR_DAYS: 4 * 24 * 60 * 60,
        MovementPhaseDuration.ONE_WEEK: 7 * 24 * 60 * 60,
        MovementPhaseDuration.TWO_WEEKS: 14 * 24 * 60 * 60,
    }
    return duration_map.get(duration, 0)
```

**File to modify:** `service/game/models.py`

Refactor existing `movement_phase_duration_seconds` property to use the utility:
```python
from common.constants import duration_to_seconds

@property
def movement_phase_duration_seconds(self):
    return duration_to_seconds(self.movement_phase_duration)
```

---

### Task 1: Add Field to Game Model

Add the `retreat_phase_duration` field and supporting methods.

**File to modify:** `service/game/models.py`

**Changes:**

1. Add import at top of file:
```python
from common.constants import PhaseType, duration_to_seconds
```

2. Add field after `movement_phase_duration` (around line 257):
```python
retreat_phase_duration = models.CharField(
    max_length=20,
    choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
    null=True,
    blank=True,
)
```

3. Add property after `movement_phase_duration_seconds`:
```python
@property
def retreat_phase_duration_seconds(self):
    duration = self.retreat_phase_duration or self.movement_phase_duration
    return duration_to_seconds(duration)
```

4. Add method to get duration based on phase type:
```python
def get_phase_duration_seconds(self, phase_type):
    if phase_type == PhaseType.MOVEMENT:
        return self.movement_phase_duration_seconds
    else:  # Retreat or Adjustment
        return self.retreat_phase_duration_seconds
```

---

### Task 2: Create Database Migration

Generate migration for the new field.

**Command:**
```bash
docker compose run --rm service python3 manage.py makemigrations game --name add_retreat_phase_duration
```

**Expected result:** `service/game/migrations/0007_add_retreat_phase_duration.py`

---

### Task 3: Update Serializers

Add the new field to all game serializers.

**File to modify:** `service/game/serializers.py`

**Changes:**

1. Update `GameListSerializer`:
```python
retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
```

2. Update `GameRetrieveSerializer`:
```python
retreat_phase_duration = serializers.CharField(read_only=True, allow_null=True)
```

3. Update `GameCreateSerializer`:
```python
retreat_phase_duration = serializers.ChoiceField(
    choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES,
    required=False,
    allow_null=True,
)
```

4. Update `GameCreateSerializer.create()` to pass field to manager:
```python
game = Game.objects.create_from_template(
    variant,
    name=validated_data["name"],
    nation_assignment=validated_data["nation_assignment"],
    movement_phase_duration=validated_data.get(
        "movement_phase_duration", MovementPhaseDuration.TWENTY_FOUR_HOURS
    ),
    retreat_phase_duration=validated_data.get("retreat_phase_duration"),
    private=validated_data["private"],
)
```

---

### Task 4: Update Phase Resolution Logic

Update the three locations where phase deadlines are calculated.

**Files to modify:**

1. `service/phase/models.py` - `create_from_adjudication_data` method (around line 244):
```python
phase_duration_seconds = previous_phase.game.get_phase_duration_seconds(
    adjudication_data["type"]
)
scheduled_resolution = (
    timezone.now() + timedelta(seconds=phase_duration_seconds)
    if phase_duration_seconds
    else None
)
```

2. `service/game/models.py` - `start` method (around line 340):
```python
# Note: The first phase is always Movement, but we use get_phase_duration_seconds
# for architectural consistency with other resolution paths (create_from_adjudication_data,
# revert_to_this_phase). This allows the same pattern everywhere.
if self.movement_phase_duration is not None:
    phase_duration_seconds = self.get_phase_duration_seconds(current_phase.type)
    current_phase.scheduled_resolution = timezone.now() + timedelta(
        seconds=phase_duration_seconds
    )
else:
    current_phase.scheduled_resolution = None
```

3. `service/phase/models.py` - `revert_to_this_phase` method (around line 503):
```python
phase_duration_seconds = self.game.get_phase_duration_seconds(self.type)
self.scheduled_resolution = timezone.now() + timedelta(seconds=phase_duration_seconds)
```

---

### Task 5: Update Game Manager

Accept the new field in `create_from_template`.

**File to modify:** `service/game/models.py` - `GameManager.create_from_template`

Add `retreat_phase_duration=None` parameter and include it in game creation.

---

### Task 6: Update Admin

Add the field to admin display.

**File to modify:** `service/game/admin.py`

Update `list_display`:
```python
list_display = (
    "id",
    "name",
    "variant",
    "status",
    "current_phase",
    "view_phases",
    "private",
    "movement_phase_duration",
    "retreat_phase_duration",
)
```

---

### Task 7: Run Code Generation

Regenerate frontend API types after backend changes.

**Command:**
```bash
docker compose up codegen
```

This updates `packages/web/src/api/generated/` with the new `retreatPhaseDuration` field.

---

### Task 8: Update Create Game Form

Add collapsed "Advanced duration options" section with retreat duration field.

**File to modify:** `packages/web/src/screens/Home/CreateGame.tsx`

**Changes:**

1. Install Collapsible component (more appropriate than Accordion for single collapsible section):
```bash
cd packages/web && npx shadcn@latest add collapsible
```

2. Import Collapsible components:
```typescript
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
```

3. Update form schema to include `retreatPhaseDuration`:
```typescript
retreatPhaseDuration: z
  .enum([
    "1 hour",
    "12 hours",
    "24 hours",
    "48 hours",
    "3 days",
    "4 days",
    "1 week",
    "2 weeks",
  ] as const)
  .optional()
  .nullable(),
```

4. Update default values to include `retreatPhaseDuration: null`

5. Replace "Deadlines" section with structure:
   - Movement Phase Deadline dropdown (always visible, reuses existing `DURATION_OPTIONS`)
   - Collapsible with "Advanced duration options" trigger
     - Retreat/Adjustment Phase Deadline dropdown (reuses `DURATION_OPTIONS`)
     - Placeholder text "Same as movement phase" when null
   - DeadlineSummary component (already supports both durations)

Example structure:
```typescript
<Collapsible>
  <CollapsibleTrigger asChild>
    <Button variant="ghost" size="sm" className="gap-2">
      <ChevronDown className="h-4 w-4" />
      Advanced duration options
    </Button>
  </CollapsibleTrigger>
  <CollapsibleContent>
    <FormField
      control={form.control}
      name="retreatPhaseDuration"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Retreat/Adjustment Phase Deadline</FormLabel>
          <Select
            onValueChange={field.onChange}
            value={field.value ?? undefined}
          >
            <FormControl>
              <SelectTrigger>
                <SelectValue placeholder="Same as movement phase" />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {DURATION_OPTIONS.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormDescription>
            If not set, uses the same deadline as movement phases.
          </FormDescription>
        </FormItem>
      )}
    />
  </CollapsibleContent>
</Collapsible>
```

---

### Task 9: Write Backend Tests

**File to modify:** `service/game/tests.py`

Add tests to `TestGameCreateView`:

1. `test_create_game_with_retreat_phase_duration` - Create game with different movement and retreat durations
2. `test_create_game_retreat_duration_defaults_to_movement` - Verify fallback behavior when retreat duration is null

**File to modify:** `service/phase/tests.py`

Add test class `TestPhaseDuration`:

1. `test_movement_phase_uses_movement_duration` - Verify movement phases use movement_phase_duration
2. `test_retreat_phase_uses_retreat_duration` - Verify retreat phases use retreat_phase_duration
3. `test_adjustment_phase_uses_adjustment_duration` - Verify adjustment phases use retreat_phase_duration
4. `test_retreat_duration_fallback` - Verify fallback to movement duration when retreat is null

**File to modify:** `service/common/tests.py` (or create if needed)

Add test for utility function:

1. `test_duration_to_seconds` - Test all duration conversions and None handling

---

### Task 10: Write Frontend Tests

**File to modify:** `packages/web/src/components/DeadlineSummary.test.tsx`

Add tests:

1. Test that separate durations are displayed when retreat differs from movement
2. Test that single duration is displayed when retreat matches movement
3. Test that single duration is displayed when retreat is null

**File to create:** `packages/web/src/screens/Home/CreateGame.test.tsx`

Add tests:

1. Test that collapsible is collapsed by default
2. Test that retreat duration field appears when collapsible is opened
3. Test that form submits correctly with retreat duration set
4. Test that form submits correctly without retreat duration

---

### Task 11: Update Release Notes

**File to modify:** `RELEASE_NOTES.md`

Add entry under appropriate section:

```markdown
### Improved
- Games can now have different deadlines for retreat/adjustment phases than movement phases
```

---

## Acceptance Criteria

- [ ] `duration_to_seconds` utility function extracted to `common/constants.py`
- [ ] Game model has `retreat_phase_duration` field (nullable CharField)
- [ ] API returns `retreat_phase_duration` in game responses
- [ ] API accepts `retreat_phase_duration` in game creation
- [ ] Movement phases use `movement_phase_duration` for deadline calculation
- [ ] Retreat phases use `retreat_phase_duration` (or fallback to movement)
- [ ] Adjustment phases use `retreat_phase_duration` (or fallback to movement)
- [ ] Create game form has collapsible "Advanced duration options" section
- [ ] Retreat duration field shows "Same as movement phase" placeholder
- [ ] DeadlineSummary correctly displays both durations
- [ ] Existing games continue to work (all phases use movement duration)
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Release notes updated

---

## File Summary

### New Files
```
packages/web/src/
├── components/ui/
│   └── collapsible.tsx           # Generated via shadcn CLI
└── screens/Home/
    └── CreateGame.test.tsx       # Form tests
```

### Modified Files
```
service/
├── common/
│   └── constants.py              # Add duration_to_seconds utility
├── game/
│   ├── models.py                 # Add field, property, method; refactor existing property
│   ├── serializers.py            # Add field to serializers
│   ├── admin.py                  # Add to list_display
│   └── tests.py                  # Add creation tests
├── phase/
│   ├── models.py                 # Update deadline calculation
│   └── tests.py                  # Add duration tests
└── migrations/
    └── game/0007_*.py            # Generated migration

packages/web/src/
├── api/generated/                # Regenerated via codegen
├── screens/Home/
│   └── CreateGame.tsx            # Add collapsible section
└── components/
    └── DeadlineSummary.test.tsx  # Add new test cases

RELEASE_NOTES.md                  # Add user-facing change note
```

---

## Implementation Order

1. **Task 0**: Extract `duration_to_seconds` utility (enables clean Task 1)
2. **Task 1**: Add field and methods to Game model
3. **Task 2**: Create database migration
4. **Task 5**: Update Game manager
5. **Task 3**: Update serializers
6. **Task 4**: Update phase resolution logic
7. **Task 6**: Update admin
8. **Task 9**: Write backend tests (run to verify)
9. **Task 7**: Run code generation
10. **Task 8**: Update create game form (install Collapsible first)
11. **Task 10**: Write frontend tests
12. **Task 11**: Update release notes

---

## Edge Cases

1. **Sandbox games (no duration)**: Continue to work with no scheduled resolution
2. **Existing games**: Use movement duration for all phases via fallback logic
3. **Phase reversion**: Uses correct duration based on reverted phase type
4. **Both durations equal**: Works correctly, no special handling needed

---

## Migration Strategy

The new field is nullable with no default value, ensuring:
- No data migration needed for existing games
- Existing games automatically use fallback to movement duration
- API is backwards compatible (new field is optional)
