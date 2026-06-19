---
name: ux-patterns
description: UX design decisions for diplicity-react — which controls to use, how to handle feedback, progressive disclosure, microcopy, accessibility, and interaction patterns. Load when building or reviewing any UI, making design decisions, or choosing between controls.
allowed-tools: Task, Read, Glob, Grep, Write, Edit, Bash, TodoWrite
---

# UX Patterns Skill

This skill encodes the design decisions for the diplicity-react application. These are not suggestions — they are resolved decisions to apply consistently across the codebase.

The stack is **React 19 + Tailwind v4 + Radix UI (shadcn/ui style) + react-hook-form + Zod**. No Chakra, no Semantic UI.

## Quick Reference: Which file to consult?

- Choosing a form control (select vs radio vs slider)? → [./form-controls.md](./form-controls.md)
- Loading states, errors, toasts, confirmations? → [./feedback-patterns.md](./feedback-patterns.md)
- Sheets vs dialogs, screen structure, navigation? → [./navigation-layout.md](./navigation-layout.md)
- When and how to explain things to users? → [./progressive-disclosure.md](./progressive-disclosure.md)
- Button labels, error copy, help text, tone? → [./microcopy.md](./microcopy.md)
- Optimistic updates, undo, live data, mobile? → [./interaction-patterns.md](./interaction-patterns.md)

## Non-Negotiable Principles

1. **Tabs are navigation only.** Never use `<Tabs>` to drive form selection or binary choices — use radio buttons instead.
2. **Dialogs are for interruptions only.** A `<Dialog>` or `<AlertDialog>` appears only for destructive confirmations or unexpected required information. Secondary content, player profiles, and settings go in a `<Sheet>`.
3. **Dropdowns are a last resort for form fields.** 2–4 short-label options use segmented control or radio group. `<Select>` is for 5+ options or long lists.
4. **No adaptive UI.** The interface is identical for new and experienced players. It does not hide or alter content based on usage history.
5. **Rare features are deprioritized, not hidden.** Sandbox mode and Game Master controls are always accessible but visually subordinate.

## Suspense Fallbacks

All screens that fetch data must use a skeleton fallback — not `<Suspense fallback={<div></div>}>`. See [./feedback-patterns.md](./feedback-patterns.md) for the correct pattern.

Apply this to every new screen you build and to any existing screen you touch as part of the current issue. Do not fix screens the current PR is not already touching — boy scout rule.

## Detailed Guidance

- **[./form-controls.md](./form-controls.md)** — Decision tree for every input type: select, radio, segmented control, slider, stepper, combobox, checkbox, switch
- **[./feedback-patterns.md](./feedback-patterns.md)** — Loading skeletons, toast rules, inline errors, confirmation dialogs, button loading states
- **[./navigation-layout.md](./navigation-layout.md)** — Screen structure, sheet vs dialog, action placement, stepper navigation, focus management
- **[./progressive-disclosure.md](./progressive-disclosure.md)** — Two-tier explanation model, first-time UX, conditional fields, complexity escalation, the (i) tooltip pattern
- **[./microcopy.md](./microcopy.md)** — Tone, button labels, placeholder text, help text, error copy, confirm dialog copy
- **[./interaction-patterns.md](./interaction-patterns.md)** — Optimistic updates, undo, live updates, inline editing, empty states, pagination
