# Interaction Patterns

## Optimistic Updates

Three tiers based on action stakes:

### Standard optimistic (messaging, non-critical actions)
Update the UI immediately. If the server rejects, revert silently and show an error toast. No success toast — the UI state change is the confirmation.

### Orders: optimistic + success confirmation
Game orders are the exception. Update the UI immediately (optimistic), then show a success toast when the server confirms. This is non-negotiable: a missed order can lose a game. The player needs to know their order was received.

```tsx
// After mutateAsync resolves:
toast.success("Orders submitted")
```

Do not apply this pattern elsewhere — it would create noise. Only game orders warrant explicit server confirmation.

### Pessimistic (one-shot actions: join game, create game)
Wait for the server before updating the UI. Show a spinner on the button. No optimistic state change. If it fails, the user is still in the same state they started from.

---

## Undo

For reversible destructive actions (actions the user can redo without consequence, e.g. leaving a lobby they can rejoin):

1. Execute the action immediately
2. Show a toast: `"You left the lobby" [Undo]`
3. Undo window: ~5 seconds
4. If the user doesn't undo, the action is committed

For irreversible actions, use a confirmation dialog instead (see [./feedback-patterns.md](./feedback-patterns.md)).

---

## Live Updates

When new data arrives while the user is viewing a screen (e.g. a new game phase starts):

- Show a toast describing what changed
- Automatically refresh the relevant list/screen

Do not use "New content available — tap to refresh" banners. The toast + auto-refresh handles it.

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

## Inline Editing

See [./navigation-layout.md](./navigation-layout.md) for the full pattern. Summary: tap edit icon → Input appears in-place → Save/Cancel icon buttons appear inline → success returns to display state → failure shows inline error.

---

## Empty States

All empty states include: icon + title + description + primary CTA (action to resolve the empty state).

```tsx
<Notice
  icon={Users}
  title="No games found"
  message="Try a different filter or create your own game."
  action={<Button>Create Game</Button>}
/>
```

**No-results state** (search/filter returned nothing): "No results" title + "Clear filters" CTA. No icon needed — keep it lightweight.

---

## Multi-Select with Checkboxes

In a vertical checkbox list, when the user has applied selections and the state is "nothing found":

Show the empty state with a "Clear filters" button that resets all selections to their default (unselected) state.

---

## Notification Badges

| Situation | Component |
|-----------|-----------|
| "Your turn" on a nav item | Dot indicator (colored dot, no count) |
| Unread message count | Numeric badge |
| Phase or game status | Semantic `<Badge>` (colored pill) |
| Metadata count (3/7 players) | Muted text — no badge |

---

## Game Order Submission Flow

Direct manipulation on the map — tapping a unit shows order options contextually, inline on or near the map. No separate wizard panel. No sheet for order type selection.

This is the existing pattern in the codebase. Do not change it to a side-panel form.

---

## Accordion: Orders Display

When showing resolved orders for a completed phase:

- Collapsed by default (one row per nation)
- Individual rows expand/collapse on tap
- Always include "Expand all" / "Collapse all" controls above the accordion

```tsx
<div className="flex justify-end gap-3 text-sm mb-2">
  <button
    className="text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
    onClick={() => setExpandedItems(allNationIds)}
  >
    Expand all
  </button>
  <button
    className="text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
    onClick={() => setExpandedItems([])}
  >
    Collapse all
  </button>
</div>
```

---

## First-Time Feature Encounter

When a user encounters a feature for the first time (not covered in the new-player introduction):

Show a subtle muted text block below the relevant UI element. It disappears after the user takes their first action. It does not reappear.

This is the only contextual help mechanism for first encounters. Do not use highlighted "New" badges, modal announcements, or coach marks.

---

## App Updates

Non-breaking updates: distribute automatically through the app store. No in-app prompt, no banner, no notification. Users receive the update silently.

Breaking updates (if ever required): blocking `<AlertDialog>` that prevents use until updated. This should be extremely rare.

---

## Animations

Minimal. Only animate when the animation communicates a state change:

- Sheet slides in from bottom/right when opening
- Fields fade in/slide in when conditionally appearing
- Fields fade out when conditionally removed

Do not animate: page transitions, hover states, data loading, list item appearance. The game context does not call for decorative motion — players are focused on the board.

Use Tailwind's `animate-in`, `fade-in`, `slide-in-from-top-1`, `duration-150` for conditional field appearance/disappearance. Use the default Radix animation for Sheet/Dialog (already built in).
