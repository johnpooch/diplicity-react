import { render, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation, useSearchParams } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { GameMap } from "./GameMap";
import type { Order } from "@/api/generated/endpoints";

// vi.hoisted ensures these are initialized before vi.mock hoisting runs
const {
  mockToastSuccess,
  mockToastError,
  mockWizardReset,
  mockMapView,
} = vi.hoisted(() => ({
  mockToastSuccess: vi.fn(),
  mockToastError: vi.fn(),
  mockWizardReset: vi.fn(),
  mockMapView: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: mockToastSuccess, error: mockToastError },
}));

vi.mock("@/components/MapView", () => ({
  MapView: (props: unknown) => {
    mockMapView(props);
    return <div data-testid="map" />;
  },
}));

// Wizard state is held in a mutable object the mock reads from each render
type WizardState = {
  isComplete: boolean;
  selectedArray: string[];
  resolvedSelections: Record<string, string>;
  resolvedLabels: Record<string, string>;
  nextField: string | null;
  choices: Array<{ id: string; label: string }>;
  selections: Record<string, string>;
  select: ReturnType<typeof vi.fn>;
  reset: ReturnType<typeof vi.fn>;
};

let mockWizardState: WizardState = buildIdleWizard();

function buildIdleWizard(): WizardState {
  return {
    isComplete: false,
    selectedArray: [],
    resolvedSelections: {},
    resolvedLabels: {},
    nextField: "source",
    choices: [],
    selections: {},
    select: vi.fn(),
    reset: mockWizardReset,
  };
}

vi.mock("@/hooks/useOrderWizard", () => ({
  useOrderWizard: () => mockWizardState,
}));

let mockMutateAsync = vi.fn();
let mockExistingOrders: Order[] = [];
let mockPublishedVariants: (typeof mockVariant)[] = [];
let mockRetrievedVariant: typeof mockVariant | undefined = undefined;

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieve: () => ({ data: mockGame }),
  useVariantsList: () => ({ data: mockPublishedVariants }),
  useVariantsRetrieve: () => ({ data: mockRetrievedVariant }),
  useGamePhaseRetrieve: () => ({ data: mockPhase }),
  useGameOrdersList: () => ({ data: mockExistingOrders }),
  useGameOptionsRetrieve: () => ({ data: { orders: [], fieldOrder: {} } }),
  useGameOrdersCreate: () => ({ mutateAsync: mockMutateAsync }),
  getGameOrdersListQueryKey: (gameId: string, phaseId: number) => [
    `/game/${gameId}/orders/${phaseId}`,
  ],
  getGamePhaseStatesListQueryKey: (gameId: string) => [
    `/game/${gameId}/phase-states/`,
  ],
}));

vi.mock("@/utils/provinces", () => ({
  determineRenderableProvinces: () => ["lon", "nth"],
}));

// --- Fixture data ---
const england = { name: "England", color: "rgb(255,0,0)" };

const makeProvince = (id: string) => ({
  id,
  name: id,
  type: "land",
  supplyCenter: false,
  parentId: null,
  namedCoastIds: [],
});

const lon = makeProvince("lon");
const nth = makeProvince("nth");

const mockVariant = {
  id: "standard",
  name: "Standard",
  description: "",
  rules: "",
  victoryConditions: {
    soloVictorySupplyCenters: 18,
    gameEndsYear: null,
    drawAfterYear: null,
  },
  nations: [england],
  provinces: [lon, nth],
  templatePhase: {},
};

const mockGame = {
  id: "game-1",
  variantId: "standard",
  name: "Test Game",
  status: "active",
  createdAt: "",
  canJoin: false,
  canLeave: false,
  canDelete: false,
  phases: [1],
  currentPhaseId: 1,
  members: [] as { nation: string; civilDisorder: boolean; kicked: boolean }[],
  sandbox: false,
  victory: null,
  phaseConfirmed: false,
  movementPhaseDuration: null,
  retreatPhaseDuration: null,
  private: false,
  anonymous: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 0,
  deadlineMode: "auto",
  fixedDeadlineTime: null,
};

const mockPhase = {
  id: 1,
  ordinal: 1,
  season: "Spring",
  year: 1901,
  name: "Spring 1901",
  type: "movement",
  remainingTime: 0,
  scheduledResolution: "",
  status: "active",
  units: [
    {
      type: "Army",
      nation: england,
      province: lon,
      dislodged: false,
      dislodgedFrom: null,
    },
  ],
  supplyCenters: [],
  previousPhaseId: null,
  nextPhaseId: null,
};

// --- Test helpers ---
const makeQueryClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false } } });

const gameMapJsx = (queryClient = makeQueryClient()) => (
  <QueryClientProvider client={queryClient}>
    <MemoryRouter initialEntries={["/game/game-1/phase/1"]}>
      <Routes>
        <Route path="/game/:gameId/phase/:phaseId" element={<GameMap />} />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>
);

const LocationProbe = () => {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}{location.search}</div>;
};

// Re-sets ?source=<provinceId>, mirroring how OrdersScreen re-triggers order
// creation for a province the player has already selected once this session.
const SetSourceButton = ({ provinceId }: { provinceId: string }) => {
  const [, setSearchParams] = useSearchParams();
  return (
    <button
      onClick={() =>
        setSearchParams(
          (prev) => {
            const next = new URLSearchParams(prev);
            next.set("source", provinceId);
            return next;
          },
          { replace: true }
        )
      }
    >
      Set source
    </button>
  );
};

const gameMapJsxAt = (initialEntry: string, queryClient = makeQueryClient()) => (
  <QueryClientProvider client={queryClient}>
    <MemoryRouter initialEntries={[initialEntry]}>
      <LocationProbe />
      <SetSourceButton provinceId="lon" />
      <Routes>
        <Route path="/game/:gameId/phase/:phaseId" element={<GameMap />} />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>
);

function completeWizard() {
  mockWizardState = {
    ...mockWizardState,
    isComplete: true,
    selectedArray: ["lon", "Move", "nth"],
    resolvedSelections: { source: "lon", orderType: "Move", target: "nth" },
    resolvedLabels: { source: "London", orderType: "Move", target: "North Sea" },
  };
}

function getLastOrdersProp(): Order[] {
  const last = mockMapView.mock.calls.at(-1);
  if (!last) return [];
  const props = (last[0] as unknown) as { orders: Order[] };
  return props.orders ?? [];
}

function getLastCivilDisorderNationsProp(): string[] {
  const last = mockMapView.mock.calls.at(-1);
  if (!last) return [];
  const props = (last[0] as unknown) as { civilDisorderNations: string[] };
  return props.civilDisorderNations ?? [];
}

// --- Tests ---
describe("GameMap", () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
    mockMutateAsync = vi.fn();
    mockExistingOrders = [];
    mockWizardState = buildIdleWizard();
    mockPublishedVariants = [mockVariant];
    mockRetrievedVariant = undefined;
    mockGame.members = [];
  });

  it("stops shading a nation in civil disorder once its member has been replaced", async () => {
    mockGame.members = [
      { nation: "England", civilDisorder: true, kicked: true },
      { nation: "England", civilDisorder: false, kicked: false },
    ];

    render(gameMapJsx());

    await waitFor(() => expect(mockMapView).toHaveBeenCalled());
    expect(getLastCivilDisorderNationsProp()).toEqual([]);
  });

  it("renders the map using a fetched draft variant when it is absent from the published list", async () => {
    mockPublishedVariants = [];
    mockRetrievedVariant = mockVariant;

    render(gameMapJsx());

    await waitFor(() => {
      expect(mockMapView).toHaveBeenCalled();
    });

    const props = mockMapView.mock.calls.at(-1)?.[0] as { variant: { id: string } };
    expect(props.variant.id).toBe("standard");
  });

  describe("optimistic order rendering", () => {
    it("passes pending order to the map immediately when wizard completes", async () => {
      let resolveOrder!: (order: Order) => void;
      mockMutateAsync.mockReturnValue(
        new Promise<Order>((res) => {
          resolveOrder = res;
        })
      );

      const { rerender } = render(gameMapJsx());

      completeWizard();
      rerender(gameMapJsx());

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });

      const orders = getLastOrdersProp();
      expect(orders).toHaveLength(1);
      expect(orders[0].source.id).toBe("lon");
      expect(orders[0].target!.id).toBe("nth");
      expect(orders[0].orderType).toBe("Move");

      // Resolve so the promise doesn't leave unhandled rejection
      resolveOrder({ title: "Army London → North Sea" } as unknown as Order);
    });

    it("shows success toast after mutation resolves and clears pending order", async () => {
      mockMutateAsync.mockResolvedValue({
        title: "Army London → North Sea",
      } as unknown as Order);

      const { rerender } = render(gameMapJsx());

      completeWizard();
      rerender(gameMapJsx());

      await waitFor(() => {
        expect(mockToastSuccess).toHaveBeenCalledWith(
          "Army London → North Sea"
        );
      });

      expect(mockWizardReset).toHaveBeenCalled();

      // After success the pending order must be gone from the displayed list
      const orders = getLastOrdersProp();
      expect(
        orders.some((o) => o.source?.id === "lon" && o.orderType === "Move")
      ).toBe(false);
    });

    it("hides the old order for the same source while the pending order is shown", async () => {
      const existingHoldOrder = {
        source: lon,
        target: lon,
        aux: lon,
        namedCoast: lon,
        sourceCoast: null,
        orderType: "Hold",
        unitType: "Army",
        nation: england,
        resolution: { status: "Succeeded", by: null },
        complete: null,
        step: null,
        title: "Army London hold",
        summary: null,
      } as unknown as Order;

      mockExistingOrders = [existingHoldOrder];

      let resolveOrder!: (order: Order) => void;
      mockMutateAsync.mockReturnValue(
        new Promise<Order>((res) => {
          resolveOrder = res;
        })
      );

      const { rerender } = render(gameMapJsx());

      completeWizard();
      rerender(gameMapJsx());

      await waitFor(() => expect(mockMutateAsync).toHaveBeenCalled());

      // During the pending mutation, only the new pending order should be shown
      // for the "lon" source — the old Hold order must be hidden
      const ordersWhilePending = getLastOrdersProp();
      const lonOrders = ordersWhilePending.filter((o) => o.source.id === "lon");
      expect(lonOrders).toHaveLength(1);
      expect(lonOrders[0].orderType).toBe("Move");

      resolveOrder({ title: "Army London → North Sea" } as unknown as Order);
    });

    it("replaces the old order in the cache when mutation succeeds", async () => {
      const existingHoldOrder = {
        source: lon,
        target: lon,
        aux: lon,
        namedCoast: lon,
        sourceCoast: null,
        orderType: "Hold",
        unitType: "Army",
        nation: england,
        resolution: { status: "Succeeded", by: null },
        complete: null,
        step: null,
        title: "Army London hold",
        summary: null,
      } as unknown as Order;

      mockExistingOrders = [existingHoldOrder];

      const realNewOrder = {
        ...existingHoldOrder,
        orderType: "Move",
        target: nth,
        title: "Army London → North Sea",
      } as unknown as Order;

      mockMutateAsync.mockResolvedValue(realNewOrder);

      const queryClient = makeQueryClient();
      queryClient.setQueryData(
        ["/game/game-1/orders/1"],
        mockExistingOrders
      );

      const { rerender } = render(gameMapJsx(queryClient));

      completeWizard();
      rerender(gameMapJsx(queryClient));

      await waitFor(() =>
        expect(mockToastSuccess).toHaveBeenCalledWith("Army London → North Sea")
      );

      const cached = queryClient.getQueryData<Order[]>([
        "/game/game-1/orders/1",
      ]);
      expect(cached).toHaveLength(1);
      expect(cached![0].orderType).toBe("Move");
    });

    it("shows error toast and removes pending order when mutation rejects", async () => {
      mockMutateAsync.mockRejectedValue(new Error("Network error"));

      const { rerender } = render(gameMapJsx());

      completeWizard();
      rerender(gameMapJsx());

      await waitFor(() => {
        expect(mockToastError).toHaveBeenCalledWith("Failed to create order");
      });

      expect(mockWizardReset).toHaveBeenCalled();

      // After failure the pending order must be gone
      const orders = getLastOrdersProp();
      expect(
        orders.some((o) => o.source?.id === "lon" && o.orderType === "Move")
      ).toBe(false);
    });
  });

  describe("source search param", () => {
    it("selects the province, pans without zooming, and clears the param when it is a valid source choice", async () => {
      mockWizardState = {
        ...mockWizardState,
        nextField: "source",
        choices: [{ id: "lon", label: "London" }],
      };

      const { getByTestId } = render(
        gameMapJsxAt("/game/game-1/phase/1?source=lon")
      );

      await waitFor(() => expect(mockWizardState.select).toHaveBeenCalledWith("lon"));

      const props = mockMapView.mock.calls.at(-1)?.[0] as {
        focus?: string[];
        focusKeepZoom?: boolean;
      };
      expect(props.focus).toEqual(["lon"]);
      expect(props.focusKeepZoom).toBe(true);

      await waitFor(() =>
        expect(getByTestId("location")).toHaveTextContent("/game/game-1/phase/1")
      );
      expect(getByTestId("location")).not.toHaveTextContent("source=lon");
    });

    it("pans again when the same province is selected a second time", async () => {
      mockWizardState = {
        ...mockWizardState,
        nextField: "source",
        choices: [{ id: "lon", label: "London" }],
      };

      const { getByTestId, getByText } = render(
        gameMapJsxAt("/game/game-1/phase/1?source=lon")
      );

      await waitFor(() => expect(mockWizardState.select).toHaveBeenCalledWith("lon"));
      const firstToken = (
        mockMapView.mock.calls.at(-1)?.[0] as { focusToken?: number }
      ).focusToken;
      await waitFor(() =>
        expect(getByTestId("location")).not.toHaveTextContent("source=lon")
      );

      // Simulate the player re-picking the same "Order not provided" row a
      // second time, e.g. after cancelling the first order-creation attempt.
      await userEvent.click(getByText("Set source"));

      await waitFor(() => {
        const latestToken = (
          mockMapView.mock.calls.at(-1)?.[0] as { focusToken?: number }
        ).focusToken;
        expect(latestToken).not.toBe(firstToken);
      });
    });

    it("ignores and clears an invalid source param without selecting it", async () => {
      mockWizardState = {
        ...mockWizardState,
        nextField: "source",
        choices: [{ id: "lon", label: "London" }],
      };

      const { getByTestId } = render(
        gameMapJsxAt("/game/game-1/phase/1?source=unknown")
      );

      await waitFor(() =>
        expect(getByTestId("location")).not.toHaveTextContent("source=unknown")
      );
      expect(mockWizardState.select).not.toHaveBeenCalled();
    });
  });
});
