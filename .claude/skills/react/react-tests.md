# React Testing Best Practices

## Core Testing Principles

- Always use `test` instead of `it` for test definitions
- Use Testing Library's user-centric queries
- Mock API calls with MSW (Mock Service Worker)
- Focus on testing user behavior, not implementation details
- Write tests alongside feature development
- Run tests with `npm run test` (uses Vitest)

## Test File Structure

```typescript
// GameCard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach } from 'vitest';
import { GameCard } from './GameCard';

describe('GameCard', () => {
  test('displays game information correctly', () => {
    // Test implementation
  });

  test('handles user interactions', async () => {
    // Test implementation
  });
});
```

## Testing Library Queries

### Priority Order (Use in this order)

```typescript
// 1. ✅ Queries accessible to everyone (best)
screen.getByRole('button', { name: /submit order/i });
screen.getByLabelText('Email address');
screen.getByPlaceholderText('Enter game name');
screen.getByText('Welcome to Diplomacy');
screen.getByDisplayValue('current-value');

// 2. ⚠️ Semantic queries (good)
screen.getByAltText('Game map');
screen.getByTitle('Delete game');

// 3. ❌ Test IDs (last resort)
screen.getByTestId('game-card');
```

## Component Testing Patterns

### Basic Component Test

```typescript
import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import { GameCard } from './GameCard';

test('renders game card with correct information', () => {
  const game = {
    id: '1',
    name: 'Test Game',
    phase: 'Spring 1901',
    variant: 'Classical',
  };

  render(<GameCard game={game} />);

  expect(screen.getByText('Test Game')).toBeInTheDocument();
  expect(screen.getByText('Spring 1901')).toBeInTheDocument();
  expect(screen.getByText('Classical')).toBeInTheDocument();
});
```

### Testing with React Router

```typescript
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { test, expect } from 'vitest';
import { Navigation } from './Navigation';

test('highlights active navigation link', () => {
  render(
    <MemoryRouter initialEntries={['/games']}>
      <Navigation />
    </MemoryRouter>
  );

  const gamesLink = screen.getByRole('link', { name: /games/i });
  expect(gamesLink).toHaveAttribute('aria-current', 'page');
});
```

### Testing with Redux

```typescript
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { test, expect } from 'vitest';
import { GamesList } from './GamesList';
import { gamesReducer } from '@/store/slices/gamesSlice';

test('displays games from Redux store', () => {
  const store = configureStore({
    reducer: { games: gamesReducer },
    preloadedState: {
      games: {
        items: [
          { id: '1', name: 'Game 1' },
          { id: '2', name: 'Game 2' },
        ],
      },
    },
  });

  render(
    <Provider store={store}>
      <GamesList />
    </Provider>
  );

  expect(screen.getByText('Game 1')).toBeInTheDocument();
  expect(screen.getByText('Game 2')).toBeInTheDocument();
});
```

## API Mocking with MSW

### Setup MSW Handlers

```typescript
// src/test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // GET request handler
  http.get('/api/games', () => {
    return HttpResponse.json([
      { id: '1', name: 'Game 1', phase: 'Spring 1901' },
      { id: '2', name: 'Game 2', phase: 'Fall 1901' },
    ]);
  }),

  // POST request handler
  http.post('/api/orders', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: 'order-1',
      ...body,
      status: 'submitted',
    });
  }),

  // Error response handler
  http.get('/api/games/:id', ({ params }) => {
    if (params.id === 'error') {
      return HttpResponse.json(
        { error: 'Game not found' },
        { status: 404 }
      );
    }
    return HttpResponse.json({
      id: params.id,
      name: `Game ${params.id}`,
    });
  }),
];
```

### Test with MSW

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { test, expect } from 'vitest';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import { GamesList } from './GamesList';

test('handles API error gracefully', async () => {
  // Override handler for this test
  server.use(
    http.get('/api/games', () => {
      return HttpResponse.json(
        { error: 'Server error' },
        { status: 500 }
      );
    })
  );

  render(<GamesList />);

  await waitFor(() => {
    expect(screen.getByText(/error loading games/i)).toBeInTheDocument();
  });
});
```

## Testing User Interactions

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { test, expect } from 'vitest';
import { OrderForm } from './OrderForm';

test('submits order when form is filled correctly', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();

  render(<OrderForm onSubmit={onSubmit} />);

  // Select unit
  const unitSelect = screen.getByLabelText(/select unit/i);
  await user.selectOptions(unitSelect, 'army-paris');

  // Select action
  const actionSelect = screen.getByLabelText(/select action/i);
  await user.selectOptions(actionSelect, 'move');

  // Select destination
  const destinationSelect = screen.getByLabelText(/destination/i);
  await user.selectOptions(destinationSelect, 'burgundy');

  // Submit form
  const submitButton = screen.getByRole('button', { name: /submit order/i });
  await user.click(submitButton);

  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith({
      unit: 'army-paris',
      action: 'move',
      destination: 'burgundy',
    });
  });
});
```

## Testing Forms with React Hook Form

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { test, expect } from 'vitest';
import { CreateGameForm } from './CreateGameForm';

test('shows validation errors for invalid input', async () => {
  const user = userEvent.setup();

  render(<CreateGameForm />);

  // Submit without filling required fields
  const submitButton = screen.getByRole('button', { name: /create game/i });
  await user.click(submitButton);

  await waitFor(() => {
    expect(screen.getByText(/game name is required/i)).toBeInTheDocument();
  });
});
```

## Testing with TanStack Query

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { test, expect } from 'vitest';
import { GameDetails } from './GameDetails';

test('loads and displays game details', async () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <GameDetails gameId="1" />
    </QueryClientProvider>
  );

  // Initially shows loading state
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // Wait for data to load
  await waitFor(() => {
    expect(screen.getByText('Game 1')).toBeInTheDocument();
  });
});
```

## Testing Async Operations

```typescript
test('handles async operations correctly', async () => {
  render(<AsyncComponent />);

  // Wait for async operation to complete
  await waitFor(
    () => {
      expect(screen.getByText(/data loaded/i)).toBeInTheDocument();
    },
    { timeout: 3000 } // Increase timeout if needed
  );
});
```

## Testing Custom Hooks

```typescript
import { renderHook, act } from '@testing-library/react';
import { test, expect } from 'vitest';
import { useGameState } from './useGameState';

test('updates game state correctly', () => {
  const { result } = renderHook(() => useGameState());

  expect(result.current.phase).toBe('Spring 1901');

  act(() => {
    result.current.advancePhase();
  });

  expect(result.current.phase).toBe('Fall 1901');
});
```

## Test Utilities

Create a custom render function with all providers:

```typescript
// src/test/test-utils.tsx
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from '@/store';

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    </Provider>
  );
};

export const renderWithProviders = (ui: React.ReactElement) =>
  render(ui, { wrapper: AllTheProviders });

// Usage
test('renders with all providers', () => {
  renderWithProviders(<MyComponent />);
  // Test implementation
});
```

## Common Testing Patterns

### Testing Loading States

```typescript
test('shows loading state while fetching data', async () => {
  render(<DataComponent />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  await waitFor(() => {
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
});
```

### Testing Error States

```typescript
test('displays error message when API fails', async () => {
  server.use(
    http.get('/api/data', () => {
      return HttpResponse.error();
    })
  );

  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
```

### Testing Accessibility

```typescript
test('has accessible form labels', () => {
  render(<Form />);

  const emailInput = screen.getByLabelText(/email address/i);
  expect(emailInput).toHaveAttribute('type', 'email');
  expect(emailInput).toHaveAttribute('required');
});
```

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run tests with coverage
npm run test -- --coverage

# Run specific test file
npm run test GameCard.test.tsx

# Run tests matching pattern
npm run test -- --grep "displays game"
```

## Best Practices Summary

1. **Test user behavior, not implementation** - Focus on what users see and do
2. **Use semantic queries** - getByRole, getByLabelText over getByTestId
3. **Mock at the network level** - Use MSW for API mocking
4. **Keep tests isolated** - Each test should be independent
5. **Use async utilities** - waitFor, findBy queries for async operations
6. **Test accessibility** - Ensure components are accessible
7. **Avoid testing third-party libraries** - Trust that they work
8. **Write tests alongside features** - Not as an afterthought