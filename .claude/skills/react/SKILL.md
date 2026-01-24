---
name: react
description: Comprehensive guidance for writing React code in diplicity-react, including components, forms, data loading, routing, testing, and validation. Use when implementing React features, refactoring React code, or reviewing React changes.
allowed-tools: Task, Read, Glob, Grep, Write, Edit, Bash, TodoWrite
---

# React Development Skill

This skill provides guidance for writing React code in the diplicity-react web application and helps you leverage detailed guidance files for comprehensive patterns and best practices.

## When to Use This Skill

Activate this skill when:

- Writing new React components or features
- Refactoring existing React code
- Implementing forms with validation
- Adding data loading with TanStack Query or RTK Query
- Working with React Router
- Writing or updating React tests
- Reviewing React code changes
- Migrating from Material UI to Radix UI components

## General React Workflow

1. **Before starting:**
   - Check `/packages/web/CLAUDE.md` for app-specific guidelines if it exists
   - Review existing components for patterns to follow
   - Understand the current tech stack (React 19, TypeScript, Vite)

2. **Component creation:** (See [./react-components.md](./react-components.md))
   - Check existing components in `src/components/` first
   - Use Radix UI primitives for new components (transitioning from Material UI)
   - Keep components focused and under 200 lines
   - Use compound component patterns for complex UIs
   - Remember we're using React 19 (no forwardRef, Context as provider)

3. **Data fetching:** (See [./react-data-loading.md](./react-data-loading.md) and [./react-zod.md](./react-zod.md))
   - Define Zod schemas first in appropriate schema files
   - Create `parseOnlyInDev` utility for safe API validation
   - Use TanStack Query for new features
   - Keep RTK Query for existing integrated features

4. **Forms:** (See [./react-hook-form.md](./react-hook-form.md) and [./react-zod.md](./react-zod.md))
   - Use React Hook Form for all form state management
   - Integrate Zod schemas via `zodResolver` for validation
   - Use `formState.isSubmitting` instead of custom state
   - Migrate away from Formik gradually

5. **Routing:**
   - Use React Router for navigation
   - Prefetch data in loaders when possible
   - Handle loading and error states properly

6. **Testing:** (See [./react-tests.md](./react-tests.md))
   - Write tests in `.test.tsx` files alongside components
   - Mock APIs with MSW (Mock Service Worker)
   - Use Testing Library patterns
   - Run tests with `npm run test`

7. **Code review:**
   - Run `npm run lint` to check for issues
   - Run `npm run build` to ensure TypeScript compilation
   - Fix any lint violations properly (never disable rules)
   - Ensure no unnecessary useEffect usage

## Key Principles

1. **Component Reuse:** Always check existing components before creating new ones (See [./react-components.md](./react-components.md))
2. **Runtime Safety:** Create and use `parseOnlyInDev` for API parsing to avoid production crashes (See [./react-zod.md](./react-zod.md))
3. **Type Safety:** Define Zod schemas first, infer TypeScript types with `z.infer` (See [./react-zod.md](./react-zod.md))
4. **Data Loading:** Use TanStack Query for new features, keep RTK Query for existing (See [./react-data-loading.md](./react-data-loading.md))
5. **Modern React:** Use React 19 features - Context as provider, no forwardRef (See [./react-components.md](./react-components.md))
6. **Form Excellence:** React Hook Form + Zod for all new forms (See [./react-hook-form.md](./react-hook-form.md))
7. **Test Coverage:** Write tests alongside features (See [./react-tests.md](./react-tests.md))
8. **No Rule Disabling:** Fix lint violations properly, never use eslint-disable or ts-ignore
9. **Minimize useEffect:** Avoid unnecessary effects, prefer derived state and event handlers (See [./react-use-effect-minimizer.md](./react-use-effect-minimizer.md))

## Tech Stack Overview

- **React 19** - Latest React with auto-memoization
- **TypeScript** - Strict typing throughout
- **Vite** - Build tool and dev server
- **TanStack Query** - Data fetching for new features
- **RTK Query** - Existing Redux-integrated data fetching
- **React Hook Form** - Form management (migrating from Formik)
- **Zod** - Schema validation
- **Radix UI** - Component primitives (migrating from Material UI)
- **Tailwind CSS** - Utility-first styling
- **MSW** - API mocking for tests
- **Vitest** - Test runner
- **Testing Library** - Component testing

## Detailed Guidance Files

For comprehensive patterns and best practices, consult these detailed guidance files:

- **[./react-components.md](./react-components.md)** - Component patterns, React 19 features, Radix UI migration, compound components
- **[./react-data-loading.md](./react-data-loading.md)** - TanStack Query patterns, query keys, caching strategies, prefetching
- **[./react-hook-form.md](./react-hook-form.md)** - Form state management, validation patterns, migration from Formik
- **[./react-tests.md](./react-tests.md)** - Testing patterns, MSW setup, Testing Library best practices
- **[./react-use-effect-minimizer.md](./react-use-effect-minimizer.md)** - When to use/avoid useEffect, refactoring patterns
- **[./react-zod.md](./react-zod.md)** - Zod schemas, safe parsing utility, type inference, form validation

### Quick Reference: Which Guidance File to Use?

- Creating a new component? → [./react-components.md](./react-components.md)
- Working with forms? → [./react-hook-form.md](./react-hook-form.md) + [./react-zod.md](./react-zod.md)
- Fetching data? → [./react-data-loading.md](./react-data-loading.md)
- Writing tests? → [./react-tests.md](./react-tests.md)
- Dealing with useEffect? → [./react-use-effect-minimizer.md](./react-use-effect-minimizer.md)
- Validating data? → [./react-zod.md](./react-zod.md)

## Common Tasks

### Creating a New Feature Component

1. Check if similar components exist
2. Use Radix UI primitives if creating new base components
3. Define Zod schema for any data
4. Set up TanStack Query for data fetching
5. Use React Hook Form for any forms
6. Write tests alongside the component

### Adding a New Form

1. Define Zod schema for validation
2. Set up React Hook Form with zodResolver
3. Use Radix UI form components (or Material UI if not migrated yet)
4. Handle submission in event handler, not useEffect
5. Show loading state with formState.isSubmitting

### Fetching Data

1. Define Zod schema for response
2. Create parseOnlyInDev utility if not exists
3. Create queryOptions with TanStack Query
4. Use in component with proper loading/error states
5. Invalidate queries after mutations

## Diplicity-Specific Patterns

Since this is a Diplomacy game application:

- **Game State**: Derive UI state from game data, don't duplicate in local state
- **Orders**: Use React Hook Form for order submission forms
- **Real-time Updates**: Handle WebSocket updates by invalidating queries
- **Map Interactions**: Use effects only for DOM manipulation, not state updates
- **Phase Management**: Compute phase-related UI state during render

## Migration Guidelines

The project is in transition:

- **Material UI → Radix UI**: New components use Radix, existing can stay
- **Formik → React Hook Form**: New forms use RHF, migrate existing gradually
- **Class Components → Functional**: All new components must be functional
- **Redux State → TanStack Query**: Prefer TanStack for server state

## Resources

- Project root: `/packages/web/`
- Components: `src/components/`
- Redux store: `src/store/`
- API schemas: Consider creating `src/store/api/schemas/`
- Utils: `src/utils/`
- Tests: Alongside components in `.test.tsx` files