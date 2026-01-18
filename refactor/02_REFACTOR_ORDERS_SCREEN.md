# 02: Refactor Orders Screen

## Context

Refactor the Orders Screen following the patterns documented in `FRONTEND_REFACTORING_APPROACH.md`.

**Important constraints:**
- Keep the `GameDetailLayout` component mostly unchanged for now - just replace MUI components with simple divs/Tailwind where needed
- Do NOT change the overall screen structure or UX
- Create a single consolidated file instead of separate files for ActivePhaseOrders and InactivePhaseOrders
- Achieve 1:1 functional parity with the existing implementation

## Files to Refactor

**Main file:**
- `packages/web/src/screens/GameDetail/OrdersScreen.tsx`

**Related files to consolidate into OrdersScreen.new.tsx:**
- `packages/web/src/screens/GameDetail/ActivePhaseOrders.tsx`
- `packages/web/src/screens/GameDetail/InactivePhaseOrders.tsx`

## Refactoring Requirements

### 1. Create `OrdersScreen.new.tsx`

Create a new file at `packages/web/src/screens/GameDetail/OrdersScreen.new.tsx` that:

1. **Consolidates** ActivePhaseOrders and InactivePhaseOrders as internal components within the same file (similar to how CreateGame.new.tsx has CreateStandardGameForm and CreateSandboxGameForm in the same file)

2. **Replaces MUI components** with shadcn/ui + Tailwind:
   - `Stack` → `div` with Tailwind flex classes
   - `Button` → `@/components/ui/button`
   - `List`, `ListSubheader` → simple divs with appropriate styling
   - `Divider` → `<hr>` or border classes
   - `Icon` → Lucide React icons

3. **Updates data fetching** to use the new React Query hooks with Suspense:
   - Replace `service.endpoints.*.useQuery()` with generated hooks from `@/api/generated/endpoints`
   - Wrap the component in Suspense boundary
   - Export a `OrdersScreenSuspense` component (similar to other `.new.tsx` files)

4. **Keeps the GameDetailLayout usage** - don't refactor the layout itself yet, just use it as-is

5. **Updates related component imports:**
   - Use `@/components/Notice.new` instead of `Notice`
   - Use `@/components/OrderCard.new` if it exists, or note that it needs refactoring
   - Use Lucide icons instead of `Icon` component

### 2. Component Structure

```tsx
// Internal components (not exported)
interface ActivePhaseOrdersProps { ... }
const ActivePhaseOrders: React.FC<ActivePhaseOrdersProps> = () => { ... }

interface InactivePhaseOrdersProps { ... }
const InactivePhaseOrders: React.FC<InactivePhaseOrdersProps> = () => { ... }

// Main component
const OrdersScreen: React.FC = () => { ... }

// Suspense wrapper (exported)
const OrdersScreenSuspense: React.FC = () => {
  return (
    <Suspense fallback={<div></div>}>
      <OrdersScreen />
    </Suspense>
  );
};

export { OrdersScreenSuspense as OrdersScreen };
```

### 3. Create Storybook File

Create `packages/web/src/screens/GameDetail/OrdersScreen.new.stories.tsx` following the existing patterns:

```tsx
import type { Meta, StoryObj } from "@storybook/react";
import { OrdersScreen } from "./OrdersScreen.new";
// Import mock handlers from @/api/generated/endpoints
// Import mock data from @/mocks

const meta = {
  title: "Screens/GameDetail/OrdersScreen",
  component: OrdersScreen,
  parameters: {
    layout: "fullscreen",
    msw: {
      handlers: [
        // Add appropriate mock handlers
      ],
    },
  },
} satisfies Meta<typeof OrdersScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ActivePhase: Story = {};
export const InactivePhase: Story = {};
export const NoOrdersRequired: Story = {};
```

## Dependencies Check

Before starting, verify these components exist in their `.new.tsx` versions:
- [ ] `Notice.new.tsx`
- [ ] `OrderCard.new.tsx` (may need to be created)
- [ ] `MemberAvatar.new.tsx` (may need to be created)
- [ ] `Panel.new.tsx` or equivalent (may need simple div replacement)

If any dependency is missing, create a minimal version or use simple div placeholders.

## STOP: Manual Testing Required

After creating the new file:

1. Update the GameDetail index to use the new component temporarily for testing
2. Start the dev server: `npm run dev`
3. Navigate to a game's orders screen
4. Test both active and inactive phase states
5. Verify all functionality works:
   - Orders display correctly
   - Delete order button works
   - Confirm orders button works
   - Resolve phase button works (for sandbox games)

## STOP: Storybook Testing

Run Storybook and verify all stories render correctly:

```bash
npm run storybook
```

## Completion Criteria

- [ ] `OrdersScreen.new.tsx` created with consolidated components
- [ ] No MUI imports in the new file
- [ ] Suspense boundary implemented
- [ ] Storybook stories created and rendering
- [ ] Manual testing passes
- [ ] No TypeScript errors
