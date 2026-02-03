# Implementation Phase 2.2: Frontend Pause Controls

## Overview

**Goal:** Allow Game Masters to pause and resume games from the frontend, with clear visual indicators when a game is paused.

**Current State:** Phase 2.1 is complete. The backend has:
- `paused_at` DateTimeField on Game model (nullable)
- `is_paused` property on Game model
- `PUT /game/{gameId}/pause/` endpoint (GM-only)
- `PATCH /game/{gameId}/unpause/` endpoint (GM-only)
- `IsGameMaster` permission class
- Generated API hooks (`useGamePauseUpdate`, `useGameUnpausePartialUpdate`)
- `isPaused` and `pausedAt` fields on `GameList` and `GameRetrieve` types

**What Phase 2.2 Adds:**
- Pause/Resume menu items in GameDropdownMenu (GM-only)
- Paused state banner in game detail views
- Paused timestamp display in game info

---

## Implementation Tasks

### Task 1: Add formatRelativeTime Utility

Add a relative time formatting function to the existing `util.ts` file. This will display paused timestamps as "5 minutes ago" style text in the banner.

**Decision:** Implement a native solution rather than installing `date-fns`, keeping dependencies minimal. The relative time formatting is only used in one place (the pause banner) and doesn't require timezone handling or complex localization.

**Changes to `packages/web/src/util.ts`:**

```typescript
export const formatRelativeTime = (isoString: string): string => {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  } else {
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
  }
};
```

**Files to modify:**
- `packages/web/src/util.ts` - Add function and export

---

### Task 2: Add Pause/Resume Menu Items to GameDropdownMenu

Add GM-only menu items to pause and resume a game from the dropdown menu.

**Changes:**

1. Update imports:
   ```typescript
   import { Pause, PlayCircle } from "lucide-react"; // PlayCircle to differentiate from Play used elsewhere
   import {
     useGamePauseUpdate,
     useGameUnpausePartialUpdate,
     getGameRetrieveQueryKey,
     getGamesListQueryKey, // For list invalidation
   } from "@/api/generated/endpoints";
   ```

2. Update `GameDropdownMenuProps` interface to include `isPaused`:
   ```typescript
   interface GameDropdownMenuProps {
     game: Pick<GameList, "id" | "sandbox" | "canLeave" | "isPaused"> &
       Partial<Pick<GameRetrieve, "status" | "members">>;
     // ... existing props
   }
   ```

3. Add mutation hooks in component body:
   ```typescript
   const pauseGameMutation = useGamePauseUpdate();
   const resumeGameMutation = useGameUnpausePartialUpdate();
   ```

4. Determine if current user is Game Master:
   ```typescript
   const isGameMaster = currentMember?.isGameMaster ?? false;
   ```

5. Add condition for showing pause controls:
   ```typescript
   const canPauseOrResume = isActiveGame && isGameMaster && !game.sandbox;
   ```

6. Add pause handler with loading state protection:
   ```typescript
   const handlePauseGame = async () => {
     try {
       await pauseGameMutation.mutateAsync({ gameId: game.id });
       toast.success("Game paused");
       queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(game.id) });
       queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
     } catch {
       toast.error("Failed to pause game");
     }
   };
   ```

7. Add resume handler with loading state protection:
   ```typescript
   const handleResumeGame = async () => {
     try {
       await resumeGameMutation.mutateAsync({ gameId: game.id });
       toast.success("Game resumed");
       queryClient.invalidateQueries({ queryKey: getGameRetrieveQueryKey(game.id) });
       queryClient.invalidateQueries({ queryKey: getGamesListQueryKey() });
     } catch {
       toast.error("Failed to resume game");
     }
   };
   ```

8. Add menu items (between "Clone to sandbox" and "Propose draw") with disabled state during mutations:
   ```typescript
   {canPauseOrResume && (
     <>
       <DropdownMenuSeparator />
       {game.isPaused ? (
         <DropdownMenuItem
           onClick={handleResumeGame}
           disabled={resumeGameMutation.isPending}
         >
           <PlayCircle />
           Resume game
         </DropdownMenuItem>
       ) : (
         <DropdownMenuItem
           onClick={handlePauseGame}
           disabled={pauseGameMutation.isPending}
         >
           <Pause />
           Pause game
         </DropdownMenuItem>
       )}
     </>
   )}
   ```

**Files to modify:**
- `packages/web/src/components/GameDropdownMenu.tsx`

---

### Task 3: Verify GameDropdownMenu Usage Sites

Verify that all usage sites pass the `isPaused` field. Since we're adding it to the `Pick<GameList, ...>`, we need to confirm the data is available.

**Usage sites and their game object sources:**

| File | Game Source | Type | Action |
|------|-------------|------|--------|
| `screens/GameDetail/OrdersScreen.tsx` | `useGameRetrieveSuspense` | `GameRetrieve` | No change needed - full object includes `isPaused` |
| `screens/GameDetail/MapScreen.tsx` | `useGameRetrieveSuspense` | `GameRetrieve` | No change needed - full object includes `isPaused` |
| `screens/Home/GameInfo.tsx` | `useGameRetrieveSuspense` | `GameRetrieve` | No change needed - full object includes `isPaused` |
| `screens/Home/PlayerInfo.tsx` | `useGameRetrieveSuspense` | `GameRetrieve` | No change needed - full object includes `isPaused` |
| `components/GameCard.tsx` | Props `game: GameList` | `GameList` | No change needed - `GameList` includes `isPaused` |

**Conclusion:** All usage sites pass the full `GameList` or `GameRetrieve` object, which already contains `isPaused`. No changes needed to usage sites.

**Files to verify (no changes expected):**
- `packages/web/src/screens/GameDetail/OrdersScreen.tsx`
- `packages/web/src/screens/GameDetail/MapScreen.tsx`
- `packages/web/src/screens/Home/GameInfo.tsx`
- `packages/web/src/screens/Home/PlayerInfo.tsx`
- `packages/web/src/components/GameCard.tsx`

---

### Task 4: Add Paused Banner to GameStatusAlerts

Display a prominent banner when a game is paused.

**Changes:**

1. Import `Pause` icon from lucide-react

2. Import `formatRelativeTime` from util:
   ```typescript
   import { formatRelativeTime } from "@/util";
   ```

3. Update `GameStatusAlertsProps` interface:
   ```typescript
   interface GameStatusAlertsProps {
     game: {
       status: string;
       isPaused: boolean;
       pausedAt: string | null;
       victory?: {
         type: string;
         members: readonly { name: string }[];
       } | null;
     };
     variant?: {
       nations: { length: number } | readonly unknown[];
     };
   }
   ```

4. Add paused state alert (after pending check, before victory check):
   ```typescript
   {game.isPaused && (
     <Alert>
       <Pause className="size-4" />
       <AlertDescription>
         This game is paused.
         {game.pausedAt && (
           <> Paused {formatRelativeTime(game.pausedAt)}.</>
         )}
       </AlertDescription>
     </Alert>
   )}
   ```

**Files to modify:**
- `packages/web/src/components/GameStatusAlerts.tsx`

---

### Task 5: Add Paused Status to GameInfoContent

Display "Paused at [datetime]" in the game info metadata rows using the existing `formatDateTime` function.

**Changes:**

1. Import `Pause` icon from lucide-react

2. Add MetadataRow for paused status (after "Visibility" row, before the conditional "Winner" row):
   ```typescript
   {game.isPaused && (
     <MetadataRow
       icon={<Pause className="size-4" />}
       label="Status"
       value={
         game.pausedAt
           ? `Paused ${formatDateTime(game.pausedAt)}`
           : "Paused"
       }
     />
   )}
   ```

**Note:** The existing `formatDateTime` function from `util.ts` outputs "Today HH:MM", "Tomorrow HH:MM", or "DD/MM/YY HH:MM", which is appropriate for this metadata row since it's showing absolute time alongside other game metadata.

**Files to modify:**
- `packages/web/src/components/GameInfoContent.tsx`

---

### Task 6: Write Tests for GameDropdownMenu Pause Controls

Add tests for the pause/resume functionality.

**Test cases:**
- Pause menu item is hidden for non-Game Masters
- Pause menu item is hidden for sandbox games
- Pause menu item is hidden for non-active games (pending, completed, abandoned)
- Pause menu item shows "Pause game" when game is not paused (GM, active, non-sandbox)
- Pause menu item shows "Resume game" when game is paused (GM, active, non-sandbox)
- Clicking "Pause game" calls the pause mutation
- Clicking "Resume game" calls the unpause mutation
- Menu item is disabled while mutation is pending
- Toast appears on successful pause/resume
- Error toast appears on failed pause/resume

**Files to add to:**
- `packages/web/src/components/GameDropdownMenu.test.tsx` (create if doesn't exist)

---

### Task 7: Write Tests for GameStatusAlerts

Add tests for the paused state banner.

**Test cases:**
- Paused banner is not shown when `isPaused` is false
- Paused banner is shown when `isPaused` is true
- Paused banner displays relative time when `pausedAt` is provided
- Paused banner handles missing `pausedAt` gracefully (shows "This game is paused." without timestamp)

**Files to add to:**
- `packages/web/src/components/GameStatusAlerts.test.tsx` (create if doesn't exist)

---

### Task 8: Add Storybook Stories

Add stories to demonstrate the pause controls and banners.

**Stories to add:**

For GameDropdownMenu:
- Default (non-GM user)
- Game Master (not paused)
- Game Master (paused)

For GameStatusAlerts:
- Default (active game, not paused)
- Paused game with timestamp
- Paused game without timestamp

**Files to add to:**
- `packages/web/src/components/GameDropdownMenu.stories.tsx` (create if doesn't exist)
- `packages/web/src/components/GameStatusAlerts.stories.tsx` (create if doesn't exist)

---

### Task 9: Update RELEASE_NOTES.md

Document the new Game Master pause controls feature.

**Entry:**
```markdown
### Game Master Controls

- Game Masters can now pause and resume active games from the game menu
- A banner displays when a game is paused, visible to all players
- Game info shows when a game was paused
```

**Files to modify:**
- `RELEASE_NOTES.md`

---

## Acceptance Criteria

- [ ] Game Masters see "Pause game" menu item in active, non-sandbox games
- [ ] Game Masters see "Resume game" menu item when game is paused
- [ ] Non-Game Masters do not see pause/resume menu items
- [ ] Menu items are disabled while mutations are pending
- [ ] Clicking "Pause game" pauses the game and shows success toast
- [ ] Clicking "Resume game" resumes the game and shows success toast
- [ ] Failed pause/resume shows error toast
- [ ] Paused games show a banner in game detail views with relative time
- [ ] Game info displays paused timestamp (absolute time) when applicable
- [ ] Both game retrieve and games list queries are invalidated after pause/resume
- [ ] All tests pass
- [ ] Storybook stories demonstrate functionality

---

## File Summary

### Files to Modify
```
packages/web/src/
├── util.ts                           # Add formatRelativeTime function
├── components/
│   ├── GameDropdownMenu.tsx          # Add pause/resume menu items
│   ├── GameStatusAlerts.tsx          # Add paused banner
│   └── GameInfoContent.tsx           # Add paused status row
RELEASE_NOTES.md                      # Document feature
```

### Files to Create (Tests & Stories)
```
packages/web/src/
├── components/
│   ├── GameDropdownMenu.test.tsx     # Tests for pause controls
│   ├── GameDropdownMenu.stories.tsx  # Stories for pause states
│   ├── GameStatusAlerts.test.tsx     # Tests for paused banner
│   └── GameStatusAlerts.stories.tsx  # Stories for paused banner
```

### Files to Verify (No Changes Expected)
```
packages/web/src/
├── screens/
│   ├── GameDetail/
│   │   ├── OrdersScreen.tsx
│   │   └── MapScreen.tsx
│   └── Home/
│       ├── GameInfo.tsx
│       └── PlayerInfo.tsx
└── components/
    └── GameCard.tsx
```

---

## Implementation Order

1. **Task 1**: Add `formatRelativeTime` utility to `util.ts`
2. **Task 2**: Add pause/resume menu items to GameDropdownMenu
3. **Task 3**: Verify GameDropdownMenu usage sites (likely no changes needed)
4. **Task 4**: Add paused banner to GameStatusAlerts
5. **Task 5**: Add paused status to GameInfoContent
6. **Task 6**: Write tests for GameDropdownMenu
7. **Task 7**: Write tests for GameStatusAlerts
8. **Task 8**: Add Storybook stories
9. **Task 9**: Update RELEASE_NOTES.md

This order ensures utilities are in place before components that use them, and core functionality is implemented before tests and documentation.

---

## Design Notes

### Icon Choice
Using `PlayCircle` instead of `Play` for "Resume game" to differentiate from the `Play` icon used for "Resolve phase" in sandbox games (`OrdersScreen.tsx`). This avoids visual confusion since both features can appear in the same game context.

### Banner Placement
The paused banner appears in `GameStatusAlerts`, which is displayed at the top of both `GameInfoContent` and `PlayerInfoContent`. This ensures visibility across all game detail screens without duplicating logic.

### Mutation Invalidation
After pause/resume mutations, we invalidate both:
- `getGameRetrieveQueryKey(game.id)` - Updates the current game detail view
- `getGamesListQueryKey()` - Updates the home screen games list cache

This ensures users see the correct paused state whether they're in the game or navigate back to the home screen.

### Error Handling
Pause/resume failures show a toast error. The mutation hooks handle the HTTP error response automatically. No special error state is needed in the UI beyond the toast notification.

### Loading State
Menu items are disabled while their respective mutations are pending (`disabled={pauseGameMutation.isPending}`). This prevents accidental double-clicks and provides visual feedback during the API call.

### Date Formatting
- **Banner (GameStatusAlerts):** Uses relative time ("5 minutes ago") via new `formatRelativeTime` function for quick comprehension of how long the game has been paused.
- **Game Info (GameInfoContent):** Uses existing `formatDateTime` function for absolute time ("Today 14:30" or "03/02/26 14:30"), consistent with other metadata timestamps.

### Utility Implementation
Implementing `formatRelativeTime` natively rather than installing `date-fns` to minimize dependencies. The relative time formatting is straightforward and only used in one place (pause banner). If more complex date handling is needed in the future, `date-fns` can be added then.
