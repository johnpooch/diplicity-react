import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
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
const mockDeleteOrderMutation = vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false }));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamePhaseRetrieveSuspense: () => ({ data: mockPhaseData() }),
  useGameOrdersListSuspense: () => ({ data: mockOrdersData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamePhaseStatesListSuspense: () => ({ data: mockPhaseStatesData() }),
  useGameOrdersDeleteDestroy: () => mockDeleteOrderMutation(),
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
  getContrastColor: () => "#ffffff",
}));
vi.mock("@/components/PhaseStepper", () => ({
  PhaseStepperTitle: () => null,
  PhaseStepperActions: () => null,
}));
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

const LocationProbe = () => {
  const location = useLocation();
  return (
    <div data-testid="location">
      {location.pathname}
      {location.search}
    </div>
  );
};

const renderOrdersScreenWithLocation = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/orders"]}>
        <LocationProbe />
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/orders"
            element={<OrdersScreen />}
          />
          <Route path="/game/:gameId/phase/:phaseId" element={<div>Map screen</div>} />
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

describe("OrdersScreen spectating", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockPhaseStatesData.mockReturnValue([]);
    mockOrdersData.mockReturnValue([]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ isCurrentUser: false })],
    });
  });

  it("shows the spectating notice when the user is not a member", () => {
    renderOrdersScreen();

    expect(screen.getByText(/spectating/i)).toBeInTheDocument();
  });

  it("hides the confirm orders button when the user is not a member", () => {
    renderOrdersScreen();

    expect(screen.queryByRole("button", { name: /orders confirmed/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /confirm orders/i })).not.toBeInTheDocument();
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

    expect(screen.getByText(/spectating/i)).toBeInTheDocument();
  });

  it("falls back to an unmatched member instead of crashing when game.members is not an array and there are past orders to group by nation", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: undefined,
    });
    mockPhaseData.mockReturnValue({
      id: 1, status: "completed", supplyCenters: [], units: [],
    });
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "England" },
        source: { id: "lon", name: "London" },
        summary: "Hold",
        resolution: null,
      },
    ]);

    renderOrdersScreen();

    expect(screen.getByText("England")).toBeInTheDocument();
  });

  it("renders without crashing when orders is not an array", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember()],
    });
    mockPhaseData.mockReturnValue({
      id: 1, status: "completed", supplyCenters: [], units: [],
    });
    mockOrdersData.mockReturnValue(undefined);

    renderOrdersScreen();

    expect(screen.getByText(/no orders created/i)).toBeInTheDocument();
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

  it("matches a historical order to a fleet's named coast via the order's parent-province source", () => {
    mockPhaseData.mockReturnValue({
      id: 1,
      status: "completed",
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
    mockPhaseStatesData.mockReturnValue([]);
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "England" },
        source: { id: "spa", name: "Spain" },
        summary: "Hold",
        resolution: { status: "Succeeded" },
      },
    ]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: false })],
    });

    renderOrdersScreen();

    expect(screen.getByText(/Fleet Spain \(NC\)/)).toBeInTheDocument();
    expect(screen.getByText("Hold")).toBeInTheDocument();
    expect(screen.queryByText("Order not provided")).not.toBeInTheDocument();
  });
});

describe("OrdersScreen delete order button", () => {
  beforeEach(() => {
    mockDeleteOrderMutation.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ civilDisorder: false })],
    });
    mockPhaseData.mockReturnValue({
      id: 1,
      status: "active",
      supplyCenters: [],
      units: [
        {
          type: "Army",
          dislodged: false,
          nation: { name: "England" },
          province: { id: "lon", name: "London", parentId: null },
        },
      ],
    });
    mockPhaseStatesData.mockReturnValue([
      {
        member: baseMember({ civilDisorder: false }),
        orderableProvinces: [{ id: "lon", name: "London", parentId: null }],
      },
    ]);
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "England" },
        source: { id: "lon", name: "London" },
        summary: "Hold",
        resolution: null,
      },
    ]);
  });

  it("disables the delete button while a delete is pending", () => {
    mockDeleteOrderMutation.mockReturnValue({ mutateAsync: vi.fn(), isPending: true });

    renderOrdersScreen();

    expect(screen.getByLabelText(/Delete order for/)).toBeDisabled();
  });

  it("enables the delete button when no delete is pending", () => {
    renderOrdersScreen();

    expect(screen.getByLabelText(/Delete order for/)).not.toBeDisabled();
  });
});

describe("OrdersScreen no orders required (active phase, has a member)", () => {
  it("shows an inline nation heading and message, not the centered notice", () => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockOrdersData.mockReturnValue([]);
    mockPhaseStatesData.mockReturnValue([
      { member: baseMember(), orderableProvinces: [] },
    ]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember()],
    });

    renderOrdersScreen();

    expect(screen.getByText("England")).toBeInTheDocument();
    expect(screen.getByText("No orders required")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /england/i })
    ).not.toBeInTheDocument();
  });
});

describe("OrdersScreen historical multi-nation view", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "completed", supplyCenters: [], units: [],
    });
    mockPhaseStatesData.mockReturnValue([]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [
        baseMember({ isCurrentUser: true, nation: "England" }),
        baseMember({ id: 2, isCurrentUser: false, nation: "France" }),
      ],
    });
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "England" },
        source: { id: "lon", name: "London" },
        summary: "Hold",
        resolution: null,
      },
      {
        nation: { name: "France" },
        source: { id: "par", name: "Paris" },
        summary: "Hold",
        resolution: null,
      },
    ]);
  });

  it("opens the current user's nation by default and collapses others", () => {
    renderOrdersScreen();

    expect(screen.getByText("London")).toBeInTheDocument();
    expect(screen.queryByText("Paris")).not.toBeInTheDocument();
  });

  it("always renders the current user's nation heading first, regardless of order data", () => {
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "France" },
        source: { id: "par", name: "Paris" },
        summary: "Hold",
        resolution: null,
      },
      {
        nation: { name: "England" },
        source: { id: "lon", name: "London" },
        summary: "Hold",
        resolution: null,
      },
    ]);

    renderOrdersScreen();

    const headings = screen.getAllByRole("button", { name: /france|england/i });
    expect(headings[0]).toHaveAccessibleName(/england/i);
    expect(headings[1]).toHaveAccessibleName(/france/i);
  });

  it("expands a collapsed nation on click, and only shows the 'you' badge on the current user's nation", async () => {
    renderOrdersScreen();

    const franceHeading = screen.getByRole("button", { name: /france/i });
    expect(within(franceHeading).queryByText("you")).not.toBeInTheDocument();

    const englandHeading = screen.getByRole("button", { name: /england/i });
    expect(within(englandHeading).getByText("you")).toBeInTheDocument();

    await userEvent.click(franceHeading);

    expect(screen.getByText("Paris")).toBeInTheDocument();
  });
});

describe("OrdersScreen historical phase with unordered units", () => {
  it("shows a row for every unit the nation had, not just the ones with orders", () => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1,
      status: "completed",
      supplyCenters: [],
      units: [
        { type: "Army", dislodged: false, nation: { name: "Italy" }, province: { id: "tri", name: "Trieste", parentId: null } },
        { type: "Fleet", dislodged: false, nation: { name: "Italy" }, province: { id: "nap", name: "Naples", parentId: null } },
        { type: "Army", dislodged: false, nation: { name: "Italy" }, province: { id: "rom", name: "Rome", parentId: null } },
        { type: "Army", dislodged: false, nation: { name: "Italy" }, province: { id: "ven", name: "Venice", parentId: null } },
      ],
    });
    mockPhaseStatesData.mockReturnValue([]);
    mockOrdersData.mockReturnValue([
      {
        nation: { name: "Italy" },
        source: { id: "tri", name: "Trieste" },
        summary: "Move to Budapest",
        resolution: { status: "Bounced" },
      },
    ]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "completed",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember({ isCurrentUser: true, nation: "Italy" })],
    });

    renderOrdersScreen();

    expect(screen.getByText(/Army Trieste/)).toBeInTheDocument();
    expect(screen.getByText(/Fleet Naples/)).toBeInTheDocument();
    expect(screen.getByText(/Army Rome/)).toBeInTheDocument();
    expect(screen.getByText(/Army Venice/)).toBeInTheDocument();
    expect(screen.getAllByText("Order not provided")).toHaveLength(3);
  });
});

describe("OrdersScreen order creation entry point", () => {
  beforeEach(() => {
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockPhaseData.mockReturnValue({
      id: 1, status: "active", supplyCenters: [], units: [],
    });
    mockPhaseStatesData.mockReturnValue([
      {
        member: baseMember(),
        orderableProvinces: [{ id: "lon", name: "London" }],
      },
    ]);
    mockOrdersData.mockReturnValue([]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      status: "active",
      sandbox: false,
      deadlineMode: "duration",
      phaseConfirmed: false,
      members: [baseMember()],
    });
  });

  it("sets the source search param without navigating away on desktop", async () => {
    renderOrdersScreenWithLocation();

    await userEvent.click(screen.getByRole("button", { name: /create order for london/i }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/game-1/phase/1/orders?source=lon"
    );
  });

  it("navigates to the map screen with the source search param on mobile", async () => {
    window.innerWidth = 500;

    renderOrdersScreenWithLocation();

    await userEvent.click(screen.getByRole("button", { name: /create order for london/i }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/game/game-1/phase/1?source=lon"
    );

    window.innerWidth = 1024;
  });

  it("does not make the row clickable when the order is already provided", () => {
    mockOrdersData.mockReturnValue([
      { nation: { name: "England" }, source: { id: "lon", name: "London" }, summary: "Hold" },
    ]);

    renderOrdersScreenWithLocation();

    expect(
      screen.queryByRole("button", { name: /create order for london/i })
    ).not.toBeInTheDocument();
  });
});
