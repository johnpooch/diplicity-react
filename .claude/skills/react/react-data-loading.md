# Data Loading Best Practices

## Core Principles

- Always use TanStack Query for all data fetching and mutations
- Prefer `isPending` over `isLoading` for loading states
- Use `useQueries` with `combine` for multiple queries
- Use `useSuspenseQuery` in suspense boundaries
- Use `parseOnlyInDev` for API validation (see react-zod.md)
- Always `invalidateQueries` after mutations
- Extract queryOptions for reusability
- Never hand-roll queryOptions or queryKeys

## TanStack Query Setup

Since you have both RTK Query and TanStack Query, here's how to use TanStack Query effectively:

### Basic Query Pattern

```tsx
// ❌ Don't use useEffect with manual fetch
useEffect(() => {
  const fetchData = async () => {
    const response = await fetch("/api/games");
    const json = await response.json();
    setGames(json);
    setLoading(false);
  };
  fetchData();
}, []);

// ✅ Use TanStack Query
import { queryOptions, useQuery } from "@tanstack/react-query";
import { parseOnlyInDev } from "@/utils/zod";
import { gamesSchema } from "@/store/api/schemas/game.schema";

// Step 1: Create fetcher function
const getGames = async () => {
  const response = await fetch("/api/games");
  const data = await response.json();
  return parseOnlyInDev(gamesSchema, data);
};

// Step 2: Extract queryOptions for reusability
export const gamesQueryOptions = queryOptions({
  queryKey: ["games"],
  queryFn: getGames,
  staleTime: 5 * 60 * 1000, // 5 minutes
});

// Step 3: Use in component
export function GamesList() {
  const { data, isPending, isError } = useQuery(gamesQueryOptions);

  if (isPending) return <div>Loading games...</div>;
  if (isError) return <div>Error loading games</div>;

  return (
    <div>
      {data.map(game => (
        <GameCard key={game.id} game={game} />
      ))}
    </div>
  );
}
```

### Query with Parameters

```tsx
// Define parameterized queryOptions
export const gameDetailsQueryOptions = (gameId: string) =>
  queryOptions({
    queryKey: ["games", gameId],
    queryFn: async () => {
      const response = await fetch(`/api/games/${gameId}`);
      const data = await response.json();
      return parseOnlyInDev(gameDetailsSchema, data);
    },
    enabled: !!gameId, // Only run if gameId exists
  });

// Use in component
export function GameDetail({ gameId }: { gameId: string }) {
  const { data, isPending } = useQuery(gameDetailsQueryOptions(gameId));
  // ...
}
```

### Mutations with Automatic Cache Invalidation

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";

// Define mutation function
const createOrder = async (orderData: CreateOrderData) => {
  const response = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderData),
  });

  if (!response.ok) {
    throw new Error("Failed to create order");
  }

  const data = await response.json();
  return parseOnlyInDev(orderSchema, data);
};

// Use in component
export function OrderForm({ gameId }: { gameId: string }) {
  const queryClient = useQueryClient();

  const createOrderMutation = useMutation({
    mutationFn: createOrder,
    onSuccess: () => {
      // Invalidate relevant queries after successful mutation
      queryClient.invalidateQueries({ queryKey: ["games", gameId] });
      queryClient.invalidateQueries({ queryKey: ["orders", gameId] });
    },
    onError: (error) => {
      console.error("Failed to create order:", error);
      // Handle error (show toast, etc.)
    },
  });

  const handleSubmit = (orderData: CreateOrderData) => {
    createOrderMutation.mutate(orderData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button
        type="submit"
        disabled={createOrderMutation.isPending}
      >
        {createOrderMutation.isPending ? "Submitting..." : "Submit Order"}
      </button>
    </form>
  );
}
```

### Multiple Queries with useQueries

```tsx
import { useQueries } from "@tanstack/react-query";

export function Dashboard() {
  const results = useQueries({
    queries: [
      gamesQueryOptions,
      userProfileQueryOptions,
      notificationsQueryOptions,
    ],
    combine: (results) => {
      return {
        data: results.map((result) => result.data),
        isPending: results.some((result) => result.isPending),
        isError: results.some((result) => result.isError),
      };
    },
  });

  if (results.isPending) return <div>Loading dashboard...</div>;
  if (results.isError) return <div>Error loading dashboard</div>;

  const [games, profile, notifications] = results.data;
  // Render dashboard with all data
}
```

### Suspense Mode with useSuspenseQuery

```tsx
import { useSuspenseQuery } from "@tanstack/react-query";
import { Suspense } from "react";

// Component using suspense query
function GameDetailsContent({ gameId }: { gameId: string }) {
  // This will suspend until data is available
  const { data } = useSuspenseQuery(gameDetailsQueryOptions(gameId));

  return <div>{/* Render game details */}</div>;
}

// Parent component with Suspense boundary
export function GameDetailsPage({ gameId }: { gameId: string }) {
  return (
    <Suspense fallback={<div>Loading game details...</div>}>
      <GameDetailsContent gameId={gameId} />
    </Suspense>
  );
}
```

### Optimistic Updates

```tsx
const updateOrderMutation = useMutation({
  mutationFn: updateOrder,
  onMutate: async (newOrder) => {
    // Cancel in-flight queries
    await queryClient.cancelQueries({ queryKey: ["orders", gameId] });

    // Snapshot previous value
    const previousOrders = queryClient.getQueryData(["orders", gameId]);

    // Optimistically update
    queryClient.setQueryData(["orders", gameId], (old) => {
      return [...old, newOrder];
    });

    // Return context with snapshot
    return { previousOrders };
  },
  onError: (err, newOrder, context) => {
    // Rollback on error
    queryClient.setQueryData(
      ["orders", gameId],
      context.previousOrders
    );
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ["orders", gameId] });
  },
});
```

### Prefetching in React Router Loaders

```tsx
import { queryClient } from "@/store/queryClient";

// In your route loader
export const gameLoader = async ({ params }) => {
  const gameId = params.gameId;

  // Prefetch game details
  await queryClient.prefetchQuery(gameDetailsQueryOptions(gameId));

  // Prefetch related data
  await queryClient.prefetchQuery(gameOrdersQueryOptions(gameId));

  return { gameId };
};

// In your component
export function GamePage() {
  const { gameId } = useLoaderData();

  // This will use cached data from the loader
  const { data } = useQuery(gameDetailsQueryOptions(gameId));
  // ...
}
```

## Integration with Existing RTK Query

Since you have RTK Query set up, you can gradually migrate or use both:

### When to use TanStack Query
- Complex caching requirements
- Optimistic updates
- Infinite queries/pagination
- Suspense mode
- Background refetching with fine control

### When to keep RTK Query
- Tightly integrated with Redux state
- Simple CRUD operations
- Already working endpoints

### Example Migration Pattern

```tsx
// Old: RTK Query
const { data, isLoading } = useGetGameQuery(gameId);

// New: TanStack Query
const { data, isPending } = useQuery(gameDetailsQueryOptions(gameId));
```

## WebSocket/Real-time Updates

For your Diplomacy game's real-time features:

```tsx
import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

export function useGameUpdates(gameId: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Update cache based on event type
      if (update.type === "order_submitted") {
        queryClient.invalidateQueries({ queryKey: ["orders", gameId] });
      } else if (update.type === "phase_change") {
        queryClient.invalidateQueries({ queryKey: ["games", gameId] });
      }
    };

    return () => ws.close();
  }, [gameId, queryClient]);
}
```

## Error Handling Pattern

```tsx
import { useQuery } from "@tanstack/react-query";
import { toast } from "your-toast-library"; // Add a toast library

export function useGameData(gameId: string) {
  return useQuery({
    ...gameDetailsQueryOptions(gameId),
    throwOnError: false,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    meta: {
      errorMessage: "Failed to load game details",
    },
    onError: (error) => {
      toast.error("Failed to load game. Please try again.");
      console.error("Game loading error:", error);
    },
  });
}
```

## Best Practices Summary

1. **Always extract queryOptions** - Makes queries reusable in loaders and components
2. **Use isPending, not isLoading** - More accurate loading state
3. **Invalidate after mutations** - Keep cache fresh
4. **Use parseOnlyInDev** - Prevent production crashes from API changes
5. **Prefetch in loaders** - Better perceived performance
6. **Handle errors gracefully** - Show user-friendly messages
7. **Use Suspense for new features** - Cleaner loading states
8. **Combine queries when needed** - Reduce loading states