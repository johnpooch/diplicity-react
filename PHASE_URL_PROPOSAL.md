# Proposal: Path-Based Phase Selection

## Problem Statement

The current implementation uses URL query parameters (`?selectedPhase=123`) to track the selected phase in game detail views. This approach has caused an infinite request loop in Storybook where `/game/game-1/` and `/game/game-1/phases/` are fetched repeatedly.

### Root Cause of the Infinite Loop

The hooks `useSelectedPhase` and `usePhaseNavigation` both:
1. Subscribe to `useSearchParams()` to read the query string
2. Derive the selected phase on every render
3. Call `setSearchParams()` to update the URL

This creates a feedback loop:
- Component renders → hook reads URL → hook updates URL → `useSearchParams` subscribers re-render → repeat

Attempts to fix this with memoization (`useMemo`, `useCallback`) and guards were unsuccessful, likely due to the fundamental complexity of synchronizing React state with query strings in a Suspense-based environment.

## Proposed Solution: Path-Based Phase Selection

Instead of using query parameters, embed the phase ID directly in the URL path.

### Current URL Structure
```
/game/:gameId/orders?selectedPhase=123
/game/:gameId/chat?selectedPhase=123
/game/:gameId/game-info?selectedPhase=123
```

### Proposed URL Structure
```
/game/:gameId/phase/:phaseId/orders
/game/:gameId/phase/:phaseId/chat
/game/:gameId/phase/:phaseId/game-info
/game/:gameId/phase/:phaseId/player-info
/game/:gameId/phase/:phaseId/chat/channel/create
/game/:gameId/phase/:phaseId/chat/channel/:channelId
```

## Why This Is Better

### 1. Route Params Are Stable
`useParams()` returns values that are part of the matched route. They don't cause re-renders when other parts of the URL change. Unlike `useSearchParams()`, which subscribes to all query string changes.

### 2. Navigation Replaces State Management
Instead of managing state and syncing it to the URL, we just navigate:
```typescript
// Changing phase = navigating to a new URL
navigate(`/game/${gameId}/phase/${newPhaseId}/orders`);
```

### 3. Browser History Works Naturally
- Back button → goes to previous phase
- Forward button → goes to next phase
- Deep linking → works automatically

### 4. Conceptually Cleaner
Each phase is a distinct "view" of the game. The URL reflects this reality.

### 5. No Synchronization Complexity
We're not trying to keep two things (React state and URL) in sync. The URL IS the state.

## Implementation Details

### Route Changes (`Router.tsx`)

**Before:**
```typescript
{
  path: "game/:gameId",
  element: <GameLayout />,
  children: [
    {
      element: <GameDetailLayoutWrapper />,
      children: [
        { index: true, element: <GameIndexRoute /> },
        { path: "game-info", element: <GameDetail.GameInfoScreen /> },
        { path: "player-info", element: <GameDetail.PlayerInfoScreen /> },
        { path: "orders", element: <GameDetail.OrdersScreen /> },
        { path: "chat", element: <GameDetail.ChannelListScreen /> },
        { path: "chat/channel/create", element: <GameDetail.ChannelCreateScreen /> },
        { path: "chat/channel/:channelId", element: <GameDetail.ChannelScreen /> },
      ],
    },
  ],
}
```

**After:**
```typescript
{
  path: "game/:gameId",
  element: <GameLayout />,
  children: [
    // Redirect /game/:gameId to /game/:gameId/phase/:latestPhaseId/orders
    { index: true, element: <GamePhaseRedirect /> },
    {
      path: "phase/:phaseId",
      element: <GameDetailLayoutWrapper />,
      children: [
        { index: true, element: <GameIndexRoute /> },
        { path: "game-info", element: <GameDetail.GameInfoScreen /> },
        { path: "player-info", element: <GameDetail.PlayerInfoScreen /> },
        { path: "orders", element: <GameDetail.OrdersScreen /> },
        { path: "chat", element: <GameDetail.ChannelListScreen /> },
        { path: "chat/channel/create", element: <GameDetail.ChannelCreateScreen /> },
        { path: "chat/channel/:channelId", element: <GameDetail.ChannelScreen /> },
      ],
    },
  ],
}
```

### New Component: `GamePhaseRedirect`

When a user navigates to `/game/123` without a phase, redirect them to the latest phase:

```typescript
function GamePhaseRedirect() {
  const { gameId } = useParams<{ gameId: string }>();
  const { data: phases } = useGamePhasesListSuspense(gameId!);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Sort by ordinal descending to get most recent phase first
    const sortedPhases = [...phases].sort((a, b) => b.ordinal - a.ordinal);
    const latestPhase = sortedPhases[0];

    // Determine the target path (default to orders, or preserve current sub-path)
    const targetPath = `/game/${gameId}/phase/${latestPhase.id}/orders`;

    navigate(targetPath, { replace: true });
  }, [gameId, phases, navigate]);

  return null; // Or a loading spinner
}
```

### Simplified Hook: `useSelectedPhase`

```typescript
import { useParams } from "react-router";

export function useSelectedPhase(): number {
  const { phaseId } = useParams<{ phaseId: string }>();

  if (!phaseId) {
    throw new Error("useSelectedPhase must be used within a route with :phaseId param");
  }

  return Number(phaseId);
}
```

This is dramatically simpler - just read from route params. No subscriptions, no derivation, no URL writing.

### Simplified Hook: `usePhaseNavigation`

```typescript
import { useParams, useNavigate, useLocation } from "react-router";
import { useGamePhasesListSuspense, PhaseList } from "@/api/generated/endpoints";

interface PhaseNavigation {
  selectedPhase: number;
  phases: readonly PhaseList[];
  setPhase: (phaseId: number) => void;
  setPreviousPhase: () => void;
  setNextPhase: () => void;
  hasPreviousPhase: boolean;
  hasNextPhase: boolean;
}

export function usePhaseNavigation(): PhaseNavigation {
  const { gameId, phaseId } = useParams<{ gameId: string; phaseId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: phases } = useGamePhasesListSuspense(gameId!);

  const selectedPhase = Number(phaseId);

  // Sort ascending by ordinal for navigation (oldest first)
  const sortedPhases = [...phases].sort((a, b) => a.ordinal - b.ordinal);
  const currentIndex = sortedPhases.findIndex(p => p.id === selectedPhase);

  // Get current sub-path (orders, chat, etc.)
  const getCurrentSubPath = () => {
    const match = location.pathname.match(/\/phase\/\d+\/(.*)$/);
    return match ? match[1] : 'orders';
  };

  const setPhase = (newPhaseId: number) => {
    const subPath = getCurrentSubPath();
    navigate(`/game/${gameId}/phase/${newPhaseId}/${subPath}`);
  };

  const setPreviousPhase = () => {
    if (currentIndex > 0) {
      setPhase(sortedPhases[currentIndex - 1].id);
    }
  };

  const setNextPhase = () => {
    if (currentIndex < sortedPhases.length - 1) {
      setPhase(sortedPhases[currentIndex + 1].id);
    }
  };

  return {
    selectedPhase,
    phases,
    setPhase,
    setPreviousPhase,
    setNextPhase,
    hasPreviousPhase: currentIndex > 0,
    hasNextPhase: currentIndex < sortedPhases.length - 1,
  };
}
```

Note: No `useMemo`, `useCallback`, or guards needed because:
- `useParams()` is stable (doesn't cause unnecessary re-renders)
- `navigate()` is an action, not state synchronization
- No feedback loops possible

## Files to Modify

1. **`packages/web/src/Router.tsx`**
   - Add `phase/:phaseId` path segment
   - Add `GamePhaseRedirect` component for index route

2. **`packages/web/src/hooks/useSelectedPhase.ts`**
   - Simplify to just read from `useParams()`

3. **`packages/web/src/hooks/usePhaseNavigation.ts`**
   - Change from `setSearchParams` to `navigate()`
   - Preserve current sub-path when changing phase

4. **Navigation links throughout the app**
   - Any `<Link>` or `navigate()` calls that go to game detail screens need to include the phase
   - Example: Links from game cards, home screens, etc.

5. **Storybook decorators**
   - Update router mocks to include `phase/:phaseId` in the path
   - Update `initialEntries` to include phase in the URL

## Migration Considerations

### Backwards Compatibility

Old URLs like `/game/123/orders?selectedPhase=456` will no longer work. Options:

1. **Hard break**: Old URLs return 404 (simplest)
2. **Redirect**: Add a loader that checks for `selectedPhase` query param and redirects
3. **Deprecation period**: Support both for a while

Recommendation: Hard break is fine since this is an internal app without public URLs.

### Links from External Sources

If there are links from emails, notifications, or external systems, they'll need to be updated to the new format.

## Storybook Updates

Stories need updated route configuration:

**Before:**
```typescript
parameters: {
  router: {
    initialEntries: ["/game/game-1/orders?selectedPhase=1"],
    path: "/game/:gameId/*",
  },
}
```

**After:**
```typescript
parameters: {
  router: {
    initialEntries: ["/game/game-1/phase/1/orders"],
    path: "/game/:gameId/phase/:phaseId/*",
  },
}
```

## Testing the Change

1. **Manual testing**:
   - Navigate to a game from home screen
   - Verify redirect to latest phase works
   - Click phase forward/backward buttons
   - Verify browser back/forward works
   - Verify URL updates correctly

2. **Storybook**:
   - Verify no infinite request loops
   - Verify phase navigation works in stories

3. **Unit tests**:
   - Test `GamePhaseRedirect` redirects to correct phase
   - Test `usePhaseNavigation` returns correct values

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing bookmarks | Acceptable for internal app |
| Missing some navigation links | Search codebase for all `navigate()` and `<Link>` usage |
| Storybook configuration issues | Update decorator with new route pattern |
| Complex sub-routes (chat channels) | Test thoroughly, preserve sub-paths in navigation |

## Summary

This proposal simplifies phase selection by making the phase part of the URL path instead of a query parameter. This eliminates the state synchronization complexity that caused the infinite loop and provides a cleaner mental model where navigation = changing phase.

**Key benefits:**
- Dramatically simpler hooks (no memoization or guards needed)
- No infinite loops possible
- Browser history works naturally
- URL is the single source of truth

**Trade-offs:**
- All game detail URLs change
- Need to update all navigation code
- Slightly longer URLs
