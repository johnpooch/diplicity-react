# Zod Best Practices & Guidelines

## Key Principles

### Production Safety with Zod Parsing

**Critical Best Practice:** Create a safe parsing utility that prevents production crashes while still catching errors in development.

**Create this utility in your project:**

```typescript
// src/utils/zod.ts
import { z } from 'zod';

export function parseOnlyInDev<T>(
  schema: z.ZodType<T>,
  data: unknown
): T {
  if (process.env.NODE_ENV === 'development' || process.env.NODE_ENV === 'test') {
    // In dev/test, throw errors to catch issues early
    return schema.parse(data);
  } else {
    // In production, log errors but don't crash
    const result = schema.safeParse(data);
    if (!result.success) {
      console.error('Schema validation failed:', result.error);
      // Could also send to Sentry or other error tracking
    }
    return result.success ? result.data : data as T;
  }
}
```

**Usage with TanStack Query (you have @tanstack/react-query installed):**

```typescript
// ❌ BEFORE - Using .parse() directly
export async function getGameDetails(gameId: string) {
  const response = await fetch(`/api/games/${gameId}`);
  const data = await response.json();
  return gameDetailsSchema.parse(data); // Can crash in production!
}

// ✅ AFTER - Using parseOnlyInDev with TanStack Query
import { queryOptions, useQuery } from "@tanstack/react-query";
import { parseOnlyInDev } from "@/utils/zod";

// Step 1: Create the fetcher function with parseOnlyInDev
const getGameDetails = async (gameId: string) => {
  const response = await fetch(`/api/games/${gameId}`);
  const data = await response.json();
  return parseOnlyInDev(gameDetailsSchema, data); // Safe in production!
};

// Step 2: Extract queryOptions for reusability
export const getGameDetailsQueryOptions = (gameId: string) => {
  return queryOptions({
    queryKey: ["gameDetails", gameId],
    queryFn: () => getGameDetails(gameId),
  });
};

// Step 3: Create the hook for components
export const useGameDetails = (gameId: string) => {
  return useQuery(getGameDetailsQueryOptions(gameId));
};
```

**Rationale:**
- Prevents production pages from crashing due to unexpected API response shapes
- Still catches schema violations during development and testing
- Logs errors for monitoring without breaking user experience
- Follows TanStack Query patterns for caching and invalidation

### Single Source of Truth Pattern

**Best Practice:** Define schemas once with Zod and derive TypeScript types from them. Avoid duplicate type definitions.

```typescript
// ❌ BEFORE - Duplicate type definitions
const gameSchema = z.object({
  id: z.string(),
  name: z.string(),
  phase: z.string(),
  variant: z.string(),
});

// Redundant interface that duplicates the schema
export interface Game {
  id: string;
  name: string;
  phase: string;
  variant: string;
}

// ✅ AFTER - Single source of truth
const gameSchema = z.object({
  id: z.string(),
  name: z.string(),
  phase: z.string(),
  variant: z.string(),
});

// Only derive types from schema
export type Game = z.infer<typeof gameSchema>;
```

**Key Points:**
- Prevents schema/type drift
- Maintains single source of truth
- Use `z.infer<typeof schema>` for type generation
- Export types from the same file as schemas

### File Organization

**Structure for diplicity-react:**

```
packages/web/src/
├── utils/
│   └── zod.ts                    # parseOnlyInDev utility
├── store/
│   └── api/
│       ├── schemas/
│       │   ├── game.schema.ts    # Game-related schemas
│       │   ├── order.schema.ts   # Order-related schemas
│       │   └── user.schema.ts    # User-related schemas
│       └── endpoints/
│           ├── games.ts           # Game API endpoints using schemas
│           └── orders.ts          # Order API endpoints using schemas
```

**Guidelines:**
- Place `parseOnlyInDev` utility in `src/utils/zod.ts`
- Keep related schemas together in schema files
- Export both schemas and inferred types from schema files
- Import and use schemas in API endpoint files

### Form Validation with React Hook Form

**Best Practice:** Use Zod schemas with react-hook-form resolver for form validation (you have @hookform/resolvers installed).

```typescript
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

// Define form schema
const createGameSchema = z.object({
  name: z.string().min(1, "Game name is required"),
  variant: z.string(),
  description: z.string().optional(),
  isPrivate: z.boolean(),
  maxPlayers: z.number().min(2).max(7),
});

type CreateGameFormData = z.infer<typeof createGameSchema>;

// Use with react-hook-form
function CreateGameForm() {
  const form = useForm<CreateGameFormData>({
    resolver: zodResolver(createGameSchema),
    defaultValues: {
      isPrivate: false,
      maxPlayers: 7,
    },
  });

  const onSubmit = async (data: CreateGameFormData) => {
    // Data is already validated by Zod
    await createGame(data);
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

### Integration with RTK Query

Since you use Redux Toolkit with RTK Query, here's how to integrate Zod:

```typescript
// store/api/schemas/game.schema.ts
import { z } from 'zod';

export const gameSchema = z.object({
  id: z.string(),
  name: z.string(),
  phase: z.string(),
  // ... other fields
});

export type Game = z.infer<typeof gameSchema>;

// store/api.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { parseOnlyInDev } from '@/utils/zod';
import { gameSchema, type Game } from './schemas/game.schema';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    getGame: builder.query<Game, string>({
      query: (id) => `games/${id}`,
      transformResponse: (response: unknown) => {
        return parseOnlyInDev(gameSchema, response);
      },
    }),
  }),
});
```

### When to Use Zod Schemas

**Use Zod schemas for:**
- ✅ API response validation
- ✅ Form validation
- ✅ External data parsing (Firebase, WebSockets, etc.)
- ✅ Any untrusted data sources
- ✅ Data that needs runtime validation

**Skip Zod schemas when:**
- ❌ Only defining request payload types (no parsing needed)
- ❌ Internal type definitions that don't need validation
- ❌ Simple utility functions with clear TypeScript types

### Common Patterns for Diplomacy Game

```typescript
// Example schemas for Diplomacy-specific data
const provinceSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['land', 'sea', 'coast']),
  supplyCenter: z.boolean(),
  owner: z.string().nullable(),
});

const orderSchema = z.object({
  id: z.string(),
  type: z.enum(['move', 'support', 'convoy', 'hold']),
  unitId: z.string(),
  from: z.string(),
  to: z.string().optional(),
  via: z.string().optional(),
  status: z.enum(['pending', 'succeeded', 'failed', 'invalid']),
});

const phaseSchema = z.object({
  year: z.number(),
  season: z.enum(['spring', 'fall']),
  type: z.enum(['movement', 'retreat', 'adjustment']),
});

export type Province = z.infer<typeof provinceSchema>;
export type Order = z.infer<typeof orderSchema>;
export type Phase = z.infer<typeof phaseSchema>;
```

## Migration from Existing Patterns

Since you have both Formik and Zod installed, gradually migrate:

1. **Replace Formik validation with Zod schemas**
2. **Add parseOnlyInDev utility to your utils**
3. **Wrap existing API calls with safe parsing**
4. **Define schemas for all API responses**
5. **Derive TypeScript types from schemas**

## Summary

Using Zod effectively in your React application:
- Provides runtime type safety
- Prevents production crashes with safe parsing
- Maintains single source of truth for types
- Integrates well with React Hook Form and RTK Query
- Improves developer experience with clear validation errors