# Investigation: Infinite Request Loop in Storybook

## Problem

When loading stories in Storybook, there's an infinite request loop where `/game/game-1/` and `/game/game-1/phases/` are being fetched repeatedly:

```
[MSW] 14:00:52 GET /game/game-1/ (200 OK)
[MSW] 14:00:52 GET /game/game-1/phases/ (200 OK)
[MSW] 14:00:52 GET /game/game-1/ (200 OK)
[MSW] 14:00:52 GET /game/game-1/phases/ (200 OK)
... (continues infinitely)
```

The requests are returning 200 OK (MSW mocks are working), but something is causing React Query to refetch continuously.

## Recent Changes (Root Cause Context)

We recently removed `SelectedPhaseContext` and replaced it with URL-derived state via custom hooks:

### New Hooks Created

**`packages/web/src/hooks/useSelectedPhase.ts`**:
```typescript
import { useSearchParams } from "react-router";
import { useGamePhasesListSuspense } from "@/api/generated/endpoints";

export function useSelectedPhase(gameId: string): number {
  const [searchParams] = useSearchParams();
  const { data: phases } = useGamePhasesListSuspense(gameId);

  const urlPhaseId = searchParams.get("selectedPhase");

  if (urlPhaseId) {
    const phaseId = Number(urlPhaseId);
    if (phases.some(p => p.id === phaseId)) {
      return phaseId;
    }
  }

  const sortedPhases = [...phases].sort((a, b) => b.ordinal - a.ordinal);
  return sortedPhases[0].id;
}
```

**`packages/web/src/hooks/usePhaseNavigation.ts`**:
```typescript
import { useSearchParams } from "react-router";
import { useGamePhasesListSuspense, PhaseList } from "@/api/generated/endpoints";

export function usePhaseNavigation(gameId: string): PhaseNavigation {
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: phases } = useGamePhasesListSuspense(gameId);

  // ... derives selectedPhase from URL or defaults to most recent
  // ... setPhase updates URL via setSearchParams({ replace: true })
}
```

### Components Using These Hooks

- `GameMap.tsx` - uses `useSelectedPhase(gameId)`
- `PhaseSelect.tsx` - uses `usePhaseNavigation(gameId)`
- `OrdersScreen.new.tsx`, `OrdersScreen.tsx`, `PlayerInfoScreen.tsx`, `InactivePhaseOrders.tsx` - use `useSelectedPhase(gameId)`

### Key Architectural Change

`GameDetailLayout.new.tsx` renders `<GameMap />` on desktop (line 81), which means any story using `GameDetailLayout` or `withGameDetailLayout` decorator will trigger the phases fetch.

## Suspected Causes

1. **`setSearchParams` triggering re-renders**: The `usePhaseNavigation` hook calls `setSearchParams` to update the URL. If this causes a re-render that invalidates or refetches queries, it could loop.

2. **URL state not stabilizing**: If the selected phase derived from URL doesn't match what's being set, it could cause a loop of "read URL -> set URL -> read URL -> ..."

3. **React Query cache key instability**: If something in the query key is changing on each render, React Query will refetch.

4. **Suspense boundary issues**: The hooks use `useGamePhasesListSuspense` which suspends. If the Suspense boundary is re-mounting, it could cause refetches.

5. **useSearchParams causing renders**: Reading from `useSearchParams` subscribes to URL changes. If something is constantly updating the URL, this could trigger loops.

## Files to Investigate

### Primary Files
- `packages/web/src/hooks/useSelectedPhase.ts`
- `packages/web/src/hooks/usePhaseNavigation.ts`
- `packages/web/src/components/GameMap.tsx`
- `packages/web/src/components/PhaseSelect.tsx`
- `packages/web/src/components/GameDetailLayout.new.tsx`

### Story/Decorator Files
- `packages/web/src/stories/decorators.tsx`
- `packages/web/src/components/GameDetailLayout.new.stories.tsx`

### Context for Comparison
- The deleted `packages/web/src/context/SelectedPhaseContext.tsx` used to sync URL state via `useEffect` with `navigate({ replace: true })`. That approach may have had safeguards we're now missing.

## Investigation Steps

1. **Add console logging** to `useSelectedPhase` and `usePhaseNavigation` to see if they're being called repeatedly and why

2. **Check if URL is being modified**: Add logging before/after `setSearchParams` calls

3. **Verify query cache behavior**: Check if React Query thinks it needs to refetch (stale data? cache miss?)

4. **Test without URL sync**: Temporarily remove the `setSearchParams` logic and see if the loop stops

5. **Compare with old context**: Review the deleted `SelectedPhaseContext.tsx` to see how it prevented loops

## Possible Fixes

1. **Memoize or stabilize derived values**: Ensure `selectedPhase` value is stable and doesn't change unnecessarily

2. **Add guards before URL updates**: Only call `setSearchParams` if the value actually changed

3. **Use `useMemo` for computed values**: Prevent recalculation on every render

4. **Check React Router integration**: Ensure Storybook's router mock is compatible with `useSearchParams`

5. **Consider using `useEffect` for URL sync**: Like the old context did, with proper dependency tracking

## Additional Context

- The app uses React Query (TanStack Query) for data fetching
- Storybook uses `storybook-addon-remix-react-router` for router mocking
- MSW is used for API mocking in stories
- The hooks use Suspense variants of queries (`useGamePhasesListSuspense`)

## Goal

Find the root cause of the infinite loop and fix it so that:
1. The selected phase is correctly derived from URL or defaults to most recent
2. Queries only run once (plus normal cache invalidation)
3. URL updates don't cause cascading re-renders
