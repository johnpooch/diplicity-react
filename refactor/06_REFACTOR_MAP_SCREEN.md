# 06: Refactor Map Screen

## Context

Refactor the Map Screen following the patterns documented in `FRONTEND_REFACTORING_APPROACH.md`.

**Important constraints:**
- Keep the `GameDetailLayout` component mostly unchanged for now
- Do NOT change the overall screen structure or UX
- Achieve 1:1 functional parity with the existing implementation
- The `GameMap` component itself does NOT need refactoring in this step (it's a complex SVG component)

## Files to Refactor

**Main file:**
- `packages/web/src/screens/GameDetail/MapScreen.tsx`

## Current Implementation Analysis

The current `MapScreen.tsx` is relatively simple:
- Uses `GameDetailLayout` wrapper
- Uses `GameDetailAppBar` with `PhaseSelect` component
- Uses `Panel` component for structure
- Uses `GameMap` component for the actual map rendering

This is one of the simpler screens to refactor.

## Refactoring Requirements

### 1. Create `MapScreen.new.tsx`

Create a new file at `packages/web/src/screens/GameDetail/MapScreen.new.tsx` that:

1. **Replaces Panel component** with simple div structure or shadcn Card:
   - The Panel is just providing a container, can be replaced with Tailwind classes

2. **Keeps these components as-is** (they work independently):
   - `GameDetailLayout` - don't refactor yet
   - `GameDetailAppBar` - keep using existing
   - `PhaseSelect` - keep using existing
   - `GameMap` - keep using existing (complex SVG component)

3. **Wraps in Suspense** for consistency with other screens

### 2. Component Structure

```tsx
import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { PhaseSelect } from "../../components/PhaseSelect";
import { GameMap } from "../../components/GameMap";

const MapScreen: React.FC = () => {
  const navigate = useNavigate();

  return (
    <GameDetailLayout
      appBar={
        <GameDetailAppBar
          title={<PhaseSelect />}
          onNavigateBack={() => navigate("/")}
        />
      }
      content={
        <div className="flex flex-col h-full">
          <GameMap />
        </div>
      }
    />
  );
};

const MapScreenSuspense: React.FC = () => {
  return (
    <Suspense fallback={<div></div>}>
      <MapScreen />
    </Suspense>
  );
};

export { MapScreenSuspense as MapScreen };
```

### 3. Create Storybook File

Create `packages/web/src/screens/GameDetail/MapScreen.new.stories.tsx`:

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { MapScreen } from "./MapScreen.new";
// Import mock handlers and data

const meta = {
  title: "Screens/GameDetail/MapScreen",
  component: MapScreen,
  parameters: {
    layout: "fullscreen",
    msw: {
      handlers: [
        // Mock game retrieve
        // Mock phase retrieve
        // Mock variants list
      ],
    },
  },
} satisfies Meta<typeof MapScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
```

## Note on GameMap Component

The `GameMap` component is a complex SVG-based interactive map component. It should NOT be refactored as part of this migration because:

1. It doesn't use MUI components
2. It's a specialized rendering component
3. Refactoring it would be a significant undertaking with high risk

The `InteractiveMap` component it uses is already well-structured and doesn't depend on MUI.

## STOP: Manual Testing Required

After creating the new file:

1. Update the GameDetail index to use the new component temporarily
2. Start the dev server: `npm run dev`
3. Navigate to a game's map screen (`/game/:gameId` on mobile, or click map view)
4. Verify:
   - Map renders correctly
   - Phase select works
   - Back navigation works
   - Map interactions (zoom, pan) work

## STOP: Storybook Testing

Run Storybook and verify all stories render correctly:

```bash
npm run storybook
```

## Completion Criteria

- [ ] `MapScreen.new.tsx` created
- [ ] No MUI imports in the new file (Panel replaced)
- [ ] Suspense boundary implemented
- [ ] Storybook stories created and rendering
- [ ] Manual testing passes
- [ ] No TypeScript errors
