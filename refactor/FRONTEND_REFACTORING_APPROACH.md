# Frontend Refactoring Approach

This document summarizes the refactoring approach being used to modernize the frontend codebase.

## 1. UI Framework Migration: Material UI → shadcn/ui + Tailwind CSS

**Old:** MUI components (`Stack`, `Box`, `Typography`, `Button`, `Avatar`, `Skeleton`, etc.)

**New:** shadcn/ui components (`Card`, `Button`, `Avatar`, `Skeleton`, `Tabs`, etc.) with Tailwind utility classes

## 2. Styling Approach Change: CSS-in-JS → Tailwind CSS

**Old:** `createUseStyles` with theme-aware style objects

```tsx
const useStyles = createUseStyles<GameCardProps>(() => ({
  mainContainer: theme => ({ borderBottom: `1px solid ${theme.palette.divider}` }),
}));
```

**New:** Tailwind utility classes directly in JSX

```tsx
<Card className="w-full flex flex-col md:flex-row overflow-hidden p-0">
```

## 3. Data Fetching Pattern: RTK Query → React Query with Suspense

**Old:** RTK Query hooks with loading/error state handling inline

```tsx
const query = service.endpoints.gamesList.useQuery({ mine: true });
if (query.isLoading) { ... }
if (query.isError) { ... }
```

**New:** Suspense-enabled hooks with wrapper components

```tsx
const { data: games } = useGamesListSuspense({ mine: true });
// Wrapped in <Suspense fallback={...}>
```

## 4. Component API Design: Internal State → Props-driven / Lifted State

**Old GameCard:** Fetches data internally, handles navigation internally

```tsx
const variant = useVariantById(props.game?.variantId ?? "");
const handleClickGame = () => navigate(`/game/${props.game.id}`);
```

**New GameCard:** Receives data and callbacks as props (more testable/composable)

```tsx
interface GameCardProps {
  game: GameList;
  variant: Pick<VariantRead, "name" | "id">;
  onClickGame: (id: string) => void;
  // ...
}
```

## 5. Layout Architecture: MUI Grid → Flexbox with shadcn Sidebar

**Old:** Custom `HomeLayout` with MUI `Grid2` and responsive conditional rendering

**New:** shadcn `SidebarProvider` + `Sidebar` + `SidebarInset` pattern with Tailwind responsive classes

## 6. Icon Library: Custom Icon component → Lucide React

**Old:** `<Icon name={IconName.Lock} />`

**New:** `<Lock className="h-3 w-3" />`

## 7. Form Handling: Manual state → react-hook-form + Zod

**Old:** Separate form components with their own state management

**New:** Unified forms using `react-hook-form` with `zodResolver` for validation

## Overall Goals

1. **Modernize the UI stack** to shadcn/ui + Tailwind (better DX, smaller bundle, more customizable)
2. **Improve data loading UX** with Suspense boundaries (cleaner code, better loading states)
3. **Make components more testable** by lifting state and using prop-driven APIs
4. **Simplify styling** with utility-first CSS instead of CSS-in-JS
5. **Standardize patterns** across screens (ScreenContainer, ScreenHeader, ScreenCard wrappers)

## File Mapping

| Old File | New File |
|----------|----------|
| `components/GameCard.tsx` | `components/GameCard.new.tsx` |
| `screens/Home/MyGames.tsx` | `screens/Home/MyGames.new.tsx` |
| `screens/Home/FindGames.tsx` | `screens/Home/FindGames.new.tsx` |
| `screens/Home/CreateGame.tsx` | `screens/Home/CreateGame.new.tsx` |
| `screens/Home/Profile.tsx` | `screens/Home/Profile.new.tsx` |
| `screens/Home/SandboxGames.tsx` | `screens/Home/SandboxGames.new.tsx` |
| `screens/Home/Layout.tsx` | `components/HomeLayout.tsx` |
