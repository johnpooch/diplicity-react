# Form Controls

## The Decision Tree

### Single-select fields

Start with the number of options and their label length:

| Options | Label length | Control |
|---------|-------------|---------|
| 2 | Any | Segmented control (horizontal equal-weight pills) |
| 3–4 | Short (1–2 words) | Segmented control |
| 3–4 | Long (3+ words) | Vertical radio group |
| 3–4 | Each has a description | Radio group with description under each label — OR slider if options form a spectrum (see below) |
| 5+ | Any | `<Select>` dropdown |
| 10+ | Predictable/searchable names | Combobox (typeahead) |

Examples: three short-label options (Light / Dark / System, or None / 1 / 2) → segmented control; three options that each need a description (game mode: Standard / Gunboat / Sandbox) → radio group with descriptions.

**Spectrum options → Slider.** When options represent a continuum from permissive to restrictive (e.g. player reliability: Open → Reliable+New → Reliable Only), use a slider. Left = most open, right = most restrictive. Label the endpoints and current value.

**CRITICAL: `<Tabs>` is never a form control.** It is navigation only — never use it to drive form field selection or binary choices. Use a segmented control or radio group instead.

---

### Binary toggles (exactly 2 options)

- **On/off semantics** (enabling a feature): `<Switch>`. Example: Private game, Push notifications.
- **Two named alternatives** (neither is obviously "on"): Radio buttons. Example: Fixed Time vs Duration deadlines, Random vs Ordered nation assignment.

Never use `<Tabs>` for binary form choices.

---

### Boolean fields

Use `<Checkbox>` with `FormLabel` to the right. For settings rows (Account screen), use `<Switch>` with the label to the right of the toggle.

---

### Number inputs

| Range / context | Control |
|----------------|---------|
| Small integers, ≤5 options | Stepper (− display +) |
| Spectrum with visual meaning | Slider |
| Large, precise, or open-ended | Plain numeric `<Input type="number">` |

---

### Multi-select fields

Use a vertical checkbox list (`<Checkbox>` group). This applies when ≤8 options are available. For longer lists that need search, use a Popover-based combobox with checkboxes inside.

---

### Searchable selects

Use a Combobox (typeahead input + filtered dropdown) when the list has 10+ options with predictable names that benefit from typing. Do not use a Combobox just because the list is long — only when searching is genuinely useful.

The timezone selector currently has enough options for a Combobox, but the options are too similar (all "City (Region)" format) to benefit from search — keep it as a `<Select>`. A community variant selector with hundreds of variants would warrant a Combobox.

---

### Paired fields

When two fields logically belong together (e.g. time + timezone, movement duration + retreat duration), place them in a 2-column grid on the same row:

```tsx
<div className="grid grid-cols-2 gap-4">
  <FormField name="fixedDeadlineTime" ... />
  <FormField name="fixedDeadlineTimezone" ... />
</div>
```

This is the only case where form fields share a row. All other fields are full-width stacked.

---

### Option label overflow

Truncate long labels with ellipsis after 1 line. Always add a tooltip that shows the full label on hover (desktop) or long press (mobile). Never wrap labels across 2 lines in a segmented control.

---

## Lists: Cards vs Rows

| Content type | Component |
|-------------|-----------|
| Rich items with preview (games, variants with map) | `<Card>` or `<ScreenCard>` |
| Simple items (players, account settings, nav items) | `<Item>` / `<ItemGroup>` from `@/components/ui/item` |

Within a list, all items must use the same component. Never mix cards and rows. (Players are rows today; this may shift toward cards as more player data — reliability, rating — is surfaced.)
