# 04: Refactor Channel Create Screen

## Context

Refactor the Channel Create Screen following the patterns documented in `FRONTEND_REFACTORING_APPROACH.md`.

**Important constraints:**
- Keep the `GameDetailLayout` component mostly unchanged for now
- Do NOT change the overall screen structure or UX
- Achieve 1:1 functional parity with the existing implementation

## Files to Refactor

**Main file:**
- `packages/web/src/screens/GameDetail/ChannelCreateScreen.tsx`

## Current Implementation Analysis

The current `ChannelCreateScreen.tsx`:
- Uses MUI components: `Avatar`, `Button`, `Checkbox`, `Divider`, `List`, `ListItem`, `ListItemAvatar`, `ListItemButton`, `ListItemText`, `Stack`
- Uses `createUseStyles` for styling
- Uses `Panel` component for layout structure
- Uses `GameDetailLayout` wrapper
- Uses `Icon` component for icons
- Uses RTK Query for data fetching and mutation
- Manages selected members state with `useState`

## Refactoring Requirements

### 1. Create `ChannelCreateScreen.new.tsx`

Create a new file at `packages/web/src/screens/GameDetail/ChannelCreateScreen.new.tsx` that:

1. **Replaces MUI components** with shadcn/ui + Tailwind:
   - `Stack` → `div` with Tailwind flex classes
   - `Button` → `@/components/ui/button`
   - `Checkbox` → `@/components/ui/checkbox`
   - `Avatar` → `@/components/ui/avatar`
   - `List`, `ListItem`, `ListItemButton`, `ListItemText`, `ListItemAvatar` → simple divs with click handlers
   - `Divider` → `<hr>` or border classes

2. **Updates data fetching** to use the new React Query hooks with Suspense:
   - Game data should come from context (already uses `useSelectedGameContext`)
   - Replace mutation with generated hook from `@/api/generated/endpoints`
   - Export a `ChannelCreateScreenSuspense` component

3. **Replaces Icon usage** with Lucide React:
   - `IconName.GroupAdd` → `UserPlus` from Lucide

4. **Keeps the GameDetailLayout usage** - don't refactor the layout itself

### 2. Component Structure

```tsx
import React, { Suspense, useState } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { UserPlus } from "lucide-react";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { GameMap } from "../../components/GameMap";
import { useSelectedGameContext } from "../../context";
import { useGamesChannelsCreateCreate } from "@/api/generated/endpoints";

const ChannelCreateScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();
  const navigate = useNavigate();
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

  const createChannelMutation = useGamesChannelsCreateCreate();

  // ... rest of implementation
};

const ChannelCreateScreenSuspense: React.FC = () => {
  return (
    <Suspense fallback={<div></div>}>
      <ChannelCreateScreen />
    </Suspense>
  );
};

export { ChannelCreateScreenSuspense as ChannelCreateScreen };
```

### 3. Member Selection List Item

Create an internal component for the member selection item:

```tsx
interface MemberSelectionItemProps {
  member: Member;
  isSelected: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

const MemberSelectionItem: React.FC<MemberSelectionItemProps> = ({
  member,
  isSelected,
  onToggle,
  disabled,
}) => {
  return (
    <button
      onClick={onToggle}
      disabled={disabled}
      className="w-full flex items-center gap-4 p-4 hover:bg-muted border-b"
    >
      <Avatar>
        <AvatarImage src={member.picture ?? undefined} />
        <AvatarFallback>{member.nation?.[0]}</AvatarFallback>
      </Avatar>
      <div className="flex-1 text-left">
        <p className="font-medium">{member.nation}</p>
        <p className="text-sm text-muted-foreground">{member.name}</p>
      </div>
      <Checkbox checked={isSelected} disabled={disabled} />
    </button>
  );
};
```

### 4. Create Storybook File

Create `packages/web/src/screens/GameDetail/ChannelCreateScreen.new.stories.tsx`:

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { ChannelCreateScreen } from "./ChannelCreateScreen.new";
// Import mock handlers and data

const meta = {
  title: "Screens/GameDetail/ChannelCreateScreen",
  component: ChannelCreateScreen,
  parameters: {
    layout: "fullscreen",
    msw: {
      handlers: [
        // Mock game retrieve with members
        // Mock variants list
        // Mock channel create mutation
      ],
    },
  },
} satisfies Meta<typeof ChannelCreateScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithMembersSelected: Story = {
  // Could use play function to select members
};
```

## STOP: Manual Testing Required

After creating the new file:

1. Update the GameDetail index to use the new component temporarily
2. Start the dev server: `npm run dev`
3. Navigate to channel create screen (`/game/:gameId/chat/channel/create`)
4. Verify:
   - Member list displays correctly (excluding current user)
   - Checkbox selection works
   - "Select Members" button is disabled when no members selected
   - Creating a channel works and navigates to the new channel

## STOP: Storybook Testing

Run Storybook and verify all stories render correctly:

```bash
npm run storybook
```

## Completion Criteria

- [ ] `ChannelCreateScreen.new.tsx` created
- [ ] No MUI imports in the new file
- [ ] Suspense boundary implemented
- [ ] Storybook stories created and rendering
- [ ] Manual testing passes
- [ ] No TypeScript errors
