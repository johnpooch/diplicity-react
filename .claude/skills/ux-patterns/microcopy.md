# Microcopy

## Tone of Voice

**Serious and direct.** This is a strategy game. Players are focused. They want efficiency, not charm.

- No personality, warmth, or wit in UI copy
- No thematic language ("dispatches", "nations" in button labels)
- No exclamation marks
- No first-person from the app ("We couldn't find that game")
- No em-dashes, no marketing or LLM-flavored phrasing ("seamless", "effortless", "unlock"). UI copy should read like a human wrote it tersely.
- Short sentences. Active voice.

---

## Button Labels

**Title Case imperative verb phrase.** Always specific — name the object being acted on.

| Do | Don't |
|----|-------|
| Create Game | Create |
| Join Game | Join |
| Save Changes | Save |
| Delete Account | Delete |
| Submit Orders | Submit |
| Leave Game | Leave |
| View Profile | View |

In a multi-step form, the final submit button names the outcome ("Create Game"), not the action ("Submit"). All other buttons: Next, Back — no label needed beyond that.

When an action is in progress, the button shows a spinner before its label and the label stays. Never change it to "Creating..." or "Loading...".

### Icon-only buttons

Any button whose only content is an icon (no visible text label) must have both an `aria-label` and a visible tooltip — the `aria-label` for screen readers, the tooltip for sighted users.

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

## Placeholder Text

Placeholders are for **example values only**. They are never a substitute for a label.

```
Good:  placeholder="e.g. Summer 1901"
Good:  placeholder="HH:MM"
Bad:   placeholder="Enter game name"   ← that's the label's job
Bad:   placeholder="Select a timezone" ← use the FormLabel
```

If the field has no useful example to show, leave the placeholder empty. Do not add ghost text that describes the field — the `<FormLabel>` does that.

---

## Help Text (FormDescription)

Show only when **the field purpose is non-obvious** or **there is a constraint with real consequences**.

Simple fields (Name, Email, Time) need no description. If a user would understand the field from its label alone, omit the description.

When description is needed, describe **consequences**, not the field:

```
Good:  "Only players with a history of completing games can join."
Bad:   "Set the minimum reliability level for players who can join this game."

Good:  "Player names and messaging are disabled."
Bad:   "Gunboat mode hides player identities."
```

After the inline description, add a `(i)` tooltip only if misunderstanding has meaningful consequences. See [./progressive-disclosure.md](./progressive-disclosure.md) for the full (i) pattern.

---

## Error Copy

**Short and specific.** State the violated constraint, nothing more.

| Good | Bad |
|------|-----|
| Name required | Please enter a game name |
| Too long | Game name must be less than 100 characters |
| Must be at least 2 characters | Your name is too short |
| Invalid email | Please enter a valid email address |

No "Please". No full sentences. No apologies. No suggestions for what to do — the label and field make the fix obvious.

---

## Explanatory Errors (Complex Situations)

When an error requires the user to understand *why* something failed before they can proceed:

**Pattern: reason + implication. No next action.**

```
"The movement phase has ended. Your orders were not submitted."
"This game is full. You cannot join."
"Your session has expired. Log in again to continue."
```

Do not add a third sentence suggesting the next step. The implication makes it clear. The UI around the error provides the path forward.

---

## Confirmation Dialog Copy

**Title**: Verb-first, names the action. No question. No "Are you sure?"

**Description**: Specific consequence. What exactly is lost or changed. No "This cannot be undone."

```tsx
// Good
<AlertDialogTitle>Delete account</AlertDialogTitle>
<AlertDialogDescription>
  Your profile, game history, and all associated data will be permanently deleted.
</AlertDialogDescription>

// Good
<AlertDialogTitle>Leave game</AlertDialogTitle>
<AlertDialogDescription>
  You will be removed from the game and cannot rejoin.
</AlertDialogDescription>

// Bad
<AlertDialogTitle>Are you sure?</AlertDialogTitle>
<AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
```

**Action buttons**: Primary = the destructive action (verb-only: "Delete", "Leave", "Concede"). Secondary = "Cancel".

---

## Empty States

See [./interaction-patterns.md](./interaction-patterns.md) for the empty-state pattern (structure and the no-results variant). For the copy: the title names what's missing ("No games yet"), the message is one short sentence pointing to the resolving action ("Join an existing game or create your own."), and the CTA verb names that action ("Find a Game"). A no-results state uses the title "No results" and a "Clear filters" CTA, with no description.

---

## Section Headings in Forms

Section headings use `<h2 className="text-lg font-semibold">` followed by `space-y-4` around the fields. Use a `<hr className="border-t">` to separate logically distinct groups within a single form step (e.g. separating variant selection from the mode fields above it).

Do not wrap sections in separate cards within a single form step. The step itself is the container.

---

## Dates and Times

- **Near future/past** (within ~7 days): relative — "in 3h", "2 days ago", "in 5 min"
- **Distant**: absolute — "Mon 15 Jun, 21:00" using the user's locale
- **Deadlines**: always relative when within 7 days (urgency is what matters)
- **Phase history**: absolute (historical record)
