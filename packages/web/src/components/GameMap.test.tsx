import { render, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { GameMap } from "./GameMap";
import type { Order } from "@/api/generated/endpoints";

// vi.hoisted ensures these are initialized before vi.mock hoisting runs
const {
  mockToastSuccess,
  mockToastError,
  mockWizardReset,
  mockInteractiveMapZoomWrapper,
} = vi.hoisted(() => ({
  mockToastSuccess: vi.fn(),
  mockToastError: vi.fn(),
  mockWizardReset: vi.fn(),
  mockInteractiveMapZoomWrapper: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: mockToastSuccess, error: mockToastError },
}));

vi.mock("@/components/InteractiveMap/InteractiveMapZoomWrapper", () => ({
  InteractiveMapZoomWrapper: (props: unknown) => {
    mockInteractiveMapZoomWrapper(props);
    return <div data-testid="map" />;
  },
}));

// Wizard state is held in a mutable object the mock reads from each render
type WizardState = {
  isComplete: boolean;
  selectedArray: string[];
  resolvedSelections: Record<string, string>;
  nextField: string | null;
  choices: never[];
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

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieve: () => ({ data: mockGame }),
  useVariantsList: () => ({ data: [mockVariant] }),
  useGamePhaseRetrieve: () => ({ data: mockPhase }),
  useGameOrdersList: () => ({ data: mockExistingOrders }),
  useGameOptionsRetrieve: () => ({ data: { orders: [], fieldOrder: {} } }),
  useGameOrdersCreate: () => ({ mutateAsync: mockMutateAsync }),
  getGameOrdersListQueryKey: (gameId: string, phaseId: number) => [
    `/game/${gameId}/orders/${phaseId}`,
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
  soloVictoryScCount: 18,
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
  members: [],
  sandbox: false,
  victory: null,
  nationAssignment: "random",
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
      dislodgedBy: null,
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

function completeWizard() {
  mockWizardState = {
    ...mockWizardState,
    isComplete: true,
    selectedArray: ["lon", "Move", "nth"],
    resolvedSelections: { source: "lon", orderType: "Move", target: "nth" },
  };
}

function getLastOrdersProp(): Order[] {
  const last = mockInteractiveMapZoomWrapper.mock.calls.at(-1);
  if (!last) return [];
  const props = (last[0] as unknown) as { interactiveMapProps: { orders: Order[] } };
  return props.interactiveMapProps.orders ?? [];
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
      expect(orders[0].target.id).toBe("nth");
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
        options: [],
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
        options: [],
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
});
