---
paths:
  - "packages/web/src/**/*.{ts,tsx}"
---

# Frontend conventions (`packages/web/`)

React 19 + TypeScript, Vite, React Router, TanStack Query, shadcn/ui + Tailwind, Vitest.

`src/api/generated/` is produced by orval. Never edit it — run `docker compose up codegen`.

## Data and state

- Use `useXxxSuspense` hooks for reads. Never the non-suspense variants.
- Use `useXxxMutation` with `mutateAsync` for writes, never `mutate` — `mutateAsync` propagates errors to your `catch`.
- **TanStack Query for all new data loading.** Existing RTK Query integrations stay as they are; do not extend them and do not add new ones. Do not add Redux for client state.

### State hierarchy

1. **Backend** — source of truth for all domain data
2. **URL** — navigation state, tabs, filters (`useSearchParams`, `useParams`)
3. **Local state** — pure UI concerns only (e.g. `isEditingName`)

If state can be derived from the backend or the URL, it must be.

**Review check:** domain data in `useState`? navigation state in `useState`? a `useEffect` syncing state? All should be derived instead.

### Suspense guarantees

Components can assume data is loaded — no loading checks inside them. Fetch from URL params rather than passing entity data through Context:

```typescript
const { gameId } = useRequiredParams<{ gameId: string }>();
const { data: game } = useGameRetrieveSuspense(gameId);
// BAD: const { game } = useGameContext();
```

React Query deduplicates requests, so multiple components fetching the same ID share one request.

### Mutations in useEffect dependencies

Never include mutation objects in a `useEffect` dependency array — the object gets a new reference on every state change (idle → pending → success/error), causing an infinite loop.

```typescript
// BAD - infinite loop
const mut = useCreateMutation();
useEffect(() => { mut.mutateAsync(data); }, [condition, mut]);

// GOOD - mutateAsync is stable; omit the mutation object
const mut = useCreateMutation();
useEffect(() => { mut.mutateAsync(data); }, [condition]);
// eslint-disable-next-line react-hooks/exhaustive-deps -- mutateAsync stable
```

This is the **only** sanctioned `eslint-disable` in the codebase.

### Polling

Only poll (`refetchInterval`) an endpoint whose view uses `ConditionalGetMixin` or `PrecomputedConditionalGetMixin`. The precomputed variant also skips building the response, and it is allowed only when tests cover every response input. The browser/WebView revalidates with `If-None-Match` and receives an empty 304 when nothing changed; client code needs nothing extra. Do not add cache-busting query params or `Cache-Control` request headers to a polled request — both defeat revalidation.

Otherwise, minimise `useEffect` — prefer derived state and event handlers.


### Request telemetry

Request reasons are derived from query state. Pass `meta: { prefetch: true }` only to a speculative fetch nobody is waiting on, such as warming a cache in an effect. Never set it on a route loader fetch or any fetch that gates rendering: the user waits on it, so it is a `mount` and is classified that way by default.

## Components

Screens live in `src/screens/` (or feature subdirectories like `screens/GameDetail/`); shared components in `src/components/`. Keep it flat. Check `src/components/` for an existing component before creating a new one. Keep components under 200 lines.

React 19: no `forwardRef`, `<Context>` used directly as provider.

### Suspense wrapper pattern

Every screen that fetches data needs this structure:

```typescript
const MyScreen: React.FC = () => {
  const { data } = useDataSuspense();
  return <div>...</div>;
};

const MyScreenSuspense: React.FC = () => (
  <ScreenContainer>
    <ScreenHeader title="My Screen" />
    <QueryErrorBoundary>
      <Suspense fallback={<MyScreenSkeleton />}>
        <MyScreen />
      </Suspense>
    </QueryErrorBoundary>
  </ScreenContainer>
);

export { MyScreenSuspense as MyScreen };
```

`QueryErrorBoundary` must wrap `Suspense`, not sit inside it — otherwise query errors crash the whole page instead of showing a "Try Again" UI in the content area.

**Review check:** inner component uses `useXxxSuspense`? outer has `ScreenContainer + ScreenHeader + QueryErrorBoundary + Suspense`? fallback is a skeleton mirroring the screen's content and dimensions (not an empty div or a centred spinner) with no layout shift on swap — see the UX skill's loading-states guidance? wrapper exported under the screen name?

### Inline over extract

Inline sub-components and utility functions used in only one place. Extract to a separate file only when genuinely shared across screens. `CreateGame.tsx` is the canonical example.

### Prop types

Always use an explicit interface. Infer types for local return values.

```typescript
interface GameCardProps { game: Game; variant: Variant; }
const GameCard: React.FC<GameCardProps> = ({ game, variant }) => { ... };
// BAD: React.FC<{ game: Game; variant: Variant }>
```

### Layout architecture

Screens are rendered inside a layout. A screen must not wrap itself in one.

```typescript
// BAD - screen wraps itself in layout
const OrdersScreen = () => <GameDetailLayout><Panel>...</Panel></GameDetailLayout>;
```

### Custom hooks

Hooks live in `src/hooks/`. Create one only when the logic is needed in multiple components **and** it encapsulates a genuine concern (not a one-line wrapper). Current hooks: `useRequiredParams`, `useMapData`, `use-mobile`.

**Review check:** used in more than one place? more than a wrapper around a single call? in `src/hooks/` and exported from the index?

## Navigation

Use React Router hooks (`useNavigate`, `useParams`, `useSearchParams`, `useLocation`) and `Link` for declarative navigation. Store shareable or bookmarkable state in the URL. Use `useRequiredParams` for typed route params guaranteed by the route structure — it eliminates runtime null checks.

A public page that renders whether or not the visitor is logged in (the blog, the code of conduct) is wrapped in `PublicPageLayout`, declared once in `Router.tsx` and spread into both `createAuthenticatedRoutes` and `createUnauthenticatedRoutes`, ahead of each tree's catch-all. It sits outside the authenticated root, so it skips that root's loader, and it must not render `ScreenHeader` or anything else that reads the current user.

Images embedded in blog posts are committed to `packages/web/public/blog-images/` as compressed WebP, sized for the 672px content column at 2x, and referenced from the post's Markdown by absolute path. Everything in `public/` ships inside the mobile app bundle, so keep them few and small.

## UI

- Use shadcn/ui components over raw HTML, and Lucide icons (`lucide-react`).
- Use `Notice` for empty states — never an ad-hoc div with text.
- Use `ScreenCard` for home screen content.

```typescript
<Notice title="No staging games" message="Go to Find Games to join a game." icon={Inbox} />
// BAD: <div className="text-center text-muted-foreground p-8"><p>No games found</p></div>
```

### Buttons

Pick the button by its role from `@/components/ui/role-buttons`, never by setting `variant` or `size` on `Button`. The role components do not accept either prop.

| Role | Component | Renders | Examples |
| --- | --- | --- | --- |
| The one main action of a screen, panel, form or empty state | `PrimaryButton` | `default` | Submit report, Accept, Find games |
| Any other action, including full-width panel actions and the alternative beside a primary | `SecondaryButton` | `outline` | Cancel proposal, Report player, Reject, Log out |
| An entry point to a destructive flow that sits among secondary actions | `SecondaryButton destructive` | `outline`, destructive text | Delete account on `Account` |
| The button that performs an irreversible action itself | `DestructiveButton` | `destructive` | Delete Account on `DeleteAccount` |
| Icon-only action in `GameDetailAppBar` (`rightButton`, the phase stepper, the game menu trigger) | `AppBarIconButton` | `outline`, `icon` | Share game, Create channel |
| Icon-only action inline with content or in a `ScreenHeader` | `IconButton` | `ghost`, `icon` | Edit name, Delete order, Toggle filters |
| A row in a `divide-y` card list that is itself the action | `RowActionButton` | full-width row, `destructive` for red | `ActionList` rows, Mute notifications, View my profile |

Layout stays with the caller: a column parent stretches buttons full width, and `className="flex-1"` or `w-full` sizes them in a row. Icon buttons take a required `aria-label`. Confirmation dialogs use `AlertDialogAction` and `AlertDialogCancel`, not these.

`Button` is only for controls none of these roles describe, such as map overlays, segmented options, and compact `size="sm"` toolbars on admin screens. If a new screen needs a role that is not listed, add a component here rather than choosing a variant ad hoc.

### Game and member actions

The backend decides which game and member actions appear, on which screen, in what order, and whether each is blocked. Each screen renders the list the response gives it for that screen (game info renders `actions`, the players screen renders `playerListActions`, the member screen renders the member's `actions`) with `ActionList`, unchanged; never filter, reorder or decide availability on the client. If a screen needs a different set, the backend returns a new list. A new action key gets its label, icon, copy and confirmation in `actionDisplay.ts` and its handler in `ActionList`.

### Tailwind

Only add classes that do something. Question every class: does it override a default that needs overriding? Is the spacing already handled by a parent `gap`?

Commonly unnecessary: `min-w-0` when width is already constrained, `flex-shrink-0` when already handled, `h-8 w-8` when `size="icon"` sets it, `ml-4` when `gap` handles it, `h-4 w-4` on icons when the default is fine. Trust shadcn defaults.

**Review check:** any Tailwind classes that change nothing? icon sizes specified when the default is correct?

## Forms

React Hook Form + Zod for all forms. The type is derived from the schema.

```typescript
const schema = z.object({ name: z.string().min(1, "Required") });
type FormValues = z.infer<typeof schema>;

const MyForm: React.FC = () => {
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { name: "" } });
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField control={form.control} name="name" render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl><Input {...field} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
      </form>
    </Form>
  );
};
```

**Review check:** Zod validation? type via `z.infer`? every `FormField` has `FormItem + FormLabel + FormControl + FormMessage`? `form.handleSubmit` used? `defaultValues` for all fields?

## User feedback

```typescript
const handleCreate = async (data: FormValues) => {
  try {
    await createMutation.mutateAsync({ data });
    navigate("/");
  } catch {
    toast.error("Failed to create");
  }
};
```

Do not add a success toast unless one is explicitly asked for — by the user, the issue, or a written rule such as the game-orders confirmation in the `ux-patterns` skill. Always keep the error toast.

**Review check:** every mutation has try/catch? success toast only where explicitly asked for? error toast in all catch paths?

## Runtime safety

Use `parseOnlyInDev` for API parsing so a schema mismatch does not crash production. Define Zod schemas first and infer TypeScript types with `z.infer`. Never use `any`.

## Before submitting

- `npm run lint` in `packages/web` (changed files only where possible)
- `npx tsc -b --noEmit` in `packages/web` (required after codegen or type changes)
- `npm run test`

Fix violations properly; never disable a rule.
