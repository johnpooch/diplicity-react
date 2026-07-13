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
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamePhaseStatesListSuspense: () => ({ data: mockPhaseStatesData() }),
  useGameOrdersDeleteDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameConfirmPhasePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameResolvePhaseCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGameRecoverFromCivilDisorderCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGamesDrawProposalsListSuspense: () => ({ data: [] }),
  getGameRetrieveQueryKey: () => ["game"],
  getGameOrdersListQueryKey: () => ["orders"],
  getGameOptionsRetrieveQueryKey: () => ["options"],
  getGamePhaseStatesListQueryKey: () => ["phase-states"],
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

  it("shows 'I'm back' button when current member is in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: true })],
    });

    renderOrdersScreen();

    expect(screen.getByRole("button", { name: /i'm back/i })).toBeInTheDocument();
  });

  it("does not show 'I'm back' button when current member is not in civil disorder", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: false })],
    });

    renderOrdersScreen();

    expect(screen.queryByRole("button", { name: /i'm back/i })).not.toBeInTheDocument();
  });
});

describe("OrdersScreen confirm orders button", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockPhaseStatesData.mockReturnValue([
      {
        member: baseMember({ civilDisorder: false }),
        orderableProvinces: [{ id: "lon", name: "London" }],
      },
    ]);
    mockOrdersData.mockReturnValue([]);
  });

  it("shows confirm orders button for fixed-time game", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "fixed_time",
      phaseConfirmed: false,
      members: [baseMember()],
    });

    renderOrdersScreen();

    expect(screen.getByRole("button", { name: /confirm orders/i })).toBeInTheDocument();
  });

  it("shows confirm orders button for duration game", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember()],
    });

    renderOrdersScreen();

    expect(screen.getByRole("button", { name: /confirm orders/i })).toBeInTheDocument();
  });
});

describe("OrdersScreen resilience to malformed list data", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockPhaseStatesData.mockReturnValue([]);
  });

  it("renders without crashing when game.members is not an array", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: undefined,
    });
    mockOrdersData.mockReturnValue([]);

    renderOrdersScreen();

    expect(screen.getByText(/no orders required/i)).toBeInTheDocument();
  });

  it("renders without crashing when orders is not an array", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember()],
    });
    mockOrdersData.mockReturnValue(undefined);

    renderOrdersScreen();

    expect(screen.getByText(/no orders required/i)).toBeInTheDocument();
  });
});

describe("OrdersScreen named coast display", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockOrdersData.mockReturnValue([]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: false })],
    });
  });

  it("shows the unit type and coast name for a fleet on a named coast", () => {
    mockPhaseData.mockReturnValue({
      id: 1,
      status: "active",
      supplyCenters: [],
      units: [
        {
          type: "Fleet",
          dislodged: false,
          nation: { name: "England" },
          province: { id: "spa/nc", name: "Spain (NC)", parentId: "spa" },
        },
      ],
    });
    mockPhaseStatesData.mockReturnValue([
      {
        member: baseMember({ civilDisorder: false }),
        orderableProvinces: [{ id: "spa", name: "Spain", parentId: null }],
      },
    ]);

    renderOrdersScreen();

    expect(screen.getByText(/Fleet Spain \(NC\)/)).toBeInTheDocument();
  });
});
