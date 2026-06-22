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

## Settings

Group settings by topic — what they control (e.g. Profile, Notifications, Appearance) — not by where their value is stored. Users reason about the thing being configured, not whether it lives on the device or the account.

Some settings apply only to the current device (e.g. push notifications). Where that scope isn't obvious, add a small muted indicator on the individual setting ("This device") rather than splitting the screen by storage location.

---

## Notification Badges

Match the badge to the *kind* of signal it carries:

- **Binary** ("your turn", something needs attention) → a dot indicator, no count
- **Quantitative** (unread messages) → a numeric badge count
- **Status** (phase status, game status) → a `<Badge>` whose color carries meaning: red = urgent/requires action, yellow = warning/approaching deadline, green = success/complete, blue = informational
- **Passive metadata** (3/7 players) → muted text, never a badge

Color is never the only carrier of meaning. Where color encodes something — a semantic badge, or nation identity on the map/board — a label or visible legend must accompany it.
