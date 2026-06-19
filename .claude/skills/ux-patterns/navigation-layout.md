# Navigation & Layout

## Screen Structure

Every screen follows this hierarchy:

```
ScreenContainer
  ScreenHeader (title, optional back button, optional header action)
  QueryErrorBoundary
    Suspense (with skeleton fallback)
      ScreenCard / ScreenCard / ...
        ScreenCardContent
          [screen content]
```

Never put layout wrappers inside a screen component. Layouts (`HomeLayout`, `GameDetailLayout`) are applied at the router level via `<Outlet />`. Screens return content only.

---

## Typography Hierarchy

Maximum 3 levels per screen:

- `<ScreenHeader title="...">` → renders as `h1`
- Section headings inside cards → `<h2 className="text-lg font-semibold">`
- Sub-section headings → `<h3 className="text-sm font-medium">`

Never go deeper than h3. Never use bold text to substitute for a heading level.

---

## Sheet vs Dialog: The Rule

**`<Sheet>`** (drawer/bottom sheet): for secondary content and quick-peek panels.

Use for: player profiles, game info detail, settings that don't require a decision, any content the user might want to reference while staying in context.

**`<AlertDialog>`**: for interruptions only.

Use for:
1. Destructive/irreversible action confirmation
2. Unexpected information the user must acknowledge before continuing

Do not use Dialog or AlertDialog for information, navigation, or secondary content. If there's no decision to make, it's a Sheet.

When a Sheet or Dialog opens, focus moves to the first interactive element (Radix default behavior — do not override).

---

## Navigation Patterns

### Multi-mode screens (My Games / Find Games)

- **Desktop**: sidebar navigation
- **Mobile**: bottom tab bar

### Tabs (reminder)

`<Tabs>` is a navigation primitive only. It renders peer-level views the user switches between, like "My Games" and "Find Games". It is never used for form field selection.

### Action placement

- **Screen header (top right)**: global or screen-level actions — Add, Filter, Settings icon
- **Bottom of content**: primary form submission — Next, Create Game, Save Changes
- **Inline with content**: contextual row-level actions — Edit pencil, join button on a game card

### Button layout by context

| Context | Layout |
|---------|--------|
| Mobile, single action | Full-width button |
| Mobile, primary + secondary | Full-width primary, secondary as ghost/text link below |
| Desktop, form with Back/Next | Side-by-side equal-width buttons in a flex row |
| Mobile, form with Back/Next | Full-width stack (Back above Next), or full-width Next only with Back as text link |

---

## Multi-Step Forms (Stepper)

- Back on step 1 = native navigation (exit the flow)
- Back on step 2+ = previous step
- If the form has been modified and user attempts to exit from step 1, prompt before discarding
- Stepper does not allow skipping steps — each step must be validated before advancing

The wizard exists because all steps require conscious decisions. Do not skip steps programmatically or pre-validate on behalf of the user.

---

## Inline Editing

For editable fields on non-form screens (e.g. username on Account screen):

1. Show value + edit icon (`<Pencil>` button with `aria-label`)
2. Tap edit: value is replaced with `<Input>` pre-filled with current value
3. Show Save (`<Check>`) and Cancel (`<X>`) icon buttons to the right
4. Save/Cancel appear immediately — never below the field
5. On save success: return to display state
6. On save failure: show error message inline below the input (not a toast)

---

## Settings: Local vs Global

The Account screen contains both device-local settings (e.g. Push Notifications) and global account settings (e.g. username, theme preference). These must be visually separated with distinct section headings:

- "This device" or "Notifications" — settings that apply to this device only
- "Account" — profile settings that apply everywhere

Never mix the two groups in the same section.

---

## Icon-Only Buttons

Both `aria-label` and a visible tooltip are required. No exceptions.

```tsx
<Tooltip>
  <TooltipTrigger asChild>
    <Button size="icon" variant="ghost" aria-label="Edit name" onClick={handleEdit}>
      <Pencil className="size-4" />
    </Button>
  </TooltipTrigger>
  <TooltipContent>Edit name</TooltipContent>
</Tooltip>
```

---

## Touch Targets

Minimum 48×48dp for all interactive elements on mobile. If a visual element is smaller (e.g. a 16×16 icon), expand the hit area with padding. The `size="icon"` variant on `<Button>` handles this for icon buttons — do not reduce it.

---

## Lists: Cards vs Rows

| Content type | Component |
|-------------|-----------|
| Rich items with preview (games, variants with map) | `<Card>` or `<ScreenCard>` |
| Simple items (players, account settings, nav items) | `<Item>` / `<ItemGroup>` from `@/components/ui/item` |

Within a list, all items must use the same component. Never mix cards and rows.

---

## Notification Badges

| Signal | Style |
|--------|-------|
| "Your turn" (binary) | Dot indicator — colored dot, no count |
| Unread messages (quantitative) | Numeric badge count |
| Phase status, game status | Colored `<Badge>` with semantic color |
| Metadata (3/7 players) | Muted text, no badge |

Semantic badge colors: red = urgent/requires action, yellow = warning/approaching deadline, green = success/complete, blue = informational.

In the game map and board context, color alone may convey nation identity — a visible legend must accompany any color-only encoding.
