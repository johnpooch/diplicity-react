# Minimizing useEffect Usage

## Goal

- Determine if useEffect is actually needed
- If unnecessary, refactor to remove it
- If necessary, ensure it's properly implemented
- Prefer derived state, event handlers, and proper React patterns

## When to Avoid useEffect

### 1. Transforming Data for Rendering

**❌ Don't use useEffect for derived state:**
```tsx
// Bad - unnecessary effect
const [fullName, setFullName] = useState('');
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// ✅ Good - compute during render
const fullName = `${firstName} ${lastName}`;
```

### 2. Handling User Events

**❌ Don't use useEffect to respond to events:**
```tsx
// Bad - effect triggered by state change
const [shouldSubmit, setShouldSubmit] = useState(false);
useEffect(() => {
  if (shouldSubmit) {
    submitOrder();
    setShouldSubmit(false);
  }
}, [shouldSubmit]);

const handleClick = () => setShouldSubmit(true);

// ✅ Good - handle in event handler directly
const handleClick = () => {
  submitOrder();
};
```

### 3. Resetting State When Props Change

**❌ Don't reset state in effects:**
```tsx
// Bad - resetting form on game change
export function OrderForm({ gameId }) {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    setOrders([]);
  }, [gameId]);
}

// ✅ Good - use key to remount component
export function GameOrders({ gameId }) {
  return <OrderForm key={gameId} gameId={gameId} />;
}

function OrderForm({ gameId }) {
  const [orders, setOrders] = useState([]); // Resets automatically on remount
}
```

### 4. Synchronizing State Between Components

**❌ Don't sync state with effects:**
```tsx
// Bad - notifying parent via effect
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);

  useEffect(() => {
    onChange(isOn);
  }, [isOn, onChange]);

  const toggle = () => setIsOn(!isOn);
}

// ✅ Good - notify in event handler
function Toggle({ onChange }) {
  const [isOn, setIsOn] = useState(false);

  const toggle = () => {
    const newValue = !isOn;
    setIsOn(newValue);
    onChange(newValue);
  };
}
```

### 5. Expensive Calculations

**❌ Don't use useEffect for caching:**
```tsx
// Bad - using effect for expensive calculation
const [filteredGames, setFilteredGames] = useState([]);
useEffect(() => {
  setFilteredGames(filterGames(games, searchTerm));
}, [games, searchTerm]);

// ✅ Good - use useMemo (only if actually expensive)
const filteredGames = useMemo(
  () => filterGames(games, searchTerm),
  [games, searchTerm]
);

// ✅ Better - just compute if not expensive (React 19 auto-memoizes)
const filteredGames = filterGames(games, searchTerm);
```

## When useEffect IS Appropriate

### 1. External System Synchronization

**✅ Good - syncing with browser API:**
```tsx
// Listening to online/offline status
useEffect(() => {
  const handleOnline = () => setIsOnline(true);
  const handleOffline = () => setIsOnline(false);

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}, []);
```

### 2. DOM Manipulation

**✅ Good - direct DOM interaction:**
```tsx
// Integrating with non-React map library
useEffect(() => {
  const map = new MapLibrary(mapRef.current);
  map.render(gameState);

  return () => {
    map.destroy();
  };
}, [gameState]);
```

### 3. WebSocket Connections

**✅ Good - managing WebSocket lifecycle:**
```tsx
useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8000/game/${gameId}`);

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    handleGameUpdate(update);
  };

  return () => {
    ws.close();
  };
}, [gameId]);
```

### 4. Timers

**✅ Good - managing intervals:**
```tsx
useEffect(() => {
  const interval = setInterval(() => {
    checkForPhaseDeadline();
  }, 60000); // Check every minute

  return () => clearInterval(interval);
}, []);
```

## Diplicity-Specific Patterns

### Game State Updates

```tsx
// ❌ Bad - using effect to compute game status
const [canSubmitOrders, setCanSubmitOrders] = useState(false);
useEffect(() => {
  setCanSubmitOrders(
    game.phase === 'movement' &&
    !hasSubmittedOrders &&
    isMyTurn
  );
}, [game.phase, hasSubmittedOrders, isMyTurn]);

// ✅ Good - derive during render
const canSubmitOrders =
  game.phase === 'movement' &&
  !hasSubmittedOrders &&
  isMyTurn;
```

### Order Validation

```tsx
// ❌ Bad - validating orders in effect
const [validOrders, setValidOrders] = useState([]);
useEffect(() => {
  const valid = orders.filter(order => validateOrder(order));
  setValidOrders(valid);
}, [orders]);

// ✅ Good - compute valid orders directly
const validOrders = orders.filter(order => validateOrder(order));
```

### Map Interactions

```tsx
// ✅ Good - Map integration needs effect
useEffect(() => {
  if (!mapRef.current) return;

  // Update map visualization
  const provinces = mapRef.current.querySelectorAll('.province');
  provinces.forEach(province => {
    const id = province.getAttribute('data-id');
    const owner = gameState.ownership[id];
    province.style.fill = getCountryColor(owner);
  });
}, [gameState.ownership]);
```

## Migration Checklist

When you see a useEffect, ask:

1. **Is it syncing with an external system?**
   - YES → Keep it, ensure cleanup
   - NO → Continue to next question

2. **Is it transforming data for rendering?**
   - YES → Replace with derived state

3. **Is it responding to a user event?**
   - YES → Move to event handler

4. **Is it resetting state on prop change?**
   - YES → Use key prop to remount

5. **Is it synchronizing component state?**
   - YES → Lift state up or notify in handler

6. **Is it a chain of state updates?**
   - YES → Consolidate in initiating event

## Common Refactoring Examples

### Form Submission

```tsx
// ❌ Before - effect chain
const [formData, setFormData] = useState(null);
const [isSubmitting, setIsSubmitting] = useState(false);

useEffect(() => {
  if (formData) {
    setIsSubmitting(true);
    submitForm(formData).then(() => {
      setIsSubmitting(false);
      setFormData(null);
    });
  }
}, [formData]);

const handleSubmit = (data) => setFormData(data);

// ✅ After - direct handler
const [isSubmitting, setIsSubmitting] = useState(false);

const handleSubmit = async (data) => {
  setIsSubmitting(true);
  await submitForm(data);
  setIsSubmitting(false);
};
```

### Data Loading

```tsx
// ❌ Before - manual effect
const [games, setGames] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetch('/api/games')
    .then(res => res.json())
    .then(data => {
      setGames(data);
      setLoading(false);
    });
}, []);

// ✅ After - TanStack Query
const { data: games, isPending } = useQuery({
  queryKey: ['games'],
  queryFn: () => fetch('/api/games').then(res => res.json()),
});
```

### Notification After Action

```tsx
// ❌ Before - effect for notification
const [showSuccess, setShowSuccess] = useState(false);

useEffect(() => {
  if (showSuccess) {
    toast.success('Order submitted!');
    setShowSuccess(false);
  }
}, [showSuccess]);

const handleSubmit = () => {
  submitOrder();
  setShowSuccess(true);
};

// ✅ After - notify in handler
const handleSubmit = () => {
  submitOrder();
  toast.success('Order submitted!');
};
```

## Best Practices

1. **Prefer computation over effects** - Calculate values during render
2. **Handle events where they occur** - Don't defer to effects
3. **Use proper cleanup** - Always return cleanup functions for subscriptions
4. **Keep effects focused** - One effect per external system
5. **Minimize dependencies** - Only include values that actually change behavior
6. **Use React Query for data** - Don't manually manage loading states
7. **Trust React 19** - It auto-memoizes, you don't need useMemo everywhere