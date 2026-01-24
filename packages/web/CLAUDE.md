# CLAUDE.md - Frontend (packages/web)

This file provides guidance for working with the React frontend.

## Maintaining This Document

**If you discover new patterns, make decisions about architecture, or establish conventions during development, suggest updates to this CLAUDE.md file.** This document should evolve with the codebase. When you notice:

- A pattern being used consistently that isn't documented here
- A decision made that future development should follow
- A convention that would benefit from being explicit

Propose adding it to this file.

## Data & State Management

### React Query for All Server State

- Use `useXxxSuspense` hooks for data fetching - never the non-suspense variants
- Use `useXxxMutation` hooks with `mutateAsync` for writes
- No Redux - do not use Redux for any purpose

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
