# 05: Refactor Channel Screen (Chat)

## Context

Refactor the Channel Screen (individual chat view) following the patterns documented in `FRONTEND_REFACTORING_APPROACH.md`.

**Important constraints:**
- Keep the `GameDetailLayout` component mostly unchanged for now
- Do NOT change the overall screen structure or UX
- Achieve 1:1 functional parity with the existing implementation

## Files to Refactor

**Main file:**
- `packages/web/src/screens/GameDetail/ChannelScreen.tsx`

**Related component:**
- `packages/web/src/components/ChannelMessage.tsx` (may need refactoring)

## Current Implementation Analysis

The current `ChannelScreen.tsx`:
- Uses MUI components: `Box`, `List`, `Stack`, `TextField`, `IconButton`, `Typography`, `Divider`
- Uses MUI icon: `Send as SendIcon`
- Uses `createUseStyles` for styling
- Uses `Panel` component for layout structure
- Uses `GameDetailLayout` wrapper
- Uses `Icon` component for icons
- Uses RTK Query for data fetching and mutation
- Uses `useRef` and `useEffect` for auto-scrolling to bottom
- Manages message input state with `useState`
- Uses `ChannelMessage` component for rendering messages

## Refactoring Requirements

### 1. Create `ChannelScreen.new.tsx`

Create a new file at `packages/web/src/screens/GameDetail/ChannelScreen.new.tsx` that:

1. **Replaces MUI components** with shadcn/ui + Tailwind:
   - `Stack` → `div` with Tailwind flex classes
   - `Box` → `div`
   - `TextField` → `@/components/ui/input`
   - `IconButton` → `@/components/ui/button` with icon
   - `Typography` → heading/paragraph tags with Tailwind
   - `List` → simple div container
   - `Divider` → `<hr>` or border classes

2. **Replaces MUI icons** with Lucide React:
   - `Send` → `Send` from Lucide
   - `IconName.Chat` → `MessageSquare` from Lucide

3. **Updates data fetching** to use the new React Query hooks with Suspense:
   - Replace `service.endpoints.gamesChannelsList.useQuery()` with generated hook
   - Replace `service.endpoints.variantsList.useQuery()` with generated hook
   - Replace mutation with generated hook
   - Export a `ChannelScreenSuspense` component

4. **Keeps the GameDetailLayout usage** - don't refactor the layout itself

5. **Updates related component imports:**
   - Use `@/components/ChannelMessage.new` if it exists, or refactor inline
   - Use `@/components/Notice.new` for empty state

### 2. Component Structure

```tsx
import React, { Suspense, useState, useRef, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, MessageSquare } from "lucide-react";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { GameMap } from "../../components/GameMap";
import { Notice } from "@/components/Notice.new";
import { ChannelMessage } from "@/components/ChannelMessage.new";
import { useSelectedGameContext } from "../../context";
import {
  useGamesChannelsListSuspense,
  useVariantsListSuspense,
  useGamesChannelsMessagesCreateCreate,
} from "@/api/generated/endpoints";

const ChannelScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();
  const { channelId } = useParams<{ channelId: string }>();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  // ... implementation
};

const ChannelScreenSuspense: React.FC = () => {
  return (
    <Suspense fallback={<div></div>}>
      <ChannelScreen />
    </Suspense>
  );
};

export { ChannelScreenSuspense as ChannelScreen };
```

### 3. Message Input Component

Consider extracting the message input as an internal component:

```tsx
interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSubmit,
  disabled,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="flex gap-2 p-4 border-t">
      <Input
        placeholder="Type a message"
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className="flex-1"
      />
      <Button
        onClick={onSubmit}
        disabled={!value.trim() || disabled}
        size="icon"
      >
        <Send className="size-4" />
      </Button>
    </div>
  );
};
```

### 4. Check/Create ChannelMessage.new.tsx

If `ChannelMessage.new.tsx` doesn't exist, create it or refactor the message rendering inline. The component should:
- Display sender avatar with nation color
- Show message body
- Show timestamp
- Handle "show avatar" logic for grouped messages from same sender

### 5. Create Storybook File

Create `packages/web/src/screens/GameDetail/ChannelScreen.new.stories.tsx`:

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { ChannelScreen } from "./ChannelScreen.new";
// Import mock handlers and data

const meta = {
  title: "Screens/GameDetail/ChannelScreen",
  component: ChannelScreen,
  parameters: {
    layout: "fullscreen",
    router: {
      path: "/game/:gameId/chat/channel/:channelId",
      initialEntries: ["/game/123/chat/channel/1"],
    },
    msw: {
      handlers: [
        // Mock game retrieve
        // Mock channels list with messages
        // Mock variants list
        // Mock message create mutation
      ],
    },
  },
} satisfies Meta<typeof ChannelScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const WithMessages: Story = {};

export const NoMessages: Story = {
  parameters: {
    msw: {
      handlers: [
        // Return channel with empty messages array
      ],
    },
  },
};
```

## STOP: Manual Testing Required

After creating the new file:

1. Update the GameDetail index to use the new component temporarily
2. Start the dev server: `npm run dev`
3. Navigate to a channel screen (`/game/:gameId/chat/channel/:channelId`)
4. Verify:
   - Messages display correctly with avatars
   - Auto-scroll to bottom works
   - Message input works
   - Sending a message works and clears input
   - Empty state displays correctly
   - Back navigation works

## STOP: Storybook Testing

Run Storybook and verify all stories render correctly:

```bash
npm run storybook
```

## Completion Criteria

- [ ] `ChannelScreen.new.tsx` created
- [ ] `ChannelMessage.new.tsx` created/verified
- [ ] No MUI imports in the new files
- [ ] Suspense boundary implemented
- [ ] Auto-scroll functionality works
- [ ] Storybook stories created and rendering
- [ ] Manual testing passes
- [ ] No TypeScript errors
