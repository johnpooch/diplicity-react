import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

import { OrdersScreen } from "./OrdersScreen";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockGameData = vi.fn();
const mockPhaseData = vi.fn();
const mockOrdersData = vi.fn();
const mockVariantsData = vi.fn();
const mockPhaseStatesData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamePhaseRetrieveSuspense: () => ({ data: mockPhaseData() }),
  useGameOrdersListSuspense: () => ({ data: mockOrdersData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useGamePhaseStatesListSuspense: () => ({ data: mockPhaseStatesData() }),
  useGameOrdersDeleteDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameConfirmPhasePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameResolvePhaseCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGamesDrawProposalsListSuspense: () => ({ data: [] }),
  getGameRetrieveQueryKey: () => ["game"],
  getGameOrdersListQueryKey: () => ["orders"],
  getGameOptionsRetrieveQueryKey: () => ["options"],
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
}));
vi.mock("@/components/PhaseSelect", () => ({ PhaseSelect: () => null }));
vi.mock("@/components/PhaseGuidance", () => ({ PhaseGuidance: () => null }));
vi.mock("@/components/GameDropdownMenu", () => ({ GameDropdownMenu: () => null }));

const baseMember = (overrides = {}) => ({
  id: 1,
  name: "Alice",
  picture: null,
  isCurrentUser: true,
  nation: "England",
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  ...overrides,
});

const renderOrdersScreen = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/orders"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/orders"
            element={<OrdersScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("OrdersScreen civil disorder handling", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockOrdersData.mockReturnValue([]);
    mockPhaseStatesData.mockReturnValue([]);
  });

  it("shows civil disorder banner when current member is in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: true })],
    });

    renderOrdersScreen();

    expect(screen.getByText(/your nation is in civil disorder/i)).toBeInTheDocument();
  });

  it("does not show civil disorder banner when current member is not in CD", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: false })],
    });

    renderOrdersScreen();

    expect(screen.queryByText(/your nation is in civil disorder/i)).not.toBeInTheDocument();
  });

  it("hides the confirm orders button when current member is in CD", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: true })],
    });
    mockPhaseStatesData.mockReturnValue([
      {
        member: baseMember({ civilDisorder: true }),
        orderableProvinces: [{ id: "lon", name: "London" }],
      },
    ]);

    renderOrdersScreen();

    expect(screen.queryByRole("button", { name: /confirm orders/i })).not.toBeInTheDocument();
  });
});
