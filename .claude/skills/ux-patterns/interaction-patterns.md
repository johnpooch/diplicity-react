# Interaction Patterns

## Optimistic Updates

Three tiers based on action stakes:

### Standard optimistic (messaging, non-critical actions)
Update the UI immediately. If the server rejects, revert silently and show an error toast. No success toast — the UI state change is the confirmation.

### Orders: optimistic + success confirmation
Game orders are the exception. Update the UI immediately (optimistic), then show a success toast when the server confirms. This is non-negotiable: a missed order can lose a game. The player needs to know their order was received.

Do not apply this pattern elsewhere — it would create noise. Only game orders warrant explicit server confirmation.

### Pessimistic (one-shot actions: join game, create game)
Wait for the server before updating the UI. Show a spinner on the button. No optimistic state change. If it fails, the user is still in the same state they started from.

---

## Undo

See [./feedback-patterns.md](./feedback-patterns.md) for the canonical Undo pattern: execute immediately, show a toast with an Undo action, and reverse via a separate request on undo. For irreversible actions, use a confirmation dialog instead.

---

## Live Updates

When new data arrives while the user is viewing a screen (e.g. a new game phase starts):

- Show a toast describing what changed
- Automatically reload the relevant screen content

Do not use "New content available — tap to refresh" banners. The toast + auto-reload handles it.

When the current phase resolves while the user is viewing an older phase, shift them to the newest phase anyway, and show a toast telling them it updated. One consistent rule (always show the latest) is worth more than the rare moment of being moved off a phase they were reviewing — and the toast explains why.

---

## Infinite Scroll

For lists that can grow unboundedly (game history, message history), load more content as the user scrolls to the bottom. No "Load more" button. No pagination controls.

Use TanStack Query's `useInfiniteQuery` with an intersection observer on the last item.

---

## Pull to Refresh

Support pull-to-refresh only on screens where real-time state matters:

- My Games list
- Active game phase screen

Other screens (profile, settings, variants) do not need pull-to-refresh — data there changes infrequently.

---

## Touch Targets

Minimum 48×48dp for all interactive elements on mobile. If a visual element is smaller (e.g. a 16×16 icon), expand the hit area with padding. The `size="icon"` variant on `<Button>` handles this for icon buttons — do not reduce it.

---

## Inline Editing

For editable fields on non-form screens (e.g. username on the Account screen):

1. Show value + edit icon (`<Pencil>` button with `aria-label`)
2. Tap edit: the value is replaced with an `<Input>` pre-filled with the current value
3. Show Save (`<Check>`) and Cancel (`<X>`) icon buttons to the right
4. Save/Cancel appear immediately — never below the field
5. On save success: return to display state
6. On save failure: show the error message inline below the input (not a toast)

---

## Empty States

All empty states include: icon + title + description + primary CTA (action to resolve the empty state).

```tsx
<Notice
  icon={Users}
  title="No games found"
  message="Try a different filter or create your own game."
  actions={<Button>Create Game</Button>}
/>
```

**No-results state** (search/filter returned nothing): "No results" title + "Clear filters" CTA. No icon needed — keep it lightweight.

---

## Game Order Submission Flow

Direct manipulation on the map — tapping a unit shows order options contextually, inline on or near the map. No separate wizard panel. No sheet for order type selection.

This is the existing pattern in the codebase. Do not change it to a side-panel form.

---

## Animations

Minimal. Only animate when the animation communicates a state change:

- Sheet slides in from bottom/right when opening
- Fields fade in/slide in when conditionally appearing
- Fields fade out when conditionally removed

Do not animate: page transitions, hover states, data loading, list item appearance. The game context does not call for decorative motion — players are focused on the board.

Use Tailwind's `animate-in`, `fade-in`, `slide-in-from-top-1`, `duration-150` for conditional field appearance/disappearance. Use the default Radix animation for Sheet/Dialog (already built in).
