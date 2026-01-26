# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

- **Comments**: Do not add docstrings or comments.

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

Test fixtures should exist in the app's `conftest.py` file rather than in the test file itself.

Follow this testing pattern:
- Create pytest fixtures in `conftest.py` that return callable factory functions
- Focus on API endpoint testing rather than unit testing individual methods
- Use fixtures like `@pytest.fixture def factory_function(db, other_fixtures): def _create(...): return Model.objects.create(...); return _create`
- Test comprehensive endpoint behavior including permissions, validation, and data transformations
- Add performance tests to ensure N+1 query issues are avoided
- For complex logic in utils files, create separate test classes

---

# API Development

The API schema is auto-generated using DRF Spectacular:
```bash
docker compose up codegen
```

This generates OpenAPI schema and TypeScript client code for the frontend.
