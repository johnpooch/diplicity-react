# Feedback Patterns

## Loading States

**Always use skeleton screens.** When data is loading, render placeholder shapes that match the layout of the content that will appear. Do not use centered spinners.

Keep the Suspense wrapper — it is good practice. Only the fallback changes: replace `<Suspense fallback={<div></div>}>` with a skeleton that mirrors the screen structure.

**The skeleton must match the loaded content's dimensions exactly** so the swap causes no vertical shift ("hiccup"). Where content has a variable height (game cards, player cards), give the component a fixed height so the skeleton and the loaded content occupy the same space.

---

## Toast Notifications (Sonner)

### When to use a toast

- Transient mutations: join game, leave lobby, send message, copy link
- Network errors mid-session (with a Retry action)
- Success confirmation for game orders (see special rule below)
- Undo opportunity after a reversible destructive action

### When NOT to use a toast

- Form submission errors → use inline error banner instead
- State changes the UI already makes obvious (toggling a checkbox, inline edit save)

### Toast duration

Calculate based on message length. A person reads ~200 words per minute, ~3–4 words per second. Formula: `max(3000, wordCount * 300)` ms. A 5-word message stays for 3s. A 15-word message stays for ~4.5s. Never hard-code a single duration for all toasts.

A toast that carries an action (Undo, Retry) must stay long enough to use that action. Its duration is **whichever is longer** — the formula above or the action's window (see Undo toasts). An action toast must never disappear before its action can be used.

### Undo toasts

This is the canonical Undo pattern; other files reference it rather than restating it.

For reversible destructive actions (e.g. leaving a lobby you can rejoin):

1. Execute the action immediately — it is a real mutation, the user has left.
2. Show a toast with an Undo action: `"You left the lobby" [Undo]`.
3. The undo window is ~5 seconds. The toast stays for whichever is longer: the duration formula or the undo window.
4. Tapping Undo issues a *separate* reversing request (e.g. rejoin). That request can itself fail — if it does, show an error toast and leave the original action committed.

For irreversible actions, use a confirmation dialog instead (see Confirmation Dialogs below).

---

## Form Errors

### Field-level errors

The message appears below the field and the input shows a destructive border — both signals together. **This is automatic in the standard `FormField` pattern**: `FormControl` sets `aria-invalid` when the field has an error, `Input` styles its border destructive on `aria-invalid`, and `FormMessage` renders the message. Do not add a manual `border-destructive` class.

### Submission errors

When a form submission fails (server error), show an inline error banner inside the form — not a toast. Place the banner just above the submit/next button so the user sees it without scrolling up to find which field is highlighted.

```tsx
{submitError && (
  <Alert variant="destructive">
    <AlertDescription>{submitError}</AlertDescription>
  </Alert>
)}
<Button type="submit">Create Game</Button>
```

---

## Confirmation Dialogs

See [./navigation-layout.md](./navigation-layout.md) for when a confirmation belongs in an `<AlertDialog>` versus a `<Sheet>`. When you do use an `<AlertDialog>`, the copy follows this format:

### Copy format

**Title**: Verb-first, names the action exactly. No "Are you sure?"

**Description**: States the specific consequence. No vague "This cannot be undone."

```
Title:       "Delete account"
Description: "Your profile, game history, and all associated data will be permanently deleted."

Title:       "Concede game"
Description: "You will be eliminated. Your units are disbanded and your supply centers become neutral."
```

---

## Button Loading State

When an action is in progress, show a spinner before the button's label and disable the button. Keep the label — do not change it to "Creating..." or "Loading...".

```tsx
<Button disabled={isPending}>
  {isPending && <Loader2 className="size-4 animate-spin" />}
  Create Game
</Button>
```

---

## Urgency Signals

Signal urgency through color escalation only. Do not add pulsing animations or banner alerts — push notifications handle proactive alerting; the in-app UI escalates color as the situation becomes more urgent.

Example — an approaching deadline, by colouring the time display:

- Normal: default text color
- ~6 hours remaining: amber/warning color
- ~2 hours remaining: red/destructive color

---

## Network Errors (Mid-Session)

When a request fails while the user is using the app (not initial load), show an error toast with a Retry action:

```
"Failed to load games"  [Retry]
```

TanStack Query retries automatically with backoff. Only surface the error to the user after all automatic retries are exhausted.

For initial-load failures (data the screen requires to render at all), use `<QueryErrorBoundary>` which handles the error state inline in the content area, keeping the `<ScreenHeader>` visible.
