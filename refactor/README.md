# Frontend Refactoring Plan

This folder contains step-by-step prompts for completing the frontend migration from Material UI to shadcn/ui + Tailwind CSS.

## Guiding Principles

1. **1:1 Functional Parity** - Each migrated screen should behave exactly the same as before
2. **No UX Changes** - Don't "improve" things while migrating
3. **No Scope Creep** - Stick to the task at hand
4. **Test Before Moving On** - Manual testing after each screen
5. **Clean Up After** - Delete old files only after new ones are verified

## Execution Order

Complete these in order. Each document is a prompt for Claude Code.

| # | File | Status | Description |
|---|------|--------|-------------|
| 1 | [01_WIRE_UP_HOME_SCREENS.md](./01_WIRE_UP_HOME_SCREENS.md) | TODO | Connect existing .new.tsx home screens to router |
| 2 | [02_REFACTOR_ORDERS_SCREEN.md](./02_REFACTOR_ORDERS_SCREEN.md) | TODO | Refactor OrdersScreen + consolidate sub-components |
| 3 | [03_REFACTOR_CHANNEL_LIST_SCREEN.md](./03_REFACTOR_CHANNEL_LIST_SCREEN.md) | TODO | Refactor ChannelListScreen |
| 4 | [04_REFACTOR_CHANNEL_CREATE_SCREEN.md](./04_REFACTOR_CHANNEL_CREATE_SCREEN.md) | TODO | Refactor ChannelCreateScreen |
| 5 | [05_REFACTOR_CHANNEL_SCREEN.md](./05_REFACTOR_CHANNEL_SCREEN.md) | TODO | Refactor ChannelScreen (chat view) |
| 6 | [06_REFACTOR_MAP_SCREEN.md](./06_REFACTOR_MAP_SCREEN.md) | TODO | Refactor MapScreen |

## Reference

- [FRONTEND_REFACTORING_APPROACH.md](./FRONTEND_REFACTORING_APPROACH.md) - Overall refactoring patterns and goals

## How to Use These Documents

1. Open the document in order
2. Copy the contents as a prompt to Claude Code
3. Let Claude Code execute the refactoring
4. **STOP** at the manual testing checkpoints
5. Verify everything works before proceeding
6. Update the status in this README when complete

## After All Screens Are Done

Once all screens are migrated:

1. **Remove MUI dependencies** from package.json:
   - `@mui/material`
   - `@mui/icons-material`
   - `@emotion/react`
   - `@emotion/styled`

2. **Delete unused utilities**:
   - `components/utils/styles.ts` (createUseStyles)
   - `components/utils/responsive.ts` (useResponsiveness) - if no longer needed

3. **Run full test suite** and fix any issues

4. **Verify bundle size** has decreased

## Tips for Success

- Don't try to do multiple screens at once
- If you find a shared component needs refactoring, do it as part of the current screen
- Keep notes of any issues you encounter
- If stuck, move to the next screen and come back
