# 07: Consistent Query Error Handling

## Context

The codebase currently uses Suspense for loading states with `useXxxSuspense` hooks. However, there's no consistent pattern for handling query errors. When a query fails, the behavior is undefined - components may crash, show nothing, or behave unexpectedly.

**Current state:**
- Mutations use try/catch with `toast.error()` - this is good
- Queries have no consistent error handling pattern
- No error boundaries in the component tree

## Proposed Solution

Use React Error Boundaries as the complement to Suspense, with React Query configured to throw errors.

### Why Error Boundaries?

1. **Pairs naturally with Suspense** - Suspense handles loading, Error Boundaries handle errors
2. **Declarative** - Error UI is defined in the component tree, not imperative try/catch
3. **Granular control** - Can wrap at route level, screen level, or component level
4. **Automatic recovery** - Error boundaries can provide retry functionality

### Pattern Overview

```
<ErrorBoundary fallback={<ErrorFallback />}>
  <Suspense fallback={<Loading />}>
    <Component />  {/* Uses useXxxSuspense hooks */}
  </Suspense>
</ErrorBoundary>
```

## Implementation

### Step 1: Create Error Boundary Component

```typescript
// src/components/ErrorBoundary.tsx
import React, { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice.new";
import { IconName } from "@/components/Icon";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 space-y-4">
          <Notice
            icon={IconName.Error}
            title="Something went wrong"
            message="We couldn't load this content. Please try again."
          />
          <Button onClick={this.handleReset}>Try Again</Button>
        </div>
      );
    }

    return this.props.children;
  }
}

export { ErrorBoundary };
```

### Step 2: Create Query Error Boundary (with React Query integration)

```typescript
// src/components/QueryErrorBoundary.tsx
import React, { ReactNode } from "react";
import { useQueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "./ErrorBoundary";

interface QueryErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

const QueryErrorBoundary: React.FC<QueryErrorBoundaryProps> = ({
  children,
  fallback,
}) => {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <ErrorBoundary onReset={reset} fallback={fallback}>
      {children}
    </ErrorBoundary>
  );
};

export { QueryErrorBoundary };
```

### Step 3: Update Screen Suspense Wrappers

**Before:**
```typescript
const MyGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" />
      <Suspense fallback={<div></div>}>
        <MyGames />
      </Suspense>
    </ScreenContainer>
  );
};
```

**After:**
```typescript
const MyGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="My Games" />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <MyGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};
```

### Step 4: Route-Level Error Boundaries (Alternative)

For simpler setup, add error boundaries at the route level in Router.tsx:

```typescript
// src/Router.tsx
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";

const routes = [
  {
    path: "/",
    element: (
      <QueryErrorBoundary>
        <HomeLayout>
          <Outlet />
        </HomeLayout>
      </QueryErrorBoundary>
    ),
    children: [
      { path: "my-games", element: <MyGames /> },
      { path: "find-games", element: <FindGames /> },
      // ...
    ],
  },
];
```

## Error Handling Guidelines

### Query Errors (reads)

| Scenario | Handling |
|----------|----------|
| Screen-level data fetch fails | Error boundary shows fallback UI with retry |
| Optional data fetch fails | Handle inline if UI can degrade gracefully |
| Background refetch fails | React Query handles silently, shows stale data |

### Mutation Errors (writes)

| Scenario | Handling |
|----------|----------|
| User-triggered action fails | `toast.error("Descriptive message")` |
| Form submission fails | Show inline error + toast |
| Background sync fails | Toast only if user needs to know |

### Example: Mutation Error Handling

```typescript
const handleCreateGame = async (data: FormValues) => {
  try {
    await createGameMutation.mutateAsync({ data });
    toast.success("Game created successfully");
    navigate("/");
  } catch {
    toast.error("Failed to create game");
  }
};
```

## Migration Path

### Phase 1: Create Components
- [ ] Create `src/components/ErrorBoundary.tsx`
- [ ] Create `src/components/QueryErrorBoundary.tsx`
- [ ] Add `IconName.Error` if it doesn't exist

### Phase 2: Add to Router
- [ ] Wrap main route layouts with `QueryErrorBoundary`
- [ ] Test that errors are caught and displayed

### Phase 3: Update Screen Wrappers (Optional)
- [ ] Add `QueryErrorBoundary` to individual screen Suspense wrappers
- [ ] Only needed if you want screen-specific error UI

## Files Affected

### Files to Create
- `src/components/ErrorBoundary.tsx`
- `src/components/QueryErrorBoundary.tsx`

### Files to Modify
- `src/Router.tsx` - Add error boundaries
- `src/components/Icon.tsx` - Add Error icon if needed

## Success Criteria

- [ ] Query errors display user-friendly error UI
- [ ] Users can retry failed requests
- [ ] Mutations continue to show toast errors
- [ ] No unhandled promise rejections in console
- [ ] TypeScript compiles without errors
