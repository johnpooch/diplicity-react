# Bundle Size Analysis Task

## Objective

Conduct a comprehensive survey of the `packages/web` React application to identify opportunities to reduce bundle size and improve performance. A previous analysis was done but is now outdated due to ongoing migration work.

## Background

This app is undergoing a migration:
- **From**: Material UI + Redux Toolkit + RTK Query
- **To**: shadcn/ui (Radix + Tailwind) + TanStack Query

The migration may be complete or near-complete. Your job is to verify the current state and identify what can be removed or optimized.

## Analysis Tasks

### 1. Dependency Audit

Examine `package.json` and determine for each dependency:
- Is it actually used in the codebase?
- Can it be removed?
- Is there a lighter alternative?

**Specific dependencies to investigate:**

| Dependency | Suspected Status | Action Needed |
|------------|------------------|---------------|
| `@mui/material` | Possibly removable | Check if any MUI components are still imported |
| `@mui/icons-material` | Possibly removable | Check if MUI icons are still used |
| `@emotion/react` | Possibly removable | Only needed for MUI |
| `@emotion/styled` | Possibly removable | Only needed for MUI |
| `@reduxjs/toolkit` | Possibly removable | Check if Redux is still used |
| `react-redux` | Possibly removable | Check if Redux is still used |
| `formik` | Possibly removable | Check if migrated to react-hook-form |
| `zod-formik-adapter` | Possibly removable | Only needed for Formik |
| `pako` | Unknown | Search for usage |
| `xmldom` | Unknown | Search for usage |
| `lodash` | Unknown | Search for usage |

### 2. Import Analysis

Search the codebase to find actual usage:

```bash
# Check for MUI imports
grep -r "from '@mui" src/ --include="*.tsx" --include="*.ts"
grep -r 'from "@mui' src/ --include="*.tsx" --include="*.ts"

# Check for Redux imports
grep -r "from 'react-redux" src/ --include="*.tsx" --include="*.ts"
grep -r 'from "react-redux' src/ --include="*.tsx" --include="*.ts"
grep -r "from '@reduxjs" src/ --include="*.tsx" --include="*.ts"
grep -r 'from "@reduxjs' src/ --include="*.tsx" --include="*.ts"

# Check for Formik imports
grep -r "from 'formik" src/ --include="*.tsx" --include="*.ts"
grep -r 'from "formik' src/ --include="*.tsx" --include="*.ts"

# Check for other suspicious dependencies
grep -r "from 'pako" src/ --include="*.tsx" --include="*.ts"
grep -r "from 'xmldom" src/ --include="*.tsx" --include="*.ts"
grep -r "from 'lodash" src/ --include="*.tsx" --include="*.ts"
```

### 3. Code Splitting Analysis

Check current state of code splitting:
- Is `React.lazy()` being used for route-based splitting?
- Are there `Suspense` boundaries?
- Check `Router.tsx` for dynamic imports
- Check `vite.config.ts` for chunk splitting configuration

### 4. Observability Stack Analysis

The app includes heavy observability dependencies:
- OpenTelemetry (8 packages)
- Sentry
- Firebase (for push notifications)

Determine:
- Are these loaded conditionally or always?
- Can they be lazy-loaded?
- Are all OpenTelemetry packages necessary?

### 5. Icon Usage Analysis

Check `src/components/Icon.tsx`:
- Which icon libraries are being used?
- Are icons imported statically or dynamically?
- Can we consolidate to a single icon library (preferably Lucide)?

### 6. Dead Code Detection

Look for:
- Files with `.new.tsx` suffix that have superseded old versions
- Unused exports
- Commented out code
- Test/story files that import production code unnecessarily

### 7. Build Configuration

Review `vite.config.ts` for:
- Manual chunk configuration
- Tree-shaking settings
- Build optimizations
- Bundle analyzer setup (add if missing)

## Deliverables

Create a prioritized action plan with:

1. **Immediate Removals** - Dependencies/code that can be deleted now
2. **Quick Migrations** - Small changes needed before removal
3. **Code Splitting Opportunities** - Routes/components to lazy load
4. **Build Optimizations** - Vite/Rollup configuration changes
5. **Estimated Impact** - Rough size savings for each change

## Success Criteria

- Identify all unused dependencies
- Confirm whether MUI and Redux can be fully removed
- Provide specific file paths and code changes needed
- Prioritize by effort vs. impact

## Commands to Help

```bash
# Run build and check output size
npm run build

# If bundle analyzer is configured
npm run build -- --analyze

# Check for duplicate dependencies
npm ls --all | grep -E "(mui|redux|formik)"

# Find all TypeScript/React files still importing specific packages
find src -name "*.tsx" -o -name "*.ts" | xargs grep -l "@mui"
```

## Notes

- The goal is to get the bundle as small as possible while maintaining functionality
- Prefer removing entire dependencies over partial optimization
- Document any dependencies that MUST stay and why
