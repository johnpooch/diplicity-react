# Sandbox Game Channels and Members

## Overview

This document outlines how channels (chat) and member management work for sandbox games. The key principles are:
- **No channels in sandbox games**: Sandbox games are single-player practice environments with no chat
- **No joining/leaving sandbox games**: Sandbox games start immediately and cannot be joined by other players

## Key Principles

- **Explicit blocking**: Use permissions to block channel/member actions with clear error messages
- **Defensive design**: Game status naturally prevents join/leave, but permissions make it explicit
- **Consistent UX**: Frontend can hide channel/member UI for sandbox games

---

## Channel Views

### Design Decision: No Chat in Sandbox Games

**Rationale**:
- Sandbox games are single-player practice environments
- User controls all nations - no need for diplomacy/negotiation
- Simplifies implementation (no channel creation during game setup)
- Reduces complexity for the user

**Implementation**: Block all channel-related actions for sandbox games

---

### ChannelCreateView - Block for Sandbox Games

**Current implementation** ([channel/views.py:9-11](service/channel/views.py#L9-L11)):
```python
class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMember]
    serializer_class = ChannelSerializer
```

**Updated implementation**:
```python
class ChannelCreateView(SelectedGameMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsGameMember,
        IsNotSandboxGame,  # NEW: Block sandbox games
    ]
    serializer_class = ChannelSerializer
```

**Behavior**:
- Regular games: Users can create private channels for diplomacy
- Sandbox games: Returns 403 Forbidden with message "Cannot manually confirm phases in sandbox games."

---

### ChannelMessageCreateView - Block for Sandbox Games

**Current implementation** ([channel/views.py:14-16](service/channel/views.py#L14-L16)):
```python
class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame, IsGameMember, IsChannelMember]
    serializer_class = ChannelMessageSerializer
```

**Updated implementation**:
```python
class ChannelMessageCreateView(SelectedGameMixin, SelectedChannelMixin, CurrentGameMemberMixin, generics.CreateAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsActiveGame,
        IsGameMember,
        IsChannelMember,
        IsNotSandboxGame,  # NEW: Block sandbox games
    ]
    serializer_class = ChannelMessageSerializer
```

**Behavior**:
- Regular games: Users can send messages in channels
- Sandbox games: Returns 403 Forbidden

**Note**: In practice, this endpoint won't be called for sandbox games because:
1. No channels are created during sandbox game setup
2. `ChannelListView` returns empty array
3. Frontend won't show channel UI

However, adding the permission provides:
- **Defense in depth**: Explicit block if someone tries to use the API directly
- **Clear error message**: Better UX than "channel not found"

---

### ChannelListView - No Changes Needed

**Current implementation** ([channel/views.py:19-24](service/channel/views.py#L19-L24)):
```python
class ChannelListView(SelectedGameMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveGame]
    serializer_class = ChannelSerializer

    def get_queryset(self):
        return Channel.objects.accessible_to_user(self.request.user, self.get_game()).with_related_data()
```

**Behavior for sandbox games**:
- Returns empty array `[]` (no channels created)
- Frontend can check: `if (channels.length === 0) { hideChannelUI(); }`

**Conclusion**: ✅ No changes needed - naturally returns empty list

---

## Member Views

### Design Decision: No Joining/Leaving Sandbox Games

**Rationale**:
- Sandbox games start immediately with all nations assigned to creator
- Game status is never PENDING (goes straight to ACTIVE)
- Private by default (other users can't see them)
- Single-player by design

**Implementation**: Game status naturally prevents join/leave, but we can add explicit checks

---

### MemberCreateView (Join Game) - Already Blocked

**Current implementation** ([member/views.py:12-24](service/member/views.py#L12-L24)):
```python
class MemberCreateView(SelectedGameMixin, generics.CreateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingGame,  # Blocks ACTIVE games (including sandbox)
        IsNotGameMember,
        IsSpaceAvailable
    ]

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        member = serializer.save()
        if member.game.variant.nations.count() == member.game.members.count():
            member.game.start()
```

**Why it's already blocked**:
- `IsPendingGame` permission checks `game.status == GameStatus.PENDING`
- Sandbox games are created with `status = ACTIVE` (started immediately)
- Therefore, `IsPendingGame` returns False → 403 Forbidden

**Error message**: "Game is not in pending status."

**Conclusion**: ✅ No changes needed - already blocked by status check

---

### MemberDeleteView (Leave Game) - Already Blocked

**Current implementation** ([member/views.py:26-32](service/member/views.py#L26-L32)):
```python
class MemberDeleteView(SelectedGameMixin, generics.DestroyAPIView):
    serializer_class = EmptySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsPendingGame,  # Blocks ACTIVE games (including sandbox)
        IsGameMember
    ]

    def get_object(self):
        game = self.get_game()
        return get_object_or_404(Member, game=game, user=self.request.user)
```

**Why it's already blocked**:
- `IsPendingGame` permission checks `game.status == GameStatus.PENDING`
- Sandbox games have `status = ACTIVE`
- Therefore, `IsPendingGame` returns False → 403 Forbidden

**Error message**: "Game is not in pending status."

**Conclusion**: ✅ No changes needed - already blocked by status check

---

### Game Model Methods - No Changes Needed

**`can_join()` method** ([game/models.py:140-143](service/game/models.py#L140-L143)):
```python
def can_join(self, user):
    user_is_member = any(member.user.id == user.id for member in self.members.all())
    game_is_pending = self.status == GameStatus.PENDING
    return not user_is_member and game_is_pending
```

**For sandbox games**:
- `game_is_pending = False` (status is ACTIVE)
- Returns `False` ✅

**`can_leave()` method** ([game/models.py:145-148](service/game/models.py#L145-L148)):
```python
def can_leave(self, user):
    user_is_member = any(member.user.id == user.id for member in self.members.all())
    game_is_pending = self.status == GameStatus.PENDING
    return user_is_member and game_is_pending
```

**For sandbox games**:
- `game_is_pending = False` (status is ACTIVE)
- Returns `False` ✅

**Conclusion**: ✅ No changes needed - methods already return correct values

---

## Permission Summary

### Permissions to Add

**`IsNotSandboxGame`** - Already defined in `02_sandbox_game_phase_resolution.md`:
```python
# In common/permissions.py

class IsNotSandboxGame(BasePermission):
    message = "Cannot manually confirm phases in sandbox games."

    def has_permission(self, request, view):
        game = view.get_game()
        return not game.sandbox
```

**Usage**:
- `PhaseStateUpdateView` - Block manual phase confirmation
- `ChannelCreateView` - Block channel creation
- `ChannelMessageCreateView` - Block message sending

**Note**: We should update the error message to be more generic:
```python
class IsNotSandboxGame(BasePermission):
    message = "This action is not available for sandbox games."

    def has_permission(self, request, view):
        game = view.get_game()
        return not game.sandbox
```

### Permissions Already Working

**`IsPendingGame`** - Blocks ACTIVE games (including sandbox):
- Used by `MemberCreateView` (join)
- Used by `MemberDeleteView` (leave)

---

## Frontend Integration

### Hiding Channel UI for Sandbox Games

```typescript
// Fetch game details
const game = await fetch(`/game/${gameId}/`).then(res => res.json());

if (game.sandbox) {
  // Hide channel/chat UI entirely
  hideChannelNavigation();
  hideChannelList();
} else {
  // Show channel UI for regular games
  showChannelNavigation();
  fetchChannels();
}
```

### Hiding Join/Leave Buttons

```typescript
// Game details already include can_join and can_leave
const game = await fetch(`/game/${gameId}/`).then(res => res.json());

if (game.canJoin) {
  showJoinButton();
} else {
  hideJoinButton();
}

if (game.canLeave) {
  showLeaveButton();
} else {
  hideLeaveButton();
}

// For sandbox games:
// - canJoin = false (status is ACTIVE)
// - canLeave = false (status is ACTIVE)
// Both buttons will be hidden automatically
```

---

## Testing Strategy

### Channel View Tests

**ChannelCreateView** (`channel/tests/test_channel_create.py`):
- [ ] Test regular game: User can create channel
- [ ] Test sandbox game: Returns 403 Forbidden
- [ ] Test sandbox game: Error message is clear
- [ ] Test permissions: Unauthenticated user cannot create (401)
- [ ] Test permissions: Non-member cannot create (403)

**ChannelMessageCreateView** (`channel/tests/test_channel_message_create.py`):
- [ ] Test regular game: User can send message
- [ ] Test sandbox game: Returns 403 Forbidden
- [ ] Test sandbox game: Error message is clear
- [ ] Test permissions: Unauthenticated user cannot send (401)
- [ ] Test permissions: Non-member cannot send (403)
- [ ] Test permissions: Non-channel-member cannot send (403)

**ChannelListView** (`channel/tests/test_channel_list.py`):
- [ ] Test regular game: Returns channels for game
- [ ] Test sandbox game: Returns empty array
- [ ] Test sandbox game with no channels created during setup

### Member View Tests

**MemberCreateView** (`member/tests/test_member_create.py`):
- [ ] Test pending regular game: User can join
- [ ] Test active regular game: Returns 403 (game started)
- [ ] Test sandbox game: Returns 403 (status is ACTIVE)
- [ ] Test sandbox game: Error message indicates game not pending
- [ ] Test permissions: Already a member cannot join (403)
- [ ] Test permissions: No space available cannot join (403)

**MemberDeleteView** (`member/tests/test_member_delete.py`):
- [ ] Test pending regular game: User can leave
- [ ] Test active regular game: Returns 403 (game started)
- [ ] Test sandbox game: Returns 403 (status is ACTIVE)
- [ ] Test sandbox game: Error message indicates game not pending
- [ ] Test permissions: Non-member cannot leave (404)

### Game Model Method Tests

**can_join() method** (`game/tests/test_game_model.py`):
- [ ] Test pending regular game: Returns True for non-member
- [ ] Test pending regular game: Returns False for existing member
- [ ] Test active regular game: Returns False (status not pending)
- [ ] Test sandbox game: Returns False (status is ACTIVE)

**can_leave() method** (`game/tests/test_game_model.py`):
- [ ] Test pending regular game: Returns True for member
- [ ] Test pending regular game: Returns False for non-member
- [ ] Test active regular game: Returns False (status not pending)
- [ ] Test sandbox game: Returns False (status is ACTIVE)

### Integration Tests

**Sandbox Game Isolation** (`integration/tests.py`):
- [ ] Test complete sandbox game lifecycle:
  1. Create sandbox game
  2. Verify no channels created
  3. Attempt to create channel → 403
  4. Attempt to send message → 403
  5. Fetch channel list → empty array
  6. Attempt to join game → 403
  7. Attempt to leave game → 403
  8. Verify game is private and not visible to other users

**Regular Game Flow** (`integration/tests.py`):
- [ ] Test regular game still works correctly:
  1. Create regular game (PENDING)
  2. Second user joins
  3. Game starts (ACTIVE)
  4. Public press channel exists
  5. Users can create private channels
  6. Users can send messages
  7. Cannot join after game starts
  8. Cannot leave after game starts

---

## Implementation Checklist

### Channel Views
- [ ] Add `IsNotSandboxGame` permission to `ChannelCreateView`
- [ ] Add `IsNotSandboxGame` permission to `ChannelMessageCreateView`
- [ ] Update `IsNotSandboxGame` error message to be more generic
- [ ] Verify `ChannelListView` returns empty array for sandbox games
- [ ] Write tests for channel views with sandbox games

### Member Views
- [ ] Verify `MemberCreateView` blocks sandbox games (via `IsPendingGame`)
- [ ] Verify `MemberDeleteView` blocks sandbox games (via `IsPendingGame`)
- [ ] Write tests for member views with sandbox games
- [ ] Write tests for `can_join()` and `can_leave()` with sandbox games

### Frontend
- [ ] Hide channel UI when `game.sandbox === true`
- [ ] Join/leave buttons already hidden (based on `canJoin`/`canLeave`)
- [ ] Test UI correctly hides elements for sandbox games

---

## API Examples

### Attempt to Create Channel in Sandbox Game

**Request**: `POST /games/{sandbox_game_id}/channels/create/`
```json
{
  "name": "France-Germany Alliance",
  "private": true,
  "memberIds": ["member-france", "member-germany"]
}
```

**Response**: `403 Forbidden`
```json
{
  "detail": "This action is not available for sandbox games."
}
```

### List Channels in Sandbox Game

**Request**: `GET /games/{sandbox_game_id}/channels/`

**Response**: `200 OK`
```json
[]
```

### Attempt to Join Sandbox Game

**Request**: `POST /game/{sandbox_game_id}/join/`

**Response**: `403 Forbidden`
```json
{
  "detail": "Game is not in pending status."
}
```

### Get Sandbox Game Details

**Request**: `GET /game/{sandbox_game_id}/`

**Response**: Shows `canJoin: false` and `canLeave: false`
```json
{
  "id": "my-sandbox-game",
  "name": "My Sandbox Game",
  "status": "ACTIVE",
  "sandbox": true,
  "private": true,
  "canJoin": false,
  "canLeave": false,
  "members": [
    {
      "user": {"username": "alice"},
      "nation": {"id": "england", "name": "England"}
    },
    {
      "user": {"username": "alice"},
      "nation": {"id": "france", "name": "France"}
    }
    // ... 5 more members, all belonging to alice
  ],
  "phases": [...]
}
```

---

## Notes

- **Defense in depth**: Channel views blocked by permission even though no channels exist
- **Natural blocking**: Member views blocked by game status (PENDING check)
- **Clean separation**: Frontend can easily detect sandbox games and hide inappropriate UI
- **Consistent UX**: Clear error messages if API is called inappropriately
- **No special cases**: Existing permissions and status checks handle most logic
- **Private by default**: Sandbox games are private, so other users can't see them anyway
