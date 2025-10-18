# Sandbox Mode Implementation - Getting Started

## Context

This repository contains a full-stack Diplomacy game application with:
- **Backend**: Django REST Framework API
- **Frontend**: React + TypeScript with Material-UI
- **Architecture**: Monorepo with Docker services

I want to implement a **Sandbox Mode** feature that allows users to practice Diplomacy by controlling all nations in a single-player game.

## Complete Design Documentation

The feature has been fully designed and documented across 6 comprehensive documents:

1. **01_sandbox_game_creation.md** - How sandbox games are created on the backend
2. **02_sandbox_game_phase_resolution.md** - How phases are resolved in sandbox games
3. **03_sandbox_game_phase_states.md** - How phase states work with multiple nations per user
4. **04_sandbox_game_orders.md** - How order creation works for multiple nations
5. **05_sandbox_game_channels_and_members.md** - How channels and member management work
6. **06_frontend_sandbox_implementation.md** - All frontend changes needed

**Please read all 6 documents thoroughly before starting implementation.** They contain:
- Complete technical specifications
- Code examples
- API contracts
- Testing strategies
- Implementation checklists

## High-Level Summary

### What is Sandbox Mode?

A single-player practice mode where:
- User controls ALL nations (Britain, France, Germany, Italy, Austria, Turkey, Russia)
- No time limits - user resolves phases manually when ready
- No chat functionality (single player)
- Private games (not visible to other users)
- Perfect for learning mechanics and testing strategies

### Key Design Decisions

**Backend Design**:
- Add `sandbox` boolean field to Game model
- Create multiple Member instances (one per nation) all with same user
- Allow `movement_phase_duration = None` for infinite duration
- Convert `PhaseStateRetrieveView` → `PhaseStateListView` (returns array)
- Update `Order.objects.create_from_selected()` to find correct phase_state by checking orderable provinces
- Add permissions to block inappropriate actions (chat, manual confirmation)

**Frontend Design**:
- Add "Sandbox" tab to MyGames screen
- Split CreateGame into "Standard" and "Sandbox" tabs
- Show "Resolve Phase" button instead of "Confirm Orders" for sandbox games
- Hide member avatars and chat UI for sandbox games
- Group orders by nation with subheaders in sandbox games
- Order creation works exactly the same (map interaction)

## Implementation Request

Please implement the Sandbox Mode feature following these steps:

### Phase 1: Backend Implementation

**Order of implementation** (follow checklists in documents):

1. **Database & Models** (Document 01)
   - Add `sandbox` field to Game model
   - Update `movement_phase_duration` to allow `None`
   - Update `Game.movement_phase_duration_seconds` property
   - Update `Game.start()` method
   - Create migration

2. **Game Creation** (Document 01)
   - Refactor `Game.objects.create_from_template()` to remove member/channel creation
   - Update `GameSerializer.create()` to handle member/channel creation
   - Create `SandboxGameSerializer`
   - Create `CreateSandboxGameView`
   - Update `GameListView` filtering
   - Add URL route

3. **Phase Resolution** (Document 02)
   - Add `IsSandboxGame` permission
   - Add `IsNotSandboxGame` permission
   - Update `PhaseStateUpdateView` to block sandbox games
   - Rename `PhaseResolveView` → `PhaseResolveAllView`
   - Create new `PhaseResolveView` for sandbox games
   - Add `Phase.objects.resolve_phase()` method
   - Update `Phase.objects.resolve_due_phases()`
   - Add URL route

4. **Phase States** (Document 03)
   - Update `CurrentGameMemberMixin` to use `.filter().first()`
   - Convert `PhaseStateRetrieveView` → `PhaseStateListView`
   - Update URL from `/phase-state/` to `/phase-states/`

5. **Orders** (Document 04)
   - Update `Order.objects.create_from_selected()` to find phase_state by orderable provinces
   - Verify other order views work correctly

6. **Channels & Members** (Document 05)
   - Add `IsNotSandboxGame` permission to channel views
   - Verify member views are blocked by existing permissions

7. **Testing**
   - Write comprehensive tests following test strategies in each document
   - Ensure all existing tests still pass

### Phase 2: Frontend Implementation

**After backend is complete and codegen is run:**

1. **Run Codegen** (Document 06)
   ```bash
   docker compose up codegen
   ```

2. **Implement Components** (follow Document 06):
   - MyGames: Add Sandbox tab
   - CreateGame: Split into Standard/Sandbox tabs
   - GameCard: Hide avatars for sandbox
   - GameInfo/GameInfoScreen: Hide member sections
   - ActivePhaseOrders: Conditional rendering (resolve vs confirm button)
   - ActivePhaseOrders: Group orders by nation for sandbox
   - Phase timer: Show "Resolve when ready"
   - ChannelListScreen: Show alert for sandbox games
   - Hide channel UI elements

3. **Testing**
   - Component tests
   - Integration tests
   - Manual QA

## Important Notes

### Follow the Design Documents

- **Do NOT deviate from the documented design** without discussing first
- The documents contain complete specifications - follow them exactly
- All edge cases and considerations have been thought through
- Testing strategies are comprehensive - implement all tests

### Code Style

- Follow existing patterns in CLAUDE.md
- Backend: No docstrings or comments (per style guide)
- Backend: Use base `Serializer` class, not `ModelSerializer`
- Backend: Views should be simple, leverage DRF generics
- Frontend: Use existing component patterns and Material-UI theme

### Testing Requirements

- **Minimum 90% coverage** for all new code
- **100% coverage** for critical paths (game creation, order creation)
- All existing tests must continue to pass
- Follow pytest patterns in conftest.py

### Development Workflow

1. Read all 6 documents thoroughly
2. Implement backend first (Phase 1)
3. Run all backend tests - ensure they pass
4. Run codegen to update frontend types
5. Implement frontend (Phase 2)
6. Run all frontend tests
7. Manual QA of complete feature

## Questions to Ask Before Starting

Before beginning implementation, please confirm:

1. Have you read all 6 documentation files?
2. Do you understand the overall architecture (multiple members per user)?
3. Do you understand why orderable provinces are mutually exclusive?
4. Are you clear on which views need changes vs which work as-is?
5. Do you have any questions about the design before starting?

## Getting Help

If you encounter issues or need clarification:

1. **Re-read the relevant documentation** - it's very comprehensive
2. **Check existing code patterns** - follow established conventions
3. **Ask specific questions** - reference document sections when asking

## Success Criteria

The feature is complete when:

1. ✅ All backend tests pass (including new sandbox tests)
2. ✅ All frontend tests pass (including new sandbox tests)
3. ✅ User can create sandbox game via UI
4. ✅ User can place orders for all nations in sandbox game
5. ✅ User can resolve phases manually in sandbox game
6. ✅ Sandbox games appear in dedicated tab
7. ✅ Chat and inappropriate UI elements are hidden for sandbox games
8. ✅ All existing functionality for regular games still works
9. ✅ Code follows project style guidelines
10. ✅ Documentation is updated (if needed)

## Ready to Start?

Please confirm you've read all documentation files and are ready to begin implementation. Start with Phase 1 (backend), and let me know if you have any questions about the design before proceeding.

Good luck! The design is solid and comprehensive - follow the documents closely and you'll build an excellent feature.
