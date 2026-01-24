# Debug: ChannelScreen Message Layout Issues

## Problem Summary

I have a chat screen component with two layout issues that aren't working:

1. **Messages from the current user should appear on the right side of the screen** - I'm trying to use `flex-row-reverse` on the Message component when `item.isCurrentUser` is true, but it's not reversing the layout.

2. **The timestamp should appear on the right side within the message bubble** - I have `text-right block` on the MessageTimestamp but it's not aligning to the right.

## Files to Examine

- `packages/web/src/screens/GameDetail/ChannelScreen.new.tsx` - The screen component using the Message components
- `packages/web/src/components/ui/message.tsx` - The Message component definitions
- `packages/web/src/screens/GameDetail/ChannelScreen.new.stories.tsx` - Storybook stories with mock data (check if `isCurrentUser` is set correctly in the mock data)

## Expected Behavior

- When `item.isCurrentUser` is true, the entire message row should be reversed (avatar on right, bubble on left of avatar)
- The timestamp inside the message bubble should be right-aligned at the bottom of the bubble

## Investigation Checklist

1. Is `flex-row-reverse` being applied correctly to the Message component?
2. Is the mock data in stories correctly setting `isCurrentUser: true` for some messages?
3. Why isn't `text-right block` working on the MessageTimestamp?
4. Check if there are any CSS conflicts or missing styles preventing these from working

## How to Debug

Run Storybook to visually debug:
```bash
cd packages/web && npm run storybook
```

Then navigate to the ChannelScreen stories.

## Current Implementation

### Message Component (`message.tsx`)

```tsx
const Message = ({ children, className, ...props }: MessageProps) => (
  <div className={cn("flex gap-3", className)} {...props}>
    {children}
  </div>
);
```

### Usage in ChannelScreen

```tsx
<Message
  key={item.id}
  className={item.isCurrentUser ? "flex-row-reverse" : undefined}
>
  {/* avatar */}
  <MessageContent>
    <span className="text-sm font-medium block">{item.sender.nationName}</span>
    <span>{item.body}</span>
    <MessageTimestamp className="text-[10px] block text-right mt-1">
      {item.formattedTime}
    </MessageTimestamp>
  </MessageContent>
</Message>
```

## Questions to Answer

1. Is the `cn()` utility merging classes correctly?
2. Does the parent container have any styles that override flex-direction?
3. Is MessageTimestamp's parent (MessageContent) constraining its width?
