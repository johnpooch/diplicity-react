# Issue Philosophy

## Purpose

This document is a **rubric for AI agents** that scope, review, and revise issues for the Diplicity React codebase. It defines what makes an issue well-formed, with examples drawn from this specific project.

It complements `CLAUDE.md` (the developer reference) without repeating it. Where `CLAUDE.md` says "use `serializers.Serializer` not `ModelSerializer`", this document says "the technical approach section should identify which serializer pattern applies and reference the canonical example."

Agents should use this rubric when running:
- `/scope-issue` — to produce a well-formed issue
- `/review-issue` — to evaluate whether an issue meets the bar
- `/apply-issue-feedback` — to understand what "addressing feedback" means

---

## 1. Problem Statement

A problem statement anchors the issue in **observable user or developer behaviour**. It must answer: "What does the user see or experience today, and what should they see instead?"

### What makes a good problem statement

- **Current behaviour** — describe what happens now, from the user's or developer's perspective
- **Desired behaviour** — describe what should happen instead
- **Context** — which screen, endpoint, or workflow is affected

### Good example

> **Current behaviour:** When a player navigates to the game detail page for a completed game, the orders panel still shows the "Confirm Orders" button. Clicking it produces a 403 error toast.
>
> **Desired behaviour:** For completed games, the orders panel should show a read-only view of the final orders without any action buttons.
>
> **Affected screen:** `packages/web/src/screens/GameDetail/Orders.tsx`, specifically the `OrdersScreen` component within the `GameDetailLayout`.

### Bad example

> We need to fix the orders UI for completed games.

This is vague — it doesn't specify what "fix" means, what the current behaviour is, or where in the codebase the problem lives.

### Red flags in problem statements

- No mention of current vs desired behaviour
- References to "the code" without specifying which screen, endpoint, or component
- Jumping straight to a solution ("add a flag to disable the button") instead of describing the problem
- Describing internal implementation details instead of observable behaviour

---

## 2. Acceptance Criteria

Acceptance criteria define **observable, testable outcomes** — not implementation steps. An acceptance criterion answers: "How would a human verify this is done correctly?"

### Observable vs implementation

| Type | Example |
|---|---|
| **Observable (good)** | "When a player visits a completed game, the orders panel displays orders in read-only mode with no action buttons" |
| **Implementation (bad)** | "Add a `readOnly` prop to the `OrdersPanel` component" |
| **Observable (good)** | "The `GET /api/games/` endpoint returns games sorted by most recently updated, with completed games excluded from the default listing" |
| **Implementation (bad)** | "Add a `status` filter to the `GameQuerySet.with_list_data()` method" |

### Writing testable criteria

Each criterion should be verifiable by:
1. **Manual testing** — a human can follow a sequence of steps and check the result
2. **Automated testing** — a test can assert the expected outcome
3. **API response inspection** — for backend changes, the response structure can be validated

### Good example (full-stack feature)

```
**Frontend:**
- [ ] The game creation form shows a new "NMR Extensions" dropdown with options: None, 1, 2
- [ ] The dropdown defaults to "None"
- [ ] After creating a game, the game detail page displays the selected NMR extension count

**Backend:**
- [ ] `POST /api/games/` accepts an `nmrExtensionsAllowed` field (integer, 0-2, default 0)
- [ ] `GET /api/games/{id}/` returns the `nmrExtensionsAllowed` value
- [ ] Creating a game with `nmrExtensionsAllowed: 3` returns a 400 validation error

**Edge cases:**
- [ ] Omitting `nmrExtensionsAllowed` from the create request defaults to 0
- [ ] The field is read-only after game creation (cannot be updated via PATCH)
```

### Bad example

```
- [ ] Add nmrExtensionsAllowed to the Game model
- [ ] Add it to the serializer
- [ ] Add it to the form
- [ ] Write tests
```

This is an implementation checklist, not acceptance criteria. It tells the implementer what to build rather than what behaviour to verify.

### Codebase-specific patterns for criteria

When writing criteria that touch the frontend, reference the user-facing behaviour within the component hierarchy:
- **Screen-level** — what the user sees on the screen (e.g., "the My Games screen shows games sorted by activity")
- **Component-level** — what a specific component renders (e.g., "the `GameCard` shows the game master's name")
- **Interaction-level** — what happens when the user acts (e.g., "clicking 'Join Game' adds the user as a member and navigates to the game detail page")

When writing criteria that touch the backend, reference the API contract:
- **Request** — what the endpoint accepts (method, path, body shape)
- **Response** — what it returns (status code, body shape)
- **Side effects** — what changes in the database or external systems
- **Permissions** — who can perform the action (authenticated user, game member, game master)

---

## 3. Technical Approach

The technical approach identifies **which layers of the stack are affected** and **which existing patterns to follow**. It bridges the gap between "what we want" (acceptance criteria) and "how we'll build it" (implementation).

### Structure

Organise the technical approach into sections by layer:

#### Backend

```
**Models:**
- Affected model(s) and whether they need new fields, properties, or QuerySet methods
- Reference the canonical pattern: `service/game/models.py` (QuerySet → Manager → Model)
- Note if a migration is needed

**Serializers:**
- Which serializer(s) need changes and whether new ones are needed
- Reference the canonical pattern: `service/game/serializers.py` (base `Serializer`, explicit fields)
- Note if validation logic is needed (`validate_*` methods or `validate()`)

**Views:**
- Which view(s) need changes and whether new ones are needed
- Reference the canonical pattern: `service/game/views.py` (DRF generics, thin views)
- Note permission classes needed (see `service/common/permissions.py`)
- Note view mixins needed (see `service/common/views.py`)

**URLs:**
- New URL patterns needed

**Tests:**
- Which test file(s) to update or create
- Reference the canonical pattern: `service/game/conftest.py` (factory fixtures)
```

#### Frontend

```
**Components/Screens:**
- Which screen(s) or component(s) need changes
- Whether new components are needed or existing ones can be extended
- Reference the Suspense wrapper pattern if a new screen is being added (see `MyGames.tsx`)

**Data Fetching:**
- Which generated hooks are needed (`useXxxSuspense` for reads, `useXxxMutation` for writes)
- Whether cache invalidation is needed after mutations
- Note: hooks come from `src/api/generated/` — do not create custom fetch logic

**Forms:**
- Whether a form is involved and the Zod schema needed
- Reference the canonical pattern: `CreateGame.tsx` (React Hook Form + Zod + FormField)

**State:**
- What state is needed and where it lives (URL, local, derived from server)
- Reference the state hierarchy: Backend → URL → Local

**Tests:**
- Which test file(s) to update or create
```

#### Codegen

```
- Does this change require regenerating the API client? (Yes/No)
- If yes, note that `docker compose up codegen` must run after backend changes
- Note any new response types or request bodies that will be generated
```

#### Release Notes

```
- Is this a user-facing change? (Yes/No)
- If yes, draft the RELEASE_NOTES.md entry
```

### Good example

> **Backend:**
> - Add `deadline_mode` field to `Game` model (`CharField` with choices from a new `DeadlineMode` constants class in `service/common/constants.py`)
> - Add `fixed_deadline_time` and `fixed_deadline_timezone` fields to `Game` model
> - Extend `GameCreateSerializer` to accept the new fields, with cross-field validation in `validate()`: when `deadline_mode` is `"fixed_time"`, both time fields are required
> - Follow the existing serializer pattern in `service/game/serializers.py` — explicit field declarations, no `ModelSerializer`
> - Add the fields to `GameListSerializer` and `GameRetrieveSerializer` as read-only
> - No new views needed — existing `GameCreateView` and `GameRetrieveView` handle this
>
> **Frontend:**
> - Extend the `CreateStandardGameForm` in `packages/web/src/screens/Home/CreateGame.tsx` with deadline mode tabs
> - Add new Zod fields to `standardGameSchema` with conditional validation
> - Use the `Tabs` component from shadcn/ui for mode switching (already used in the same file for standard/sandbox tabs)
>
> **Codegen:** Yes — new fields in the Game response type
> **Release Notes:** Yes — "Added fixed-time deadline mode for games"

### Bad example

> We'll add some fields to the model and serializer, update the form, and run codegen.

This identifies no files, no patterns, no specific changes.

### When to identify files explicitly

Always name the specific files when:
- A new file needs to be created (e.g., a new app's `models.py`)
- An existing file needs significant changes (more than 5 lines)
- The file is non-obvious (e.g., `service/common/constants.py` for adding a new constants class)

For small, obvious changes (e.g., "add a field to `GameListSerializer`"), naming the file is sufficient — no need to specify the exact line.

---

## 4. Scope and Sizing

Every issue should result in a **single, reviewable PR**. If the work spans multiple concerns, split the issue.

### Single-PR scope

A well-scoped issue:
- Touches one logical concern (e.g., "add NMR extensions to game creation" — model + serializer + form + tests)
- Can be reviewed by reading the diff linearly without needing to jump between unrelated changes
- Has acceptance criteria that can all be verified in one pass

### When to split

Split the issue when:
- **Backend and frontend changes are independently deployable.** If the backend change can ship and provide value before the frontend consumes it, split into two issues.
- **The change touches multiple apps.** If you're modifying `game/`, `phase/`, and `order/` in one issue, consider whether each app's changes are independently meaningful.
- **The issue has both "infrastructure" and "feature" work.** For example, "add a new Django app with models + add the screen that uses it" should be two issues: one for the app, one for the screen.
- **The diff would exceed ~400 lines.** This is a soft limit, but large diffs are hard to review.

### Common split points in this codebase

| Concern | Split into |
|---|---|
| New backend feature + frontend consumption | Issue A: Backend (model, serializer, view, tests) → Issue B: Frontend (screen, components, tests) |
| New Django app | Issue A: App scaffolding (models, serializers, views, URLs, admin) → Issue B: Feature implementation |
| Database migration + application logic | Issue A: Migration (add field with default) → Issue B: Logic that uses the field |
| New component library addition | Issue A: Reusable component → Issue B: Screen that uses it |

### Sizing heuristics

| Size | Description | Example |
|---|---|---|
| **Small** | Single-layer change, <100 lines | Add a read-only field to an existing serializer |
| **Medium** | Full-stack change, 100-400 lines | Add a new feature to game creation (model + serializer + form + tests) |
| **Large** | Multi-concern, >400 lines | Should probably be split |

---

## 5. Dependencies

Dependencies describe what must be true **before** this issue can be implemented. They fall into two categories: **issue-level** and **infrastructure-level**.

### Issue-level dependencies

These are other issues that must be completed first. State them explicitly:

```
**Depends on:**
- #42 — Adds the `DeadlineMode` constants class that this issue uses
- #43 — Adds the `fixed_deadline_time` field to the Game model that the frontend reads
```

### Infrastructure-level dependencies

These are often overlooked. Check for:

| Dependency | When it applies | How to document |
|---|---|---|
| **Codegen** | Any backend change that modifies API response shape or adds endpoints | "Requires `docker compose up codegen` after backend merge" |
| **Migrations** | Any model field change | "Requires `docker compose run --rm service python3 manage.py migrate`" |
| **Environment variables** | Any new external service integration | "Requires new env var `FOO_API_KEY` — see .env.example" |
| **Railway deployment** | Any change that needs production config | "Requires Railway env var update before deploy" |
| **External service** | Any new API integration | "Requires API key from [service]" |

### Dependency graph in parent issues

When an issue is part of a milestone (parent issue), its dependencies should be documented both:
1. **In the issue itself** — "Depends on #42"
2. **In the parent issue** — as part of the dependency graph showing the order of work

---

## 6. Prerequisites

Prerequisites are **things the implementer needs before they can start**, distinct from code dependencies. These include:

- **Credentials** — API keys, OAuth client IDs, service accounts
- **Infrastructure** — Database access, Railway environment access, external service accounts
- **Data** — Test data, seed data, variant definitions
- **Knowledge** — Understanding of the adjudication service, Diplomacy game rules, phase resolution logic

### Example

```
**Prerequisites:**
- Access to the adjudication service API (currently hosted at `https://godip-adjudication.appspot.com`)
- Understanding of the phase resolution flow (see `service/phase/utils.py`)
- Firebase project access for push notification testing (see .env.example for required vars)
```

---

## 7. Risks and Open Questions

Every issue should surface uncertainties. Classify them as **blocking** (must be resolved before implementation) or **non-blocking** (can be resolved during implementation).

### Blocking risks

These prevent implementation from starting:

```
**Blocking:**
- [ ] The adjudication service API does not currently support retreat phase options — need to verify before implementing the retreat order UI
- [ ] Unclear whether `GamePauseSerializer` should reset the phase timer or preserve it — need product decision
```

### Non-blocking risks

These can be resolved during implementation but should be flagged:

```
**Non-blocking:**
- The `with_list_data()` QuerySet method may need additional prefetches for the new field — will assess during implementation
- Toast wording for the error case TBD — will follow existing patterns in `CreateGame.tsx`
```

### Codebase-specific risk areas

When scoping issues for this codebase, check for these common risks:

| Risk area | What to check |
|---|---|
| **N+1 queries** | Does the change add a new related field to a serializer? If so, the QuerySet's `select_related` / `prefetch_related` may need updating. Check `GameQuerySet.with_list_data()` and `with_retrieve_data()` in `service/game/models.py`. |
| **OpenAPI schema breaks** | Does the change modify a serializer's field names or types? This affects the generated frontend types. Run `docker compose up codegen` and check for TypeScript compilation errors. |
| **Phase resolution timing** | Does the change affect when phases resolve? The resolution logic in `service/phase/utils.py` and `service/game/models.py` (`get_scheduled_resolution`) is timing-sensitive. |
| **Permission composition** | Does the change need new permissions? Check whether existing permission classes in `service/common/permissions.py` can be composed or whether a new one is needed. Each permission class should check one thing. |
| **Generated code boundary** | Does the change require hand-editing files in `src/api/generated/`? This is never correct — changes must flow through the backend schema and codegen. |
| **Suspense boundary** | Does the change add data fetching to a component that doesn't have a Suspense boundary? If so, the component hierarchy may need restructuring. |
| **State location** | Does the change introduce local state that could live in the URL or be derived from the backend? Check the state hierarchy: Backend → URL → Local. |
| **Mutation dependency trap** | Does the change use a mutation inside `useEffect`? See the mutation dependency gotcha in CLAUDE.md — the mutation object is unstable and must be excluded from deps. |

---

## 8. Checklist

Use this checklist to verify an issue is well-formed before marking it ready for review.

### Problem statement
- [ ] Describes current behaviour (what happens now)
- [ ] Describes desired behaviour (what should happen)
- [ ] Identifies the affected screen, endpoint, or workflow
- [ ] Does not jump to a solution

### Acceptance criteria
- [ ] Every criterion describes observable behaviour, not implementation steps
- [ ] Frontend criteria reference user-visible outcomes
- [ ] Backend criteria reference API contracts (method, path, response shape, status codes)
- [ ] Edge cases are covered
- [ ] Criteria are independently testable

### Technical approach
- [ ] Identifies affected layers (model / serializer / view / component / hook)
- [ ] Names specific files for non-trivial changes
- [ ] References existing patterns in the codebase (with file paths)
- [ ] Includes codegen step if backend API shape changes
- [ ] Includes release notes entry if user-facing
- [ ] Does not prescribe implementation details beyond layer identification

### Scope
- [ ] Results in a single PR
- [ ] Diff is likely under ~400 lines
- [ ] If larger, split points are identified
- [ ] No unrelated changes bundled in

### Dependencies
- [ ] Issue-level dependencies listed with issue numbers
- [ ] Infrastructure dependencies noted (codegen, migrations, env vars, deployment)
- [ ] Dependency graph updated in parent issue if applicable

### Prerequisites
- [ ] Credentials and access requirements listed
- [ ] Required knowledge or context linked

### Risks and open questions
- [ ] Blocking risks identified with resolution owners
- [ ] Non-blocking risks flagged for awareness
- [ ] Codebase-specific risk areas checked (N+1, schema breaks, phase timing, permissions, generated code, Suspense, state location, mutation deps)
