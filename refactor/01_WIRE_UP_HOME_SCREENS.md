# 01: Wire Up Home Screens

## Context

The new home screen components have been created with the `.new.tsx` suffix. They need to be wired into the router and tested against the local server before the old versions can be removed.

## Files to Update

### Step 1: Update the Home index to use new components

Update `packages/web/src/screens/Home/index.ts` to import from the `.new.tsx` files:

```typescript
import { MyGames } from "./MyGames.new";
import { FindGames } from "./FindGames.new";
import { CreateGame } from "./CreateGame.new";
import { Profile } from "./Profile.new";
import { GameInfo } from "./GameInfo.new";
import { PlayerInfo } from "./PlayerInfo.new";
import { SandboxGames } from "./SandboxGames.new";

export const Home = {
  MyGames,
  FindGames,
  CreateGame,
  Profile,
  GameInfo,
  PlayerInfo,
  SandboxGames,
};
```

### Step 2: Create a HomeLayout wrapper with Outlet

Use React Router's nested layout pattern. Update `packages/web/src/Router.tsx`:

1. Import `HomeLayout` from `@/components/HomeLayout`
2. Import `Outlet` from `react-router`
3. Create a layout wrapper component:

```typescript
const HomeLayoutWrapper: React.FC = () => {
  return (
    <HomeLayout>
      <Outlet />
    </HomeLayout>
  );
};
```

4. Nest the home screens under a route that uses this layout:

```typescript
{
  id: "root",
  path: "/",
  element: <AuthLayout />,
  errorElement: <RootErrorBoundary />,
  loader: variantsLoader,
  children: [
    {
      element: <HomeLayoutWrapper />,
      children: [
        {
          index: true,
          element: <Home.MyGames />,
        },
        {
          path: "find-games",
          element: <Home.FindGames />,
        },
        {
          path: "create-game",
          element: <Home.CreateGame />,
        },
        {
          path: "sandbox",
          element: <Home.SandboxGames />,
        },
        {
          path: "profile",
          element: <Home.Profile />,
        },
        {
          path: "game-info/:gameId",
          element: <GameInfoLayout />,
          children: [
            {
              index: true,
              element: <Home.GameInfo />,
            },
          ],
        },
        {
          path: "player-info/:gameId",
          element: <Home.PlayerInfo />,
        },
      ],
    },
    // Game detail routes stay outside HomeLayoutWrapper
    {
      path: "game/:gameId",
      element: <GameLayout />,
      children: [
        // ... existing game detail routes
      ],
    },
  ],
}
```

This approach:
- Avoids repeating `<HomeLayout>` for every route
- Uses React Router's idiomatic nested layout pattern
- Keeps game detail routes separate (they use `GameDetailLayout` instead)

## STOP: Manual Testing Required

After making the above changes, start the dev server and manually test each screen:

```bash
cd packages/web
npm run dev
```

Test the following routes:
- [ ] `/` - My Games screen
- [ ] `/find-games` - Find Games screen
- [ ] `/create-game` - Create Game screen (standard tab)
- [ ] `/create-game?sandbox=true` - Create Game screen (sandbox tab)
- [ ] `/sandbox` - Sandbox Games screen
- [ ] `/profile` - Profile screen

For each screen, verify:
1. The screen loads without errors
2. Data fetching works (games list, variants, user profile)
3. Navigation between screens works
4. Interactive elements work (tabs, buttons, forms)
5. Responsive layout works (test mobile and desktop viewports)

## Step 3: Clean up old files (only after testing passes)

Once all screens are verified working, delete the old files:

```
packages/web/src/screens/Home/MyGames.tsx
packages/web/src/screens/Home/FindGames.tsx
packages/web/src/screens/Home/CreateGame.tsx
packages/web/src/screens/Home/Profile.tsx
packages/web/src/screens/Home/SandboxGames.tsx
packages/web/src/screens/Home/Layout.tsx
packages/web/src/screens/Home/AppBar.tsx
packages/web/src/screens/Home/SideNavigation.tsx
packages/web/src/screens/Home/InfoPanel.tsx
packages/web/src/screens/Home/BottomNavigation.tsx
packages/web/src/screens/Home/CreateStandardGame.tsx
packages/web/src/screens/Home/CreateSandboxGame.tsx
```

Then rename the `.new.tsx` files to remove the `.new` suffix:

```
MyGames.new.tsx -> MyGames.tsx
FindGames.new.tsx -> FindGames.tsx
CreateGame.new.tsx -> CreateGame.tsx
Profile.new.tsx -> Profile.tsx
SandboxGames.new.tsx -> SandboxGames.tsx
GameInfo.new.tsx -> GameInfo.tsx
PlayerInfo.new.tsx -> PlayerInfo.tsx
```

Update the `index.ts` imports accordingly.

## STOP: Final Verification

Run the full test suite and verify no regressions:

```bash
npm run lint
npm run build
```

## Completion Criteria

- All home screens load and function correctly
- No console errors
- Responsive layout works
- Old MUI-based files are deleted
- New files are renamed (`.new` suffix removed)
- Build passes without errors
