# Frontend Sandbox Implementation

## Overview

This document outlines all frontend changes needed to support sandbox mode. The key principle is to provide a clear, intuitive UX that distinguishes sandbox games while keeping the UI familiar and consistent with regular games.

## Key Principles

- **Clear separation**: Sandbox games appear in dedicated tab, not mixed with regular games
- **Simplified creation**: Sandbox creation form only requires name and variant
- **Consistent interaction**: Order creation works the same as regular games (map interaction)
- **Conditional UI**: Hide inappropriate elements (chat, member avatars, confirm button)
- **Educational**: Info alerts explain sandbox mode features

---

## Component Changes

### 1. MyGames Screen - Add Sandbox Tab

**Location**: `packages/web/src/screens/Home/MyGames.tsx`

**Change**: Add new tab to existing tab navigation

**Current tabs**:
- Active
- Completed
- (Other tabs as applicable)

**New tabs**:
- Active
- Completed
- **Sandbox** (NEW)

**Implementation**:

```tsx
const [currentTab, setCurrentTab] = useState<'active' | 'completed' | 'sandbox'>('active');

// Tab navigation
<Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
  <Tab label="Active" value="active" />
  <Tab label="Completed" value="completed" />
  <Tab label="Sandbox" value="sandbox" />
</Tabs>

// Tab content
{currentTab === 'active' && <GameList filter={{ status: 'ACTIVE' }} />}
{currentTab === 'completed' && <GameList filter={{ status: 'COMPLETED' }} />}
{currentTab === 'sandbox' && <GameList filter={{ sandbox: true }} />}
```

**API calls**:
- Active tab: `GET /games/` (default excludes sandbox)
- Completed tab: `GET /games/?status=COMPLETED`
- Sandbox tab: `GET /games/?sandbox=true`

**Navigation**: Clicking any game card navigates to `GameDetailScreen` (same as regular games)

---

### 2. CreateGame Screen - Split into Standard/Sandbox Tabs

**Location**: `packages/web/src/screens/Home/CreateGame.tsx`

**Change**: Add tab navigation to split standard and sandbox game creation

**Structure**:
```tsx
<Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
  <Tab label="Standard" value="standard" />
  <Tab label="Sandbox" value="sandbox" />
</Tabs>

{currentTab === 'standard' && <StandardGameForm />}
{currentTab === 'sandbox' && <SandboxGameForm />}
```

---

#### 2a. Standard Game Form

**Existing form** - no changes needed:
- Name (text input)
- Variant (dropdown)
- Movement phase duration (dropdown: 24h, 48h, 1 week, **"Resolve when ready"**)
- Nation assignment (dropdown: Random, Ordered)
- Private (checkbox)

**API call**: `POST /game/`

---

#### 2b. Sandbox Game Form

**New simplified form**:

```tsx
<Box>
  {/* Info Alert */}
  <Alert severity="info" sx={{ mb: 3 }}>
    <AlertTitle>Sandbox Mode</AlertTitle>
    Practice Diplomacy by controlling all nations yourself. Perfect for:
    <ul>
      <li>Learning game mechanics and order types</li>
      <li>Testing strategies and scenarios</li>
      <li>Exploring different variants</li>
    </ul>
    Sandbox games are private, have no time limits, and resolve when you're ready.
  </Alert>

  {/* Simplified form - only name and variant */}
  <TextField
    label="Game Name"
    value={name}
    onChange={(e) => setName(e.target.value)}
    fullWidth
    required
  />

  <FormControl fullWidth sx={{ mt: 2 }}>
    <InputLabel>Variant</InputLabel>
    <Select
      value={variantId}
      onChange={(e) => setVariantId(e.target.value)}
      required
    >
      <MenuItem value="classical">Classical</MenuItem>
      {/* Other variants */}
    </Select>
  </FormControl>

  <Button
    variant="contained"
    onClick={handleCreateSandboxGame}
    disabled={!name || !variantId}
    sx={{ mt: 3 }}
  >
    Create Sandbox Game
  </Button>
</Box>
```

**Fields** (only 2 required):
- Name (text input)
- Variant (dropdown)

**Hardcoded values** (not shown to user):
- `sandbox: true`
- `private: true`
- `movement_phase_duration: null` (infinite/resolve when ready)
- `nation_assignment: ORDERED`

**API call**: `POST /sandbox-game/`

**Request body**:
```json
{
  "name": "My Practice Game",
  "variantId": "classical"
}
```

---

### 3. ActivePhaseOrders Component - Conditional Rendering

**Location**: `packages/web/src/screens/GameDetail/OrdersScreen.tsx` (or similar)

**Changes**:

#### 3a. Map and List Display

**Behavior**: Show map + orders list (same as regular games)
- Interactive map for clicking provinces to create orders
- Orders list showing created orders
- **No changes to order creation flow** - works exactly the same

#### 3b. Orders List - Group by Nation (Sandbox Only)

For sandbox games, group orders by nation with subheaders:

```tsx
{game.sandbox ? (
  // Grouped by nation
  <Box>
    {nations.map(nation => (
      <Box key={nation.id} sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {nation.name}
        </Typography>
        {ordersForNation(nation.id).map(order => (
          <OrderCard key={order.id} order={order} />
        ))}
        {ordersForNation(nation.id).length === 0 && (
          <Typography color="text.secondary">No orders</Typography>
        )}
      </Box>
    ))}
  </Box>
) : (
  // Regular flat list
  <Box>
    {orders.map(order => (
      <OrderCard key={order.id} order={order} />
    ))}
  </Box>
)}
```

**Logic for grouping**:
```tsx
const ordersForNation = (nationId: string) => {
  return orders.filter(order => order.nation.id === nationId);
};
```

#### 3c. Confirm vs Resolve Button

**Conditional rendering** based on `game.sandbox`:

```tsx
{game.sandbox ? (
  // Sandbox: Resolve Phase button
  <Button
    variant="contained"
    color="primary"
    onClick={handleResolvePhase}
    fullWidth
  >
    Resolve Phase
  </Button>
) : (
  // Regular: Confirm Orders button
  <Button
    variant="contained"
    color="primary"
    onClick={handleConfirmOrders}
    disabled={phaseState.ordersConfirmed}
    fullWidth
  >
    {phaseState.ordersConfirmed ? 'Orders Confirmed' : 'Confirm Orders'}
  </Button>
)}
```

**API calls**:
- Sandbox: `POST /game/{gameId}/resolve-phase/`
- Regular: `PATCH /game/{gameId}/confirm-phase/`

**Button behavior**:
- Regular game: Confirm orders, then wait for timer or all players
- Sandbox game: Immediately resolve phase and move to next phase

---

### 4. Phase Timer Display

**Location**: Various components showing phase deadline

**Change**: Conditional text based on `scheduledResolution`

```tsx
{game.currentPhase.scheduledResolution ? (
  <Typography>
    Resolves in {formatTimeRemaining(game.currentPhase.scheduledResolution)}
  </Typography>
) : (
  <Typography color="text.secondary">
    Resolve when ready
  </Typography>
)}
```

**Applies to**:
- Regular games with `movement_phase_duration = null`: "Resolve when ready"
- Sandbox games (always `null`): "Resolve when ready"
- Regular games with time limit: "Resolves in 14h 32m"

---

### 5. GameCard Component - Hide Member Avatars

**Location**: `packages/web/src/components/GameCard.tsx`

**Change**: Conditionally hide member avatar display

```tsx
<Card>
  <CardContent>
    <Typography variant="h6">{game.name}</Typography>
    <Typography variant="body2">{game.variant.name}</Typography>
    <Typography variant="body2">
      {game.currentPhase.name}
    </Typography>

    {/* Hide avatars for sandbox games */}
    {!game.sandbox && (
      <AvatarGroup max={4} sx={{ mt: 1 }}>
        {game.members.map(member => (
          <Avatar
            key={member.id}
            alt={member.user.username}
            src={member.user.profile.avatarUrl}
          />
        ))}
      </AvatarGroup>
    )}
  </CardContent>
</Card>
```

**Rationale**: In sandbox games, all members are the same user, so showing avatars is redundant and confusing.

---

### 6. GameInfo Component - Hide Member Avatars

**Location**: `packages/web/src/components/GameInfo.tsx`

**Change**: Conditionally hide member list/avatars

```tsx
<Box>
  <Typography variant="h6">{game.name}</Typography>
  <Typography variant="body2">{game.variant.name}</Typography>
  <Typography variant="body2">{game.status}</Typography>

  {/* Hide member section for sandbox games */}
  {!game.sandbox && (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2">Players</Typography>
      {game.members.map(member => (
        <Box key={member.id} sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
          <Avatar
            src={member.user.profile.avatarUrl}
            sx={{ width: 32, height: 32, mr: 1 }}
          />
          <Typography variant="body2">
            {member.user.username}
            {member.nation && ` - ${member.nation.name}`}
          </Typography>
        </Box>
      ))}
    </Box>
  )}
</Box>
```

---

### 7. GameInfoScreen Component - Hide Member Avatars

**Location**: `packages/web/src/screens/GameDetail/GameInfoScreen.tsx`

**Change**: Same as GameInfo component - conditionally hide member display

```tsx
<Box>
  <Typography variant="h5">{game.name}</Typography>

  {/* Game details */}
  <List>
    <ListItem>
      <ListItemText primary="Variant" secondary={game.variant.name} />
    </ListItem>
    <ListItem>
      <ListItemText primary="Status" secondary={game.status} />
    </ListItem>
    <ListItem>
      <ListItemText primary="Current Phase" secondary={game.currentPhase.name} />
    </ListItem>
  </List>

  {/* Hide players section for sandbox games */}
  {!game.sandbox && (
    <>
      <Typography variant="h6" sx={{ mt: 3 }}>Players</Typography>
      <List>
        {game.members.map(member => (
          <ListItem key={member.id}>
            <ListItemAvatar>
              <Avatar src={member.user.profile.avatarUrl} />
            </ListItemAvatar>
            <ListItemText
              primary={member.user.username}
              secondary={member.nation?.name}
            />
          </ListItem>
        ))}
      </List>
    </>
  )}
</Box>
```

---

### 8. ChannelListScreen - Show Alert for Sandbox Games

**Location**: `packages/web/src/screens/GameDetail/ChannelListScreen.tsx`

**Change**: Show info alert when game is sandbox and no channels exist

```tsx
{game.sandbox ? (
  // Sandbox: Show alert explaining no chat
  <Alert severity="info">
    <AlertTitle>Chat Disabled</AlertTitle>
    Chat is not available in sandbox games. Sandbox games are single-player
    practice environments where you control all nations.
  </Alert>
) : channels.length === 0 ? (
  // Regular game with no channels
  <Typography color="text.secondary">
    No channels yet. Create one to start communicating with other players.
  </Typography>
) : (
  // Regular game with channels
  <List>
    {channels.map(channel => (
      <ChannelListItem key={channel.id} channel={channel} />
    ))}
  </List>
)}
```

**Behavior**:
- Sandbox games: Always show alert (no channels will exist)
- Regular games: Show channels or empty state

---

### 9. Hide Channel UI Elements

**Various locations**: Navigation, tabs, etc.

**Change**: Conditionally hide channel-related UI

```tsx
// In GameDetail navigation/tabs
{!game.sandbox && (
  <Tab label="Channels" value="channels" />
)}

// In mobile bottom navigation
{!game.sandbox && (
  <BottomNavigationAction
    label="Chat"
    value="channels"
    icon={<ChatIcon />}
  />
)}
```

**Locations to update**:
- GameDetail screen tabs/navigation
- Mobile bottom navigation
- Any channel entry points

---

## API Integration

### Codegen

After all backend changes are complete, regenerate TypeScript types:

```bash
docker compose up codegen
```

This will generate:
- New `sandbox` field on `Game` type
- New `createSandboxGame` endpoint
- New `resolvePhase` endpoint
- Updated `listPhaseStates` endpoint (returns array instead of single object)

### New API Endpoints to Use

**Create Sandbox Game**:
```typescript
const game = await api.createSandboxGame({
  name: gameName,
  variantId: selectedVariantId,
});
```

**Resolve Phase** (sandbox only):
```typescript
await api.resolvePhase(gameId);
```

**List Phase States** (updated - returns array):
```typescript
const phaseStates = await api.listPhaseStates(gameId);
// Regular game: phaseStates.length === 1
// Sandbox game: phaseStates.length === 7 (for Classic)

// Merge orderable provinces
const allOrderableProvinces = phaseStates.flatMap(ps => ps.orderableProvinces);
```

---

## Type Definitions (Post-Codegen)

**Game type** (updated):
```typescript
interface Game {
  id: string;
  name: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED';
  sandbox: boolean; // NEW
  private: boolean;
  variant: Variant;
  members: Member[];
  phases: Phase[];
  currentPhase: Phase;
  canJoin: boolean;
  canLeave: boolean;
  phaseConfirmed: boolean;
  movementPhaseDuration: string | null; // null for infinite
  nationAssignment: string;
}
```

**Phase type** (updated):
```typescript
interface Phase {
  id: number;
  name: string;
  type: 'MOVEMENT' | 'RETREAT' | 'ADJUSTMENT';
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED';
  scheduledResolution: string | null; // null for sandbox/infinite
  ordinal: number;
  // ... other fields
}
```

---

## Helper Functions

### Check if Orders Confirmed (Sandbox)

For sandbox games, check if ALL phase states have orders confirmed:

```typescript
const areAllOrdersConfirmed = (phaseStates: PhaseState[]): boolean => {
  return phaseStates.every(ps => ps.ordersConfirmed);
};
```

Note: This won't be displayed in UI (no confirm button), but could be used for validation.

### Get Orderable Provinces (Sandbox)

Merge orderable provinces from all phase states:

```typescript
const getAllOrderableProvinces = (phaseStates: PhaseState[]): Province[] => {
  const allProvinces = phaseStates.flatMap(ps => ps.orderableProvinces);

  // Remove duplicates by province ID
  const uniqueProvinces = Array.from(
    new Map(allProvinces.map(p => [p.provinceId, p])).values()
  );

  return uniqueProvinces;
};
```

### Group Orders by Nation (Sandbox)

For displaying orders grouped by nation:

```typescript
const groupOrdersByNation = (orders: Order[]): Map<string, Order[]> => {
  const grouped = new Map<string, Order[]>();

  orders.forEach(order => {
    const nationId = order.nation.id;
    if (!grouped.has(nationId)) {
      grouped.set(nationId, []);
    }
    grouped.get(nationId)!.push(order);
  });

  return grouped;
};
```

---

## Testing Checklist

### Component Tests

**MyGames**:
- [ ] Sandbox tab renders correctly
- [ ] Clicking sandbox tab fetches games with `sandbox=true` filter
- [ ] Sandbox games appear only in sandbox tab
- [ ] Regular games do not appear in sandbox tab

**CreateGame**:
- [ ] Standard/Sandbox tabs render correctly
- [ ] Standard form shows all fields
- [ ] Sandbox form shows only name + variant
- [ ] Sandbox form shows info alert
- [ ] Creating sandbox game calls correct endpoint
- [ ] Creating standard game still works

**ActivePhaseOrders**:
- [ ] Regular game shows "Confirm Orders" button
- [ ] Sandbox game shows "Resolve Phase" button
- [ ] Sandbox game groups orders by nation
- [ ] Regular game shows flat order list
- [ ] Resolve Phase button calls correct endpoint

**GameCard**:
- [ ] Regular game shows member avatars
- [ ] Sandbox game hides member avatars

**GameInfo/GameInfoScreen**:
- [ ] Regular game shows member list
- [ ] Sandbox game hides member list

**ChannelListScreen**:
- [ ] Regular game shows channels
- [ ] Sandbox game shows info alert
- [ ] Alert explains chat is disabled

### Integration Tests

**Sandbox Game Flow**:
- [ ] Create sandbox game
- [ ] Navigate to game detail screen
- [ ] Verify no chat UI visible
- [ ] Verify no member avatars visible
- [ ] Verify "Resolve when ready" shown instead of timer
- [ ] Fetch phase states (returns array of 7 for Classic)
- [ ] Create orders for multiple nations
- [ ] Orders grouped by nation in list
- [ ] Click "Resolve Phase" button
- [ ] Phase resolves immediately
- [ ] Next phase loads

**Regular Game Flow**:
- [ ] Create regular game
- [ ] All existing functionality still works
- [ ] Game does not appear in sandbox tab
- [ ] Chat UI visible
- [ ] Member avatars visible
- [ ] Confirm orders button visible

---

## Implementation Order

Recommended order of implementation:

1. **Run codegen** (after backend changes complete)
   - Generates types and API methods

2. **MyGames screen**
   - Add sandbox tab
   - Test filtering

3. **CreateGame screen**
   - Add Standard/Sandbox tabs
   - Implement sandbox form
   - Add info alert

4. **GameCard component**
   - Hide avatars for sandbox games

5. **GameInfo/GameInfoScreen components**
   - Hide member sections for sandbox games

6. **ActivePhaseOrders component**
   - Add conditional button (confirm vs resolve)
   - Add nation grouping for sandbox
   - Integrate resolve phase endpoint

7. **Phase timer display**
   - Show "Resolve when ready" for null scheduled resolution

8. **ChannelListScreen**
   - Add info alert for sandbox games

9. **Hide channel UI**
   - Remove from navigation/tabs for sandbox games

10. **Testing**
    - Component tests
    - Integration tests
    - Manual QA

---

## Notes

- **Minimal frontend changes**: Most components work with simple conditional rendering
- **Consistent UX**: Order creation works exactly the same (map interaction)
- **Clear separation**: Sandbox tab prevents confusion with regular games
- **Educational**: Info alerts guide users on sandbox features
- **Type safety**: Codegen ensures TypeScript types match backend
- **Mobile-friendly**: List view with nation grouping works well on small screens
