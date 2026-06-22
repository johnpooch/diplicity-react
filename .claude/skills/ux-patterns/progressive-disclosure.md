# Progressive Disclosure

Progressive disclosure is about when and how to surface complexity. The guiding principle: show what users need to act, hide what they don't — but never hide it forever.

---

## Two-Tier Explanation Model

The app has two categories of knowledge:

**Tier 1 — App features**: How to use this application. What a deadline mode is, how NMR extensions work, what Game Master controls do. These are explained **inline** using `FormDescription`, `Notice`, or the (i) tooltip pattern.

**Tier 2 — Game rules**: What a convoy is, how supply centers work, what civil disorder means. These are **never explained in the UI** unless the user explicitly asks. Gate them behind a (i) tooltip or a link to the guide. Assume the player knows the game.

---

## The (i) Info Icon Pattern

Use `(i)` when: a feature is **non-obvious** AND misunderstanding it has **meaningful consequences**.

Examples that qualify: deadline mode differences, NMR extension effects, accelerated retreat phases, Game Master implications.

Examples that do not qualify: the Game Name field, whether to make a game private.

**Implementation**: inline `FormDescription` handles the basic explanation. Add an `(i)` icon with a `<Tooltip>` immediately after the description for the fuller explanation. Never use an external link — keep all explanation in-app.

```tsx
<FormDescription>
  Automatically extends the deadline when a player hasn't submitted orders.
  <Tooltip>
    <TooltipTrigger asChild>
      <Info className="ml-1 inline size-3.5 cursor-help text-muted-foreground" />
    </TooltipTrigger>
    <TooltipContent className="max-w-xs">
      Each player receives this many extensions per game. Extensions are granted
      automatically 1 hour before the deadline if orders are incomplete. Once
      exhausted, the player NMRs normally.
    </TooltipContent>
  </Tooltip>
</FormDescription>
```

---

## First-Time Users

New users encounter an onboarding flow before reaching the main UI. This flow explains what Diplomacy is and what the app does — context before action.

The new-player introduction covers most feature types. If a feature is covered in the introduction, the UI adds no additional explanation.

If a feature is NOT covered in the introduction: show a **subtle muted text block below the relevant UI element** until the user takes their first action with it. After the first action, the text does not reappear.

```tsx
{!hasSubmittedOrders && (
  <p className="text-sm text-muted-foreground">
    Select a unit on the map to begin entering orders.
  </p>
)}
```

---

## Situational Features (First Encounter)

For features that only appear in certain game states (retreat phase, build phase, draw proposals):

- If covered in new-player intro → feature appears without any explanation
- If not covered → subtle muted inline help visible until first action

Never add "New" badges or one-time announcements. The app is the same for everyone.

---

## Conditional Fields

When a selection makes other fields irrelevant (e.g. "Sandbox" mode removes deadline fields):

- **Immediately remove** the irrelevant fields with a CSS transition (`animate-in fade-in slide-in-from-top-1`)
- Do not leave disabled ghost fields in the layout
- Do not explain what disappeared — the removed fields are self-evidently inapplicable to the chosen mode

---

## Gated Options

When an option is available only if another field is set first (e.g. Game Master requires Private game):

- Keep the option **visible but disabled**
- Use `FormDescription` to explain the condition: "Only available in private games"
- Do not hide the option — the user needs to know it exists to understand they should first enable the prerequisite

---

## Multi-Step Forms: Conscious Decisions by Design

The Create Game stepper hides deadline and advanced settings behind "Next" — but this is intentional. Deadline mode and game mode are decisions all users must consciously make. The stepper forces attention on each step.

Do not pre-validate or skip steps on behalf of the user. The defaults may be good, but users must see and consciously pass through each step.

---

## Decision Support: Just-in-Time

Show context at the moment of the decision, not before. When the user is on the variant selector, show variant details (map preview, nation count, description). When they're on the deadlines step, show a live summary of what their settings mean.

Do not front-load information. Do not summarize all consequences at the end — each step handles its own context.

---

## Competing Attention

When the user has multiple things to act on (orders to submit, a draw vote open, unread messages), show all of them simultaneously in a dashboard-style view. Do not funnel the user through one task at a time. The user decides their own priority.

---

## Read-Only Complexity (Completed Phases)

When displaying information the user doesn't need to act on (e.g. resolved orders from a completed phase):

- **Collapse by default** using an accordion
- Each nation's orders are one collapsible row
- Provide **"Expand all" and "Collapse all"** controls above the accordion — essential for players who want to review the full phase at once

```tsx
<div className="flex justify-end gap-2 text-sm">
  <button onClick={expandAll} className="text-muted-foreground hover:text-foreground">
    Expand all
  </button>
  <button onClick={collapseAll} className="text-muted-foreground hover:text-foreground">
    Collapse all
  </button>
</div>
<Accordion type="multiple" ...>
  {nations.map(nation => (
    <AccordionItem key={nation.id} value={nation.id}>
      <AccordionTrigger>{nation.name}</AccordionTrigger>
      <AccordionContent>
        {/* nation's orders */}
      </AccordionContent>
    </AccordionItem>
  ))}
</Accordion>
```

---

## Complexity Escalation

When a situation is complex enough to require understanding before acting (e.g. why the user is in civil disorder):

Use the two-layer pattern:
1. **Brief inline explanation** in a `Notice` or `Alert` on the screen where the situation is encountered
2. **`(i)` tooltip** for users who want the full picture

Never link to an external guide. Never open a Dialog to explain a situation — that interrupts the flow.

---

## Rare Features

Game Master controls and Sandbox mode are features most users will never use. They are:

- **Always present** in the UI — never behind an "Advanced" toggle
- **Visually subordinate**: listed after common options, styled at the same weight as other options but not promoted

The visual hierarchy communicates priority naturally. Users who need rare features can find them; users who don't can ignore them.
