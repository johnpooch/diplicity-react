# Feature: Private Game Creation

**Date:** 2025-09-29
**Session:** Private games implementation with visibility controls

## Summary
Implemented private game creation functionality allowing users to create games that are only accessible via direct links and excluded from public game listings.

## Problem Solved
Users needed the ability to create private games for playing with friends without having those games appear in public browse listings. This enables more intimate gaming sessions while maintaining the existing public game discovery system.

## Implementation Details

### Backend Changes
- **Modified:** `service/game/serializers.py` - Added `private` field to GameSerializer for API read/write operations
- **Modified:** `service/game/filters.py` - Updated GameFilter to exclude private games from `can_join` listings while preserving access in `mine` listings
- **Modified:** `service/game/tests.py` - Added comprehensive test suite for private game creation, filtering, and access patterns
- **Generated:** Updated TypeScript API client types to include private field in GameRead/GameWrite interfaces

### Frontend Changes
- **Modified:** `packages/web/src/screens/Home/CreateGame.tsx` - Added private checkbox with descriptive help text
- **Modified:** `packages/web/src/screens/Home/GameInfo.tsx` - Added "Visibility" field showing Private/Public status
- **Modified:** `packages/web/src/screens/GameDetail/GameInfoScreen.tsx` - Added matching visibility indicator
- **Modified:** `packages/web/src/components/GameCard.tsx` - Added subtle lock icon for private games
- **Modified:** `packages/web/src/components/Icon.tsx` - Added Lock icon to icon system

### Database Schema
- Leveraged existing `private` boolean field in Game model (no migration required)

## Rationale

**Filtering Approach:** Private games are excluded only from `can_join=true` queries (public browsing) but remain visible in `mine=true` queries (user's own games). This ensures:
- Private games don't appear in public listings
- Users can still manage their own private games
- Direct links work for all users (no additional access restrictions)

**UI Design Decisions:**
- Checkbox defaults to unchecked (public by default) to maintain current user expectations
- Lock icon placement before game name for immediate visibility
- Consistent "Visibility" field placement across game info screens
- Subtle visual treatment (small icon, reduced opacity) to avoid UI clutter

**Security Model:** Link-only access (no additional permissions) was chosen for simplicity and to match the requirement of "anyone with the link" access.

## Testing
- **Backend:** 5 comprehensive tests covering private game creation, public listing exclusion, mine listing inclusion, and direct access
- **Build:** Frontend TypeScript compilation verified with new private field integration
- **API Integration:** Verified API client regeneration includes private field in request/response types

## Notes
- The `private` field existed in the Django model from initial migration, suggesting this feature was planned from the beginning
- No additional authentication/authorization logic needed beyond existing game access patterns
- Lock icon uses Material UI's standard Lock icon for consistency with design system
- Private game functionality is fully backward compatible with existing public games