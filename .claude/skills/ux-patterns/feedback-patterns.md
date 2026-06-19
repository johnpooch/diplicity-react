# Feedback Patterns

## Loading States

**Always use skeleton screens.** When data is loading, render placeholder shapes that match the layout of the content that will appear. Do not use centered spinners. Do not render a blank `<div>`.

The current pattern `<Suspense fallback={<div></div>}>` is an anti-pattern. Replace with a skeleton that mirrors the screen structure.

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

### Undo toasts

For reversible destructive actions (e.g. leaving a lobby that you can rejoin), execute immediately and show: `"You left the lobby" [Undo]`. The Undo window is ~5 seconds.

---

## Form Errors

### Field-level errors

Show below the field AND apply a destructive-colored border to the input. Both signals together — the border draws the eye, the message explains.

```tsx
<FormItem>
  <FormLabel>Game Name</FormLabel>
  <FormControl>
    <Input className={cn(fieldState.error && "border-destructive")} {...field} />
  </FormControl>
  <FormMessage /> {/* appears below */}
</FormItem>
```

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

Use `<AlertDialog>` only for:

1. **Destructive/irreversible actions**: Delete account, concede game, end game
2. **Unexpected required information**: Something the user must acknowledge before proceeding that could not have been anticipated

Do not use `<AlertDialog>` for: secondary information, player profiles, settings, or anything that could be a `<Sheet>`.

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

When an action is in progress, replace the button label with a spinner icon. The button remains disabled and its width does not change (use a fixed-width container if needed).

```tsx
<Button disabled={isPending}>
  {isPending ? <Loader2 className="size-4 animate-spin" /> : "Create Game"}
</Button>
```

Do not show "Creating..." text. Do not show a spinner alongside text.

---

## Urgency Signals

For approaching deadlines, change the color of the time display:

- Normal: default text color
- ~6 hours remaining: amber/warning color
- ~2 hours remaining: red/destructive color

Do not add pulsing animations or banner alerts. Push notifications handle proactive alerting — the in-app UI signals urgency through color only.

---

## Network Errors (Mid-Session)

When a request fails while the user is using the app (not initial load), show an error toast with a Retry action:

```
"Failed to load games"  [Retry]
```

TanStack Query retries automatically with backoff. Only surface the error to the user after all automatic retries are exhausted.

For initial-load failures (data the screen requires to render at all), use `<QueryErrorBoundary>` which handles the error state inline in the content area, keeping the `<ScreenHeader>` visible.
