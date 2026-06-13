# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# Metabase Analytics

## Creating native SQL questions

The Metabase MCP tools (`query`, `construct_query`) **do not support explicit joins** — only single-hop implicit FK traversal. For any query that needs more than one FK hop, use native SQL.

**Always write the SQL to a file, never inline it in a shell command.** Shell escaping corrupts SQL (`=` becomes `:`, DEL chars appear silently). The reliable pattern:

```python
# 1. Write SQL to /tmp/query.sql via the Write tool

# 2. Encode in a Python heredoc:
import json, base64

with open('/tmp/query.sql') as f:
    sql = f.read().strip()

payload = {
    'lib/type': 'mbql/query',
    'stages': [{'lib/type': 'mbql.stage/native', 'native': sql, 'template-tags': {}}],
    'database': DATABASE_ID   # 2 for the production diplicity DB
}
encoded = base64.b64encode(json.dumps(payload).encode('ascii')).decode('ascii')

# 3. Always roundtrip-assert before using:
decoded = json.loads(base64.b64decode(encoded))
assert decoded['stages'][0]['native'] == sql

print(encoded)
```

**Use the base64 immediately in the next tool call** — don't store it and reference it in a later message. The context window can corrupt long base64 strings between turns.

Always test with `execute_query` before `create_question`. If the query from the Bash output looks correct but `execute_query` fails with a syntax error, regenerate the base64 from the file rather than trying to fix the stored string.

To save to the root "Our analytics" collection, pass `collection_id=null`.

## Schema gotchas (phase / game tables)

- `phase_phase.completed_at` is **always NULL** — use `status = 'completed'` to identify resolved phases.
- `phase_phase.updated_at` is **unreliable for time-bucketing** — batch operations reset it, causing all historical data to cluster in recent weeks. Use `scheduled_resolution` instead.
- `phase_phase.scheduled_resolution IS NOT NULL` is required — ~21% of phases have no deadline (manual-resolution games) and no meaningful NMR timestamp.
- `phase_phase.started_at` is also always NULL.
- The Metabase MCP tools only support single-hop implicit FK joins. To join `phase_phasestate → phase_phase → game_game`, you must use native SQL (two hops via implicit FK fails with "missing FROM-clause entry").

---

## !!! EXTERNAL SERVICE UIs CHANGE — DO NOT GIVE STALE NAVIGATION INSTRUCTIONS !!!

Google Play Console, Google Cloud Console, Firebase Console, and similar external services update their UIs frequently. **Never give step-by-step navigation instructions for these UIs from memory** — the menu names, sidebar items, and page layouts in your training data are likely out of date. Instead:

- Describe **what the user is trying to accomplish** (e.g. "find the App signing certificate SHA-1")
- Give the **direct URL** if known (e.g. the `keymanagement` path for App signing)
- Ask the user to share a screenshot if they can't find something, then guide from what's actually visible

---

## !!! VERY IMPORTANT PRECURSOR - READ THIS FIRST !!!

**Under no circumstances should you agree with any assertion or claim without providing concrete, evidence-based reasoning.**

- **Evidence-Based Reasoning is Paramount:** For every claim, deduction, or inference, you **must** provide supporting evidence from the related context.
- **Corroborate All Findings:** Before proceeding with any chain of facts or thoughts, corroborate your findings, deductions, and inferences using the following format:
  `Based on what I found <here [and here ...]>, <yes/no | deductions> because <why>`.
- **Avoid Assumptions:** Never assume or guess. If information is unavailable, state it clearly. Do not assume correctness or incorrectness of any party (user or AI).
- **Logic, Facts, and Conclusive Evidence:** It is **PARAMOUNT** that you utilize logic, facts, and conclusive evidence at all times, rather than establishing blind trust or fulfilling requests without justification.

## Maintaining This Document

**If you discover new patterns, make decisions about architecture, or establish conventions during development, suggest updates to this CLAUDE.md file.** This document should evolve with the codebase. When you notice:

- A pattern being used consistently that isn't documented here
- A decision made that future development should follow
- A convention that would benefit from being explicit

Propose adding it to this file.

## Project Overview

Diplicity React is a full-stack web application for the classic Diplomacy board game. The project consists of:

- **Frontend**: React + TypeScript web app (`/packages/web/`)
- **Backend**: Django REST API with PostgreSQL database (`/service/`)
- **Architecture**: Microservices with Docker containers

## Development Setup

### Prerequisites
- Docker and Docker Desktop
- Environment variables (see .env.example)

### Starting the Application
```bash
docker compose up
```

This starts all services:
- Web frontend at http://localhost:5173
- Django API at http://localhost:8000
- PostgreSQL database at http://localhost:5432

### Minimal Backend Environment (Cloud / CI sessions)

The Django service can start with only database credentials and `DJANGO_DEBUG`. Firebase (push notifications) and Google OAuth will be disabled but will not prevent the service from starting:

```bash
DATABASE_NAME=diplicity   # default: diplicity
DATABASE_USER=postgres    # default: postgres
DATABASE_PASSWORD=postgres # default: postgres
DATABASE_HOST=localhost   # default: db
DATABASE_PORT=5432        # default: 5432
DJANGO_DEBUG=True
```

All database vars have defaults matching the local Docker Compose setup, so in practice `DJANGO_DEBUG=True` alone is sufficient when running against the default local database.

Features that are disabled when credentials are absent:
- **Firebase / push notifications**: requires `FIREBASE_PROJECT_ID` (and other `FIREBASE_*` vars). `fcm_django` is removed from `INSTALLED_APPS` and the `/devices/` endpoint is not registered.
- **Google OAuth login**: requires `GOOGLE_CLIENT_ID`. Login attempts will fail with an authentication error but the service continues to run.

### Native (non-Docker) Workflow — Claude Code on the web

Cloud sessions run without Docker. The `.claude/hooks/session-start.sh` SessionStart hook provisions everything natively so tests, linters, build, and codegen work out of the box. It is idempotent and re-runs cheaply on resume. What it sets up:

- **Backend venv**: a Python 3.12 virtualenv at `service/.venv` with `requirements.txt` + `dev_requirements.txt` installed. Django 6 requires Python 3.12+, but the system default `python3` is 3.11 — **always use `service/.venv/bin/python`** (the hook also prepends it to `PATH` via `$CLAUDE_ENV_FILE`, so a plain `python`/`pytest`/`pip` resolves to the venv).
- **PostgreSQL**: the native cluster is started and a `diplicity` database (role `postgres`/`postgres`) is created and migrated. The hook exports `DATABASE_HOST=127.0.0.1` and the other `DATABASE_*` vars for the session, so `manage.py` and `pytest` connect automatically.
- **Frontend**: `npm install` in `packages/web`.
- **Railway CLI**: installed via npm when `RAILWAY_API_TOKEN` is set.

Manual equivalents (if running outside the hook):
```bash
# Backend env (already exported by the hook in cloud sessions)
export PATH="$PWD/service/.venv/bin:$PATH"
export DATABASE_HOST=127.0.0.1 DATABASE_PORT=5432 \
       DATABASE_NAME=diplicity DATABASE_USER=postgres DATABASE_PASSWORD=postgres

cd service
python manage.py check
python -m pytest -q --create-db        # pytest-django builds test_diplicity
```

**SQLite is not viable.** Some migrations contain Postgres-only raw SQL (e.g. `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`), which SQLite rejects with a syntax error during the test-DB build. Use the native PostgreSQL cluster, not a SQLite `DATABASE_URL`.

**Railway production access requires network allowlisting.** Installing the CLI is not enough: every `railway` command (and `/prod-query`, `/debug-production`) reaches production through Railway's hosts, which are not in the **Trusted** default allowlist. To enable them, edit the Claude Code on the web **environment** (cloud icon → environment selector → gear icon), set **Network access** to **Custom**, and add to **Allowed domains**:

```
*.railway.com
*.railway.app
```

`backboard.railway.com` is the GraphQL API behind `whoami`/`status`/`logs`; `railway run` (used by `/prod-query`) routes through additional Railway hosts, so the wildcards cover both. **Also tick "Also include default list of common package managers"** — otherwise the allowlist becomes only those two lines and the SessionStart hook's `npm install`/`pip install` break. Without this, commands fail with `Host not in allowlist` / "error decoding response body". (**Full** network access also works but allows any domain.)

**Codegen reproducibility.** `manage.py spectacular` + `orval` regenerate `service/openapi-schema.yaml` and `packages/web/src/api/generated/endpoints.ts`. To reproduce the committed output byte-for-byte the generating environment must match production config, because two switches change the schema:
- `DJANGO_DEBUG` must be **off** — when on, the DEBUG-gated `/api/test-sentry/` endpoint is added to the schema.
- `FIREBASE_PROJECT_ID` must be **set** — when absent, `fcm_django` is dropped from `INSTALLED_APPS`, removing `/devices/` and the `FCMDevice` schema.

A clean `git diff` after codegen in a cloud session (no Firebase, DEBUG off) shows only the `/devices/` + `FCMDevice` removal; that is environmental, not a stale-checkout signal.

## Key Commands

### Frontend (React/TypeScript)
Navigate to `/packages/web` for these commands:
```bash
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint
npm run test         # Vitest tests
npm run storybook    # Storybook at http://localhost:6006
```

### Backend (Django)
Navigate to `/service` for these commands:
```bash
docker compose run --rm service python3 manage.py migrate
docker compose run --rm service python3 manage.py runserver
```

### Docker Services
```bash
docker compose up codegen      # Generate API client from OpenAPI schema
docker compose up test-service # Run Django tests in container
```

### Apple / Capacitor iOS Credentials

The Team ID is `G76UP8FNMS` (stored in `.env` as `CAPACITOR_IOS_TEAM_ID`).

**Code signing** uses Xcode automatic signing. The Apple Distribution certificate (created 2026-02-22, expires 2027-02-22) and its private key are in the local macOS Keychain. Xcode manages provisioning profiles automatically; there is no manually-created profile checked into the repo.

**Push notifications** use the APNs authentication key `AuthKey_C6JM6K4J2X.p8` (Key ID: `C6JM6K4J2X`), which is in the repo root but gitignored. This key is independent of distribution certificates and does not need rotation when certificates change.

## General Development Guidelines

1. **Follow existing code patterns and conventions** - Consistency is key
2. **Use TypeScript for type safety** - Never use `any` types
3. **Run linting before submitting changes** - Fix all violations properly
   - Frontend: `npm run lint` (only on changed files when possible)
   - Backend: Use appropriate Python linters
4. **Run tests to validate changes** - Do not run full test suite
   - Always run single test files at a time for faster feedback
   - Frontend: `npm run test <filename>`
   - Backend: `docker compose run --rm service python3 -m pytest <test_file> -v`
5. **Never disable lint violations** - Fix the root cause instead
   - DO NOT use `eslint-disable`, `ts-ignore`, or similar suppression comments
   - If you cannot resolve a lint issue, explain what you tried and ask for guidance
   - The only acceptable outcomes are: the violation is properly fixed OR you report the issue
6. **Prefer composition over effects** - Minimize useEffect usage in React
7. **Use proper error handling** - Catch and handle errors appropriately
8. **Write tests alongside features** - Not as an afterthought
9. **Update RELEASE_NOTES.md for user-facing changes** - When implementing features, improvements, or bug fixes that players would notice or care about, add an entry to RELEASE_NOTES.md. Internal refactors, code cleanup, or developer-only changes do not need release notes.

---

# Frontend Development (`/packages/web/`)

## Architecture Overview

- **State Management**: React Query (TanStack Query) for server state - no Redux
- **Routing**: React Router for navigation
- **UI Components**: shadcn/ui with Tailwind CSS
- **Testing**: Vitest + Testing Library
- **Build**: Vite with TypeScript compilation

### Generated Files

Files in `src/api/generated/` are **auto-generated by orval** from the OpenAPI schema. Never manually edit these files - any changes will be overwritten when `docker compose up codegen` runs. If you see docstrings or comments in generated code, they come from the Django views' docstrings (extracted by DRF Spectacular into the OpenAPI schema).

## Data & State Management

### React Query for All Server State

- Use `useXxxSuspense` hooks for data fetching - never the non-suspense variants
- Use `useXxxMutation` hooks with `mutateAsync` for writes
- No Redux - do not use Redux for any purpose

### Mutations in useEffect Dependencies

**Never include mutation objects in useEffect dependency arrays.** The mutation object from `useXxxMutation()` gets a new reference whenever its internal state changes (idle → pending → success/error), causing infinite loops:

```typescript
// BAD - causes infinite loop
const createMutation = useCreateMutation();
useEffect(() => {
  if (condition) {
    createMutation.mutateAsync({ data });
  }
}, [condition, createMutation]); // createMutation changes on every mutation state change

// GOOD - only include stable values
const createMutation = useCreateMutation();
useEffect(() => {
  if (condition) {
    createMutation.mutateAsync({ data });
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync is stable
}, [condition]);
```

The `mutateAsync` function itself is stable, but the containing mutation object is not. When you must use a mutation inside useEffect, omit the mutation from dependencies and add an eslint-disable comment explaining why.

### State Hierarchy

1. **Backend** - Source of truth for all domain data
2. **URL** - Navigation state, selected tabs, filters (via `useSearchParams`, `useParams`)
3. **Local state** - Pure UI concerns only (e.g., `isEditingName`, `selectedItems` before submission)

If state could reasonably be derived from the backend or URL, it should be.

### Suspense Data Guarantees

Prefer Suspense data fetching so components can assume data exists. Avoid optional chaining on data that should always be present after render.

```typescript
// Good - data guaranteed by Suspense
const { data: games } = useGamesListSuspense();
games.map(game => ...);

// Avoid - unnecessary guard for Suspense data
const { data: games } = useGamesListSuspense();
games?.map(game => ...);
```

### Entity Data from URL

When a component needs entity data based on a URL param, fetch it directly:

```typescript
const { gameId } = useRequiredParams<{ gameId: string }>();
const { data: game } = useGameRetrieveSuspense(gameId);
```

Do not use React Context to share entity data. Each component should fetch what it needs - React Query handles deduplication and caching.

## Component Patterns

### File Organization

Keep it flat:
- All screens live directly in `src/screens/` (or subdirectories by feature like `screens/Home/`, `screens/GameDetail/`)
- All shared components live directly in `src/components/`

### Suspense Wrapper Pattern

Every screen that fetches data should have a Suspense wrapper:

```typescript
const MyScreen: React.FC = () => {
  const { data } = useDataSuspense();
  return <div>...</div>;
};

const MyScreenSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="My Screen" />
    <Suspense fallback={<div></div>}>
      <MyScreen />
    </Suspense>
  </ScreenContainer>
);

export { MyScreenSuspense as MyScreen };
```

### Inline Over Extract

- **Inline sub-components** when they're only used in one place
- **Inline utility functions** at the top of the file when specific to that component
- Only extract to separate files when genuinely shared across multiple screens

### Prop Types

- Always provide explicit interface definitions for component props
- Infer types elsewhere (function return types, local variables)

```typescript
interface GameCardProps {
  game: Game;
  variant: Variant;
}

const GameCard: React.FC<GameCardProps> = ({ game, variant }) => {
  // Infer types for local variables
  const playerCount = game.members.length;
  ...
};
```

### Layout Architecture

Layouts are applied at the **router level**, not within individual screens:

**Router.tsx** - Layout wrappers use `<Outlet />`:
```typescript
const HomeLayoutWrapper: React.FC = () => (
  <HomeLayout>
    <Outlet />
  </HomeLayout>
);

const GameDetailLayoutWrapper: React.FC = () => (
  <GameDetailLayout>
    <Outlet />
  </GameDetailLayout>
);
```

**Screens** - Return content only (no layout wrapper). Include their own header as part of their children:
```typescript
const OrdersScreen: React.FC = () => {
  return (
    <div className="flex flex-col h-full">
      <GameDetailAppBar title={<PhaseSelect />} onNavigateBack={() => navigate("/")} />
      <div className="flex-1 overflow-y-auto">
        <Panel>...</Panel>
      </div>
    </div>
  );
};
```

**Stories** - Wrap screens in their layout for proper rendering:
```typescript
const meta = {
  render: () => (
    <GameDetailLayout>
      <OrdersScreen />
    </GameDetailLayout>
  ),
};
```

## UI Guidelines

### Component Library

- Use ShadCN components over raw HTML elements
- Use Lucide icons (imported from `lucide-react`)
- Use `Notice` component for empty states
- Use `ScreenCard` for home screen content

### Tailwind CSS

Only add classes that actually do something. Question every class:

- Does this override a default that needs overriding?
- Is this spacing not already handled by a parent's `gap` or component's built-in spacing?
- Is this size not already set by the component's `size` prop?

```typescript
// Good - minimal, intentional
<div className="space-y-4">

// Avoid - redundant classes
<div className="flex flex-row items-stretch min-w-0 space-y-4">
```

**Examples of unnecessary classes to avoid**:
- `min-w-0` when the element already has appropriate width constraints
- `flex-shrink-0` when shrinking behavior is already handled
- `h-8 w-8` when `size="icon"` already sets dimensions
- `ml-4` when `gap` utilities already handle spacing
- `className="h-4 w-4"` on icons when the default size is appropriate

Trust component defaults - shadcn/ui components have sensible defaults; only override when necessary.

## Forms

Use React Hook Form with Zod for all forms:

```typescript
const schema = z.object({
  name: z.string().min(1, "Required"),
});

type FormValues = z.infer<typeof schema>;

const MyForm: React.FC = () => {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "" },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </form>
    </Form>
  );
};
```

## User Feedback

### Mutations

Show toast feedback for user-triggered mutations unless the UI change itself provides clear feedback:

```typescript
const handleCreate = async (data: FormValues) => {
  try {
    await createMutation.mutateAsync({ data });
    toast.success("Created successfully");
    navigate("/");
  } catch {
    toast.error("Failed to create");
  }
};
```

Skip toasts when:
- A checkbox toggle immediately shows the new state
- Inline editing where the UI confirms the change

### Query Errors

Use `QueryErrorBoundary` as the complement to Suspense for handling query errors. Wrap `<Suspense>` with `<QueryErrorBoundary>` in the screen's Suspense wrapper:

```typescript
const MyScreenSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="My Screen" />
    <QueryErrorBoundary>
      <Suspense fallback={<div></div>}>
        <MyScreen />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);
```

This keeps the screen header visible when an error occurs, with the error UI appearing in the content area. The `QueryErrorBoundary` integrates with React Query's error reset mechanism, so the "Try Again" button will refetch failed queries.

## Navigation

- Use React Router hooks: `useNavigate`, `useParams`, `useSearchParams`, `useLocation`
- Use `Link` component for declarative navigation
- Store meaningful state in URL when it should be shareable/bookmarkable

### URL Parameters

Use `useRequiredParams` for typed route params that are guaranteed by the route structure:

```typescript
// For routes like /game/:gameId/chat/:channelId
const { gameId, channelId } = useRequiredParams<{ gameId: string; channelId: string }>();
```

This eliminates the need for runtime null checks when the route guarantees the param exists.

## Mock Data (MSW + Fixture Registry)

The frontend has an MSW (Mock Service Worker) layer that serves canonical fixture data for every API endpoint, so the full app can run with no backend at all:

```bash
cd packages/web
npm run dev:mocks   # Vite dev server at http://localhost:5173 with all API calls mocked
```

In mock mode the app auto-seeds auth tokens (logged in as "Mock Player"). To see logged-out screens, set `localStorage.setItem("mock:loggedOut", "true")` and clear tokens (the screenshot script's `--logged-out` flag does this).

### Fixture registry — check before creating mocks

**`src/mocks/fixtures/index.ts` is the canonical fixture registry and the single source of truth for mock scenarios. Always check it before creating new mock data — only add a fixture when no existing one covers the scenario.** Fixture explosion is the failure mode this registry exists to prevent.

Registered game fixtures (the fixture's game `id` doubles as the URL slug, e.g. `/game/active-movement/phase/101/orders`):

| Fixture | Game ID | Scenario |
|---|---|---|
| `pendingGameNoPlayers` | `pending-no-players` | Pending, 0 members, joinable |
| `pendingGameSomePlayers` | `pending-some-players` | Pending, 3/7 players incl. current user (creator) |
| `pendingGameAlmostFull` | `pending-almost-full` | Pending, 6/7 players incl. current user |
| `activeGameMovement` | `active-movement` | Spring 1901 movement; current user (England) has 2/3 orders in; chat channels with unread |
| `activeGameRetreat` | `active-retreat` | Fall 1901 retreat; England army dislodged from Norway |
| `activeGameBuild` | `active-build` | Fall 1901 adjustment; England can build 1 unit |
| `activeGameDrawProposal` | `active-draw-proposal` | Active game with an open draw proposal, current user hasn't voted |
| `finishedGameSolo` | `finished-solo` | Completed; current user won a solo victory |
| `finishedGameDraw` | `finished-draw` | Completed; 3-way draw incl. current user |
| `gameNotJoined` | `not-joined` | Active game the current user is not a member of |

Structure of `src/mocks/`:

- `fixtures/index.ts` — the registry (`gameFixtures`, `fixtureByGameId`)
- `fixtures/games.ts` — the game scenarios; `fixtures/builders.ts` — helpers (`makeGame`, `makePhase`, `makeOrder`, …)
- `fixtures/classical.ts` + `fixtures/data/` — the real classical variant (dumped from the actual API: variant JSON, 2MB map SVG, nation flags), so maps render exactly like production
- `handlers.ts` — MSW request handlers serving the registry; `browser.ts` — worker startup + auth seeding
- `legacy.ts` — older standalone mock objects still used by some unit tests/stories; prefer the fixture registry for new work

Known limitation: `GET /game/:id/options/` returns an empty `OrderOptionsResponse`, so the interactive order-creation wizard has no options under mocks. Read-only rendering of orders, phases, maps, chat, and draw proposals is fully supported.

MSW is dev-only: `main.tsx` dynamically imports the worker only when `VITE_MOCKS=true`, and the chunk is dead-code-eliminated from production builds. Vitest does not use MSW (unit tests mock the generated hooks directly).

## UI Verification & PR Screenshots (Playwright)

Playwright is installed in `packages/web/` for ad-hoc UI verification and PR screenshots — there is **no** Playwright test suite, no assertions, no CI step. It is a tool for producing visual evidence of UI changes.

```bash
cd packages/web
npm run dev:mocks &   # 1. start the dev server with mock data

# 2. screenshot any route (script auto-picks a working Chromium)
npm run screenshot -- / /tmp/shots/my-games.png
npm run screenshot -- /game/active-movement/phase/101/orders /tmp/shots/orders.png
npm run screenshot -- /game/active-build/phase/303/orders /tmp/shots/mobile.png --viewport 390x844
```

Options: `--viewport WxH` (default 1280x800), `--full-page`, `--logged-out`, `--wait MS`, `--base URL`. The script prints page errors to the console — treat any `[pageerror]`/`[console.error]` about the app itself as a signal the fixture or the change is broken.

**Cloud-environment browser caveat:** `npx playwright install chromium` fails in Claude Code on the web because `cdn.playwright.dev` is not in the network allowlist. The screenshot script handles this automatically by falling back to the `@sparticuz/chromium` binary (shipped via npm, extracted to `/tmp/chromium`). Do not burn time trying to make `playwright install` work; the fallback is the supported path in cloud sessions.

### Attaching screenshots to a PR description

GitHub PR bodies can embed images by URL. Since the API cannot upload attachments, commit the screenshots to a dedicated **screenshots branch** (never merged) and reference them by commit-pinned raw URL:

```bash
git checkout --orphan screenshots/<feature-name>
git rm -rf . && mkdir -p shots && cp /tmp/shots/*.png shots/
git add shots && git commit -m "Screenshots for <feature>" && git push -u origin screenshots/<feature-name>
git checkout <your-feature-branch>
```

Then embed in the PR body with the commit SHA (stable even if the branch is later deleted):

```markdown
![orders screen](https://raw.githubusercontent.com/johnpooch/diplicity-react/<commit-sha>/shots/orders.png)
```

## Frontend Best Practices Summary

1. **Component Design**:
   - Check for existing components before creating new ones
   - Keep components under 200 lines
   - Use compound component patterns for complex UIs

2. **Data Management**:
   - Use TanStack Query for new data fetching features
   - Always validate API responses with Zod schemas
   - Use `parseOnlyInDev` pattern to prevent production crashes

3. **React Patterns**:
   - Minimize useEffect usage - prefer derived state and event handlers
   - Use React 19 features (Context as provider, no forwardRef)
   - Let React 19 handle memoization automatically

---

# Backend Development (`/service/`)

## Architecture Overview

- **Framework**: Django with Django REST Framework
- **API**: RESTful API with camel case conversion
- **Authentication**: JWT tokens with Google OAuth integration
- **Database**: PostgreSQL with Django ORM
- **Background Tasks**: Management commands for game resolution

## Style Guide

### General

- **Comments**: Do not add docstrings or comments. This applies to test code too — do
  not annotate assertions to explain their values. In particular, when a change shifts a
  query-count (or similar magic-number) assertion, update the number only; do not add a
  comment explaining the delta.

### Imports

- **Always place imports at the top of the file** - Do not use inline imports inside methods
- **Circular imports**: When circular imports are unavoidable, use `apps.get_model()` at module level:
  ```python
  from django.apps import apps
  Phase = apps.get_model("phase", "Phase")
  ```

### Business Logic Location

- **Managers**: Complex creation/modification logic belongs in manager methods (e.g., `Game.objects.create_from_template()`)
- **Serializers**: Should orchestrate calls to managers and handle request-specific logic (e.g., user validation, permissions)
- **Views**: Should remain thin, delegating to serializers and managers

### Project Structure

The project is broken down into apps, where each app is responsible for a single core concept, e.g. `game`, `order`, `user_profile`, etc.

**Standard App Structure:**
Each app should contain these files:
- `models.py` - Data models with custom QuerySets and Managers
- `serializers.py` - DRF serializers using base `Serializer` class
- `views.py` - API views using DRF generics
- `urls.py` - URL routing
- `conftest.py` - Test fixtures (pytest fixtures)
- `tests.py` - Test cases focusing on API endpoints
- `admin.py` - Django admin configuration
- `utils.py` - Helper functions (when needed)

## Views

Views should be simple and should leverage DRF generic views where appropriate. The `check_permissions` method should be used to carry out initial permission checks for the request. Mixins should be used to provide context to the views and serializers.

Follow this pattern:
- Use `generics.ListAPIView`, `generics.CreateAPIView`, `generics.RetrieveAPIView`, etc.
- Apply permission classes: `[permissions.IsAuthenticated, IsActiveGame, IsGameMember]`
- Use mixins from `common.views` for shared functionality (`SelectedGameMixin`, `CurrentGameMemberMixin`, etc.)
- Keep view logic minimal - delegate to managers and querysets

## Serializers

Serializers should use the standard `Serializer` base class over the `ModelSerializer` base class. They should be kept as simple as possible.

Follow this pattern:
- Explicitly define fields rather than using `ModelSerializer` auto-generation
- Use `read_only=True` for computed/derived fields
- Import and compose other serializers for related objects
- Keep validation logic in custom `validate_*` methods
- Use context from views (`self.context["request"]`, `self.context["game"]`, etc.)

## Models

Models have two responsibilities: (1) defining the fields of the data structure; (2) defining properties for conveniently accessing related entities and deriving data.

Query optimization code should be defined on a custom QuerySet class. Follow this pattern:

```python
class ModelQuerySet(models.QuerySet):
    def business_filter_method(self, param):
        return self.filter(...)

    def with_related_data(self):
        return self.select_related(...).prefetch_related(...)

class ModelManager(models.Manager):
    def get_queryset(self):
        return ModelQuerySet(self.model, using=self._db)

    def business_filter_method(self, param):
        return self.get_queryset().business_filter_method(param)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

class Model(BaseModel):
    objects = ModelManager()

    @property
    def derived_property(self):
        return self.some_calculation()
```

## Utils

Logic which does not naturally belong in the serializers, views, or models should be defined in the `utils.py` file.

---

# Testing

## Frontend Tests

Navigate to `/packages/web` and run:
```bash
npm run test              # Run all tests
npm run test <filename>   # Run specific test file (preferred)
```

## Backend Tests

To run all backend tests:
```bash
docker compose run --rm service python3 -m pytest -v
```

To run a specific test file:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py -v
```

To run a specific test function:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::test_create_game_success -v
```

To run a specific test method of a test class:
```bash
docker compose run --rm service python3 -m pytest game/tests/test_game_create.py::TestClass::test_create_game_success -v
```

## Backend Testing Patterns

Shared test fixtures live in the **root `service/conftest.py`** — this is the single place to look for (and add) fixtures. Per-app `conftest.py` files exist only for fixtures that are genuinely app-local:

- `login/conftest.py` — Google/Apple auth and token mocks (patch login internals)
- `integration/conftest.py` — autouse procrastinate mock + extra users/clients for 7-player games
- `nation/conftest.py` — draft variants and flag SVG data for nation flag tests
- `variant/conftest.py` — SVG map builders (`make_dsvg`, `make_godip_svg`, etc.)

Before adding a fixture to a per-app conftest, check whether it belongs in the root conftest instead.

### Fixture Naming Convention

- **`*_factory`** — fixtures that return a callable which creates objects on demand (`game_factory`, `phase_factory`, `member_factory`, `sandbox_game_factory`, `user_factory`, `authenticated_client_factory`). Always use this suffix for callable-returning fixtures; do not use `make_*` or bare names.
- **Session-scoped reference data** — read-only lookups named `<variant_id>_variant`, `<variant_id>_<name>_nation`, `<variant_id>_<name>_province` (e.g. `classical_england_nation`, `italy_vs_germany_kiel_province`). These are created once per session via `django_db_blocker` — never mutate them in tests.
- **Session-scoped users/clients** — `primary_user`, `secondary_user`, `tertiary_user` and `authenticated_client`, `authenticated_client_for_secondary_user`, `unauthenticated_client`. These persist across the whole session — never mutate or delete them; use `user_factory` for disposable users.
- **Scenario fixtures** — descriptive nouns returning ready-made objects (`active_game_with_phase_state`, `game_with_two_members`, `order_active_game`).
- **`mock_*`** — fixtures that patch external behavior (`mock_send_notification_to_users`, `mock_immediate_on_commit`).

### Performance

- The root conftest forces `MD5PasswordHasher` for tests (session autouse `override_test_settings`), so `create_user` is cheap. Do not create users with the production hasher in tests.
- Prefer the session-scoped users/clients and variant lookups over creating new ones per test.
- **Full suite runs: use `pytest -n auto`** (pytest-xdist, in `dev_requirements.txt`). The suite is parallel-safe: each worker gets its own database (`test_diplicity_gwN`), there are no live-server/port-binding tests, no FileField/media writes, and all external I/O (Resend email, Google/Apple auth, Firebase notifications) is mocked. CI runs with `-n auto`. It is deliberately not in `addopts` so that single-file runs (the preferred local feedback loop) skip the worker startup cost.
- **Use `pytest --reuse-db` locally** to skip recreating the test database (and rerunning migrations, ~6s) between runs. Pass `--create-db` again after pulling new migrations. Works with `-n auto` too.
- No test uses `django_db(transaction=True)` — keep it that way unless a test genuinely needs real transaction semantics (`on_commit`, concurrency); use the `mock_immediate_on_commit` fixture instead of transactional tests.

Follow this testing pattern:
- Create pytest fixtures in the root `conftest.py` that return callable factory functions
- Focus on API endpoint testing rather than unit testing individual methods
- Use fixtures like `@pytest.fixture def factory_function(db, other_fixtures): def _create(...): return Model.objects.create(...); return _create`
- Test comprehensive endpoint behavior including permissions, validation, and data transformations
- Add performance tests to ensure N+1 query issues are avoided
- For complex logic in utils files, create separate test classes

---

# Production Debugging

The application is deployed on **Railway** (project: `devoted-rejoicing`, service: `diplicity-react`).

## Railway CLI

Two separate environment variables control Railway access in cloud sessions:

| Variable | Scope | Used for |
|---|---|---|
| `RAILWAY_API_TOKEN` | Account-scoped | `railway whoami`, `railway status`, `railway logs` — auth and observability |
| `RAILWAY_TOKEN` | Project-scoped | `railway run` — inject production env vars to run management commands locally |

**IMPORTANT — token conflict**: When both variables are set, the Railway CLI v5 gives `RAILWAY_TOKEN` priority and uses it for all commands, including account-scoped ones like `whoami`/`status`/`logs`. This causes those commands to fail with an "Unauthorized" error because `RAILWAY_TOKEN` is project-scoped, not account-scoped.

**Always unset the irrelevant token per command using `env -u`:**

```bash
# Account-scoped commands — unset RAILWAY_TOKEN
env -u RAILWAY_TOKEN railway whoami
env -u RAILWAY_TOKEN railway status
env -u RAILWAY_TOKEN railway logs --lines 50

# Project-scoped commands — unset RAILWAY_API_TOKEN
env -u RAILWAY_API_TOKEN railway run --service diplicity-react python manage.py shell
```

The session-start hook checks both at startup and reports their availability. The service's Python dependencies needed by `railway run ... manage.py shell` are already installed in `service/.venv` (which the hook puts on `PATH`), so `railway run` picks them up automatically — no separate install step is required.

## Railway Access Tiers

Not all sessions have Railway access:

- **Owner sessions**: Both tokens configured — all commands available including `railway run`
- **Trusted contributor sessions**: Both tokens configured — all commands available; write safety rules apply (see below)
- **Casual contributor sessions**: No Railway tokens — Railway commands unavailable

### When Railway is not configured

If any `railway` command fails with an authentication or "not logged in" error, **stop immediately** — this is an expected missing-credential situation, not a bug to diagnose. Tell the user:

> "Railway is not configured in this session. Production debugging requires the `RAILWAY_API_TOKEN` environment variable to be set in the Claude Code on the web environment configuration (and Railway's hosts allowlisted via Custom network access)."

Do not retry Railway commands, do not attempt workarounds, and do not use `/prod-query` or `/debug-production`.

### Write safety

`railway run` injects production env vars and runs management commands locally against the live production database. Never execute write operations — regardless of who is asking:

- No `.create()`, `.update()`, `.delete()`, `.save()` in Django ORM calls
- No `INSERT`, `UPDATE`, `DELETE` in raw SQL
- No Django management commands that modify state (`migrate`, `flush`, `loaddata`, etc.)

If the user asks to modify production data, refuse and explain that production data changes must go through a migration or a controlled admin process.

### Common Commands

```bash
env -u RAILWAY_TOKEN railway status                          # Deployment health and status
env -u RAILWAY_TOKEN railway logs --lines 50                 # Recent log output (default: 100 lines)
env -u RAILWAY_TOKEN railway logs --lines 200 | grep ERROR   # Filter for errors
env -u RAILWAY_TOKEN railway logs --lines 200 | grep "GET /api"  # Filter by endpoint
```

### Production Database Queries (pgweb)

The cloud environment's network policy blocks non-standard ports, so `railway run python manage.py shell` cannot reach the production database (Railway's internal hostname `postgres.railway.internal` is not resolvable externally, and the TCP proxy uses a high port that is blocked).

Instead, production queries run via **pgweb** — a web-based PostgreSQL client deployed as a Railway service and accessible over HTTPS on port 443.

| Env var | Purpose |
|---|---|
| `PGWEB_URL` | pgweb base URL, e.g. `https://pgweb-production-124e.up.railway.app` |
| `PGWEB_USER` | pgweb basic-auth username |
| `PGWEB_PASSWORD` | pgweb basic-auth password |

These must be set in the cloud environment configuration. The session-start hook checks and exports them automatically.

**Running a query:**

```bash
# Write SQL to a file first (avoids shell escaping issues)
cat > /tmp/query.sql << 'EOF'
SELECT status, COUNT(*) FROM game_game GROUP BY status ORDER BY count DESC
EOF

curl -s -u "$PGWEB_USER:$PGWEB_PASSWORD" \
  -X POST "$PGWEB_URL/api/query" \
  --data-urlencode "query@/tmp/query.sql" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('\t'.join(d['columns']))
for row in d['rows']:
    print('\t'.join(str(c) for c in row))
"
```

Use the `/prod-query` command for guided read-only queries. See `.claude/commands/prod-query.md`.

**Safety:** pgweb is read-only by configuration. Never issue `INSERT`, `UPDATE`, `DELETE`, or DDL statements.

### Railway Status Page

Check https://status.railway.com for platform-wide incidents. Use WebFetch to check this during debugging.

---

# PR Staging Environments

PRs can be deployed to an isolated staging environment with a copy of the production database. This is useful for:
- Testing database migrations against real production data before merging
- Validating end-to-end behavior with realistic data
- Manual QA of features that need backend changes

## How to Deploy

Add the `deploy-to-staging` label to a PR. A GitHub Actions workflow (`.github/workflows/pr-staging.yml`) will:
1. Find or create a Railway environment (`staging-pr-<number>`)
2. Generate a Railway domain for the staging backend
3. Clone the production database via `pg_dump`/`pg_restore`
4. Configure CORS/ALLOWED_HOSTS for the staging domain
5. Deploy the PR branch to the staging backend
6. Comment on the PR with the frontend preview and staging backend URLs

The frontend Netlify deploy preview automatically derives the staging backend URL from the PR number at build time (`packages/web/netlify.toml` uses Netlify's `REVIEW_ID` env var).

## How to Redeploy

Add the `deploy-to-staging` label again. The workflow reuses the existing environment and re-clones the production database.

## Teardown

Staging environments are automatically deleted when the PR is closed or merged.

## Auth on Staging

Use email/password login. Google OAuth is not configured for staging environments.

## Key Details

- **One staging environment per PR** (no pool of shared environments)
- Railway GraphQL API is used for all environment management (not the Railway CLI)
- The `RAILWAY_ACCOUNT_TOKEN` GitHub secret is an account-level token (not a project token)
- Railway project: `devoted-rejoicing` (ID: `39039c2c-4f5d-4a37-8c0d-f8e4279fce61`)

---

# API Development

The API schema is auto-generated using DRF Spectacular:
```bash
docker compose up codegen
```

This generates OpenAPI schema and TypeScript client code for the frontend.

---

# Android Development (Capacitor)

## Real Device Testing (Preferred)

**Always use the physical Pixel 8a for Android testing — do not use the emulator.** The emulator consumes too much RAM; the real device is the preferred testing target.

- **Bundle ID / Application ID**: `com.diplicityreact.app`
- **Android Project**: `packages/web/android/`
- **Connected device UDID**: `46101JEKB13333`

## Environment Prerequisites

The following must be installed on the development machine:

- **JDK 21**: `sudo apt install openjdk-21-jdk` (Capacitor Android 8 requires Java 21; Java 17 is not sufficient)
- **Android Studio**: `sudo snap install android-studio --classic` (bundles the Android SDK, build-tools, and platform-tools including ADB)
- **`ANDROID_HOME`**: Set to `$HOME/Android/Sdk` — add to `~/.bashrc`:
  ```bash
  export ANDROID_HOME="$HOME/Android/Sdk"
  export PATH="$ANDROID_HOME/platform-tools:$PATH"
  ```

## ADB Device Setup (Linux)

Linux requires a udev rule to access the Pixel over USB:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0664", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-android.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG plugdev $USER
# Log out and back in, then unplug/replug the device
adb kill-server && adb devices
# Accept the "Allow USB debugging" prompt on the phone
```

## Build & Deploy Workflow

**IMPORTANT**: All Capacitor commands must be run from `packages/web/` — they use the `capacitor.config.ts` in that directory and will fail if run from the repo root.

```bash
# All commands run from packages/web/
cd packages/web
npm run build                          # Build the web app
ANDROID_HOME=$HOME/Android/Sdk npx cap sync android   # Sync web assets to Android project
ANDROID_HOME=$HOME/Android/Sdk npx cap run android --target 46101JEKB13333  # Build and deploy to device
```

## Version Management

- `versionName` is read from `packages/web/package.json` `version` field (via `rootProject.projectDir/../package.json` in `build.gradle`)
- `versionCode` is a Unix timestamp (seconds), auto-generated per build
- Both are set in `android/app/build.gradle` — no manual editing needed

## Firebase Cloud Messaging (Android)

Android push notifications use Firebase Cloud Messaging via the `@capacitor-firebase/messaging` plugin (same plugin as iOS). The Android-specific config file `google-services.json` must be present at `packages/web/android/app/google-services.json` (gitignored).

To set up:
1. Go to [Firebase console](https://console.firebase.google.com/) → project `diplicity-react` → Project settings → Add app → Android
2. Enter package name `com.diplicityreact.app`
3. Download `google-services.json` and place it at `packages/web/android/app/google-services.json`

The `android/app/build.gradle` conditionally applies the `com.google.gms.google-services` plugin when this file exists — no manual Gradle editing needed.

Runtime `POST_NOTIFICATIONS` permission for Android 13+ is handled by `FirebaseMessaging.requestPermissions()` in `messaging-native.ts`.

## Google Sign-In

Android Google Sign-In uses the existing `VITE_GOOGLE_CLIENT_ID` (web client ID) as the `webClientId` in `SocialLogin.initialize()`. No separate Android client ID is needed in app code.

However, an **Android OAuth client must be registered in Google Cloud Console** (Credentials page, same project as the web client) with:
- Package name: `com.diplicityreact.app`
- SHA-1 fingerprint — see below

This registration is what allows Google Sign-In to trust builds from this machine/keystore.

### SHA-1 Fingerprints

| Keystore | SHA-1 | Purpose |
|----------|-------|---------|
| `~/.android/debug.keystore` (alias `androiddebugkey`) | `6F:9D:E2:20:2F:35:17:10:8C:41:28:B2:61:F5:4F:DE:7F:B1:0E:38` | Local dev / `npx cap run android` debug builds |
| `diplicity-android-upload.keystore` (alias `upload`) | `6A:39:8D:D3:B4:43:12:22:0C:4C:FA:08:93:B7:AD:19:58:D2:E0:0E` | Release builds / Play Console upload key |
| Play App Signing certificate | `17:CF:46:81:F1:B2:95:8E:16:25:4A:9E:3E:85:F9:84:17:42:AD:58` | Play Store / CI release builds |

To re-extract the debug SHA-1:
```bash
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

## Credentials

### Upload Keystore

The upload keystore signs AAB/APK builds before submission to Play Console. Play App Signing re-signs the app with Google's key before distribution, so the upload key is never seen by end users — but it must match across all future uploads.

| Item | Value |
|------|-------|
| File | `diplicity-android-upload.keystore` (repo root, gitignored) |
| Key alias | `upload` |
| SHA-1 | `6A:39:8D:D3:B4:43:12:22:0C:4C:FA:08:93:B7:AD:19:58:D2:E0:0E` |
| SHA-256 | `72:86:DC:A5:6F:C9:E1:5E:CF:E1:38:8A:AD:D9:C5:FC:B6:0D:2F:5B:CC:05:4D:B1:E5:E9:27:BD:05:EA:32:F8` |
| Validity | 10 000 days (expires 2053-10-11) |
| Password | Store in your password manager under "diplicity-android-upload.keystore" |

**Required env vars for release builds:**

```bash
ANDROID_KEYSTORE_PATH=/path/to/diplicity-android-upload.keystore  # defaults to repo root
ANDROID_KEYSTORE_PASSWORD=<password>
ANDROID_KEY_ALIAS=upload
ANDROID_KEY_PASSWORD=<password>
```

**Local release build:**
```bash
cd packages/web/android
ANDROID_HOME=$HOME/Android/Sdk \
  ANDROID_KEYSTORE_PATH="$(git rev-parse --show-toplevel)/diplicity-android-upload.keystore" \
  ANDROID_KEYSTORE_PASSWORD="..." \
  ANDROID_KEY_ALIAS="upload" \
  ANDROID_KEY_PASSWORD="..." \
  ./gradlew bundleRelease
```

**Restoring the keystore from scratch:** If the file is lost, a new upload key must be generated and submitted to Play Console via "Upload new key" in the Play App Signing settings. The app can still be distributed — Google holds the actual signing key.

### Gitignored credential files (repo root)

| File | Purpose |
|------|---------|
| `diplicity-android-upload.keystore` | Android upload keystore |
| `google-services.json` | _(at `packages/web/android/app/`)_ Firebase Android config |
| `AuthKey_C6JM6K4J2X.p8` | APNs key (iOS push notifications) |
| `AuthKey_WVUV6626PT.p8` | App Store Connect API key (iOS Fastlane CI) |

---

# iOS Development (Capacitor)

## Real Device Testing (Preferred)

**Always use the physical iPhone for iOS testing — do not use simulators.** Simulators consume too much RAM and the real device is the preferred testing target.

The XcodeBuildMCP session defaults are pre-configured to target the real device (profile: `real-device`, persisted in `.xcodebuildmcp/config.yaml`).

- **Bundle ID**: `com.diplicity.app`
- **Xcode Project**: `packages/web/ios/App/App.xcodeproj` (there is no `.xcworkspace`)
- **Scheme**: `App`

### MCP Tools

- **XcodeBuildMCP**: Only simulator workflow tools are enabled by default. Device workflows must be explicitly enabled in XcodeBuildMCP configuration. Until enabled, use `xcodebuild` CLI directly for device builds.
- **mobile-mcp**: Use for UI interaction — screenshots, taps, swipes, text input on the real device

### Build & Deploy Workflow

**IMPORTANT**: `npx cap sync` must be run from `packages/web/` — it uses the `capacitor.config.ts` in that directory and will fail if run from the repo root.

```bash
# All commands run from packages/web/
cd packages/web
npm run build                # Build the web app
npx cap sync ios             # Sync web assets to iOS project

# Build for device via CLI (when XcodeBuildMCP device tools are unavailable)
xcodebuild -project ios/App/App.xcodeproj -scheme App \
  -destination 'id=<DEVICE_UDID>' \
  -allowProvisioningUpdates \
  DEVELOPMENT_TEAM=G76UP8FNMS CODE_SIGN_STYLE=Automatic \
  build
```

## Credentials

The following files are in the repo root but gitignored:

- `AuthKey_C6JM6K4J2X.p8` — APNs authentication key (Key ID: `C6JM6K4J2X`). Used by Firebase to send push notifications to iOS.
- `AuthKey_WVUV6626PT.p8` — App Store Connect API key (Key ID: `WVUV6626PT`, Issuer ID: `988659a4-ba96-4fb1-8ad7-bccc72aa219f`). Used by Fastlane for CI/CD TestFlight uploads. The key ID and issuer ID are also stored in `.env` as `ASC_KEY_ID` and `ASC_ISSUER_ID`.

Code signing uses **Xcode automatic signing** — Xcode manages provisioning profiles automatically. No manual `.mobileprovision` file is needed in the repo (`.gitignore` still excludes `*.mobileprovision`).

Signing certificates installed in the local macOS Keychain:
- Apple Development: John McDowell (`P96LAJ7FF8`) — for device builds
- Apple Distribution: John McDowell (`G76UP8FNMS`) — for App Store distribution (created Feb 2026)

The Team ID is `G76UP8FNMS` (stored in `.env` as `CAPACITOR_IOS_TEAM_ID`). The canonical source is the certificate's OU field, confirmed via `security find-certificate -c "Apple Development: John McDowell" -p | openssl x509 -noout -subject`.

## Fastlane CI/CD

### Local Usage

Run from `packages/web/`:
```bash
# iOS — full release to TestFlight
npm run build && npx cap sync ios && bundle exec fastlane ios release

# iOS — PR validation build
PR_NUMBER=42 PR_TITLE="My feature" bundle exec fastlane ios pr_build

# Android — full release to Play Console internal track
VITE_DIPLICITY_API_BASE_URL=https://diplicity-react-production.up.railway.app \
  npm run build && npx cap sync android && bundle exec fastlane android release

# Android — PR build
PR_NUMBER=42 PR_TITLE="My feature" bundle exec fastlane android pr_build
```

iOS requires `ASC_KEY_ID` and `ASC_ISSUER_ID` in `.env`, and the `.p8` key file in the repo root.

Android requires these env vars (add to shell or `.env`):
```bash
ANDROID_KEYSTORE_PATH=/path/to/diplicity-android-upload.keystore
ANDROID_KEYSTORE_PASSWORD=<password>
ANDROID_KEY_ALIAS=upload
ANDROID_KEY_PASSWORD=<password>
PLAY_SERVICE_ACCOUNT_JSON=/path/to/play-service-account.json  # optional; upload skipped if unset
```

### Signing Strategy

- **Local dev**: Xcode automatic signing (`CODE_SIGN_STYLE=Automatic`)
- **CI / Fastlane**: Manual signing via `match` + `update_code_signing_settings` (targets the App target only)
- **Certificates**: Stored in a private Git repo (`ios-certificates`), managed by `match`

Fastlane uses `update_code_signing_settings` to switch the App target to Manual signing before building. This is target-scoped (unlike `xcargs` which applies globally to all targets including SPM dependencies). On local runs, signing is automatically restored to Automatic after the build via an `ensure` block.

### Version Management

- `MARKETING_VERSION` is read from `packages/web/package.json` `version` field
- `CURRENT_PROJECT_VERSION` (build number) is a Unix timestamp, auto-generated per build
- Both are passed via `xcargs` — no `agvtool` or project file modification needed

### GitHub Actions Workflows

- **`ios-release.yml`**: Triggers on push to `main` when `packages/web/**` changes. Builds web, syncs Capacitor, runs `fastlane ios release` to upload to TestFlight.
- **`ios-pr-build.yml`**: Manual `workflow_dispatch` with a `pr_number` input. Checks out the PR branch, builds, uploads to TestFlight with a changelog, and comments on the PR.

### Required GitHub Secrets

#### iOS

| Secret | Description |
|--------|-------------|
| `ASC_KEY_ID` | App Store Connect API key ID (`WVUV6626PT`) |
| `ASC_ISSUER_ID` | App Store Connect issuer ID |
| `ASC_KEY_CONTENT` | Base64-encoded `.p8` key file content |
| `MATCH_GIT_URL` | URL to the `ios-certificates` Git repo |
| `MATCH_PASSWORD` | Encryption password for match certificates |
| `MATCH_GIT_BASIC_AUTHORIZATION` | Base64-encoded `user:token` for HTTPS Git auth |
| `VITE_GOOGLE_IOS_CLIENT_ID` | Google OAuth iOS client ID |

#### Android

| Secret | Description |
|--------|-------------|
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded `diplicity-android-upload.keystore` |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore and key password |
| `ANDROID_KEY_ALIAS` | Key alias (`upload`) |
| `ANDROID_KEY_PASSWORD` | Key password (same as keystore password) |
| `PLAY_SERVICE_ACCOUNT_JSON` | Play Console service account JSON (raw JSON string) |
