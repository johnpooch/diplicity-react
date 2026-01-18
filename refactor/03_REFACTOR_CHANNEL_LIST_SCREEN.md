# 03: Refactor Channel List Screen

## Context

Refactor the Channel List Screen following the patterns documented in `FRONTEND_REFACTORING_APPROACH.md`.

**Important constraints:**
- Keep the `GameDetailLayout` component mostly unchanged for now
- Do NOT change the overall screen structure or UX
- Achieve 1:1 functional parity with the existing implementation

## Files to Refactor

**Main file:**
- `packages/web/src/screens/GameDetail/ChannelListScreen.tsx`

## Current Implementation Analysis

The current `ChannelListScreen.tsx`:
- Uses MUI components: `Box`, `Button`, `Chip`, `Divider`, `List`, `ListItem`, `ListItemButton`, `ListItemText`, `Stack`, `Typography`
- Uses `createUseStyles` for styling
- Uses `Panel` component for layout structure
- Uses `GameDetailLayout` wrapper
- Uses `Icon` component for icons
- Uses RTK Query for data fetching

## Refactoring Requirements

### 1. Create `ChannelListScreen.new.tsx`

Create a new file at `packages/web/src/screens/GameDetail/ChannelListScreen.new.tsx` that:

1. **Replaces MUI components** with shadcn/ui + Tailwind:
   - `Stack` → `div` with Tailwind flex classes
   - `Button` → `@/components/ui/button`
   - `Chip` → `@/components/ui/badge` or simple styled span
   - `List`, `ListItem`, `ListItemButton`, `ListItemText` → simple divs with click handlers
   - `Divider` → `<hr>` or border classes
   - `Typography` → heading/paragraph tags with Tailwind
   - `Box` → `div`

2. **Updates data fetching** to use the new React Query hooks with Suspense:
   - Replace `service.endpoints.gamesChannelsList.useQuery()` with generated hook
   - Wrap the component in Suspense boundary
   - Export a `ChannelListScreenSuspense` component

3. **Replaces Icon usage** with Lucide React:
   - `IconName.NoChannels` → appropriate Lucide icon
   - `IconName.GroupAdd` → `UserPlus` from Lucide

4. **Keeps the GameDetailLayout usage** - don't refactor the layout itself

5. **Updates related component imports:**
   - Use `@/components/Notice.new` instead of `Notice`

### 2. Component Structure

```tsx
import React, { Suspense } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UserPlus, MessageSquare } from "lucide-react";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { GameMap } from "../../components/GameMap";
import { Notice } from "@/components/Notice.new";
import { useSelectedGameContext } from "../../context";
import { useGamesChannelsListSuspense } from "@/api/generated/endpoints";

const ChannelListScreen: React.FC = () => {
  // Implementation
};

const ChannelListScreenSuspense: React.FC = () => {
  return (
    <Suspense fallback={<div></div>}>
      <ChannelListScreen />
    </Suspense>
  );
};

export { ChannelListScreenSuspense as ChannelListScreen };
```

### 3. Channel List Item Component

Consider creating an internal `ChannelListItem` component for cleaner code:

```tsx
interface ChannelListItemProps {
  channel: Channel;
  onClick: () => void;
}

const ChannelListItem: React.FC<ChannelListItemProps> = ({ channel, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 hover:bg-muted border-b flex justify-between items-center"
    >
      <div>
        <div className="flex items-center gap-2">
          <span className="font-medium">{channel.name}</span>
          {!channel.private && (
            <Badge variant="outline">Public</Badge>
          )}
        </div>
        <p className="text-sm text-muted-foreground">
          {getLatestMessagePreview(channel.messages)}
        </p>
      </div>
    </button>
  );
};
```

### 4. Create Storybook File

Create `packages/web/src/screens/GameDetail/ChannelListScreen.new.stories.tsx`:

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { ChannelListScreen } from "./ChannelListScreen.new";
// Import mock handlers and data

const meta = {
  title: "Screens/GameDetail/ChannelListScreen",
  component: ChannelListScreen,
  parameters: {
    layout: "fullscreen",
    msw: {
      handlers: [
        // Mock game retrieve
        // Mock channels list
        // Mock variants list
      ],
    },
  },
} satisfies Meta<typeof ChannelListScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const WithChannels: Story = {};

export const NoChannels: Story = {
  parameters: {
    msw: {
      handlers: [
        // Return empty channels array
      ],
    },
  },
};

export const SandboxGame: Story = {
  parameters: {
    msw: {
      handlers: [
        // Return game with sandbox: true
      ],
    },
  },
};
```

## STOP: Manual Testing Required

After creating the new file:

1. Update the GameDetail index to use the new component temporarily
2. Start the dev server: `npm run dev`
3. Navigate to a game's chat screen (`/game/:gameId/chat`)
4. Verify:
   - Channel list displays correctly
   - "Create Channel" button works
   - Clicking a channel navigates to the channel screen
   - Empty state displays correctly
   - Sandbox game shows appropriate notice

## STOP: Storybook Testing

Run Storybook and verify all stories render correctly:

```bash
npm run storybook
```

## Completion Criteria

- [ ] `ChannelListScreen.new.tsx` created
- [ ] No MUI imports in the new file
- [ ] Suspense boundary implemented
- [ ] Storybook stories created and rendering
- [ ] Manual testing passes
- [ ] No TypeScript errors
