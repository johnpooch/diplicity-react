import { act, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { AxiosRequestConfig } from "axios";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

import {
  getGameOptionsRetrieveQueryKey,
  getGamePhaseStatesListQueryKey,
  getGameRetrieveQueryKey,
  type OrderOptionsResponse,
  type PhaseState,
} from "@/api/generated/endpoints";
import { MapScreen } from "./MapScreen";
import { OrdersScreen } from "./OrdersScreen";

const { mockRequest, mockMapView } = vi.hoisted(() => ({
  mockRequest: vi.fn(),
  mockMapView: vi.fn(),
}));

vi.mock("@/api/axiosInstance", () => ({ customInstance: mockRequest }));

vi.mock("@/components/MapView", () => ({
  MapView: (props: unknown) => {
    mockMapView(props);
    return <div data-testid="map" />;
  },
}));
vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
}));
vi.mock("@/components/PhaseStepper", () => ({
  PhaseStepperTitle: () => null,
  PhaseStepperActions: () => null,
}));

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

const makeProvince = (id: string, name: string) => ({
  id,
  name,
  type: "land",
  supplyCenter: false,
  parentId: null,
  namedCoastIds: [],
});

const london = makeProvince("lon", "London");
const edinburgh = makeProvince("edi", "Edinburgh");
const england = { name: "England", color: "#ff0000" };

const member = {
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
};

const unitProvinceByPhase: Record<number, typeof london> = {
  1: london,
  2: edinburgh,
  3: london,
};

let currentPhaseId = 1;

const serve = (config: AxiosRequestConfig) => {
  const url = config.url ?? "";
  const phaseMatch = url.match(/^\/game\/game-1\/phase\/(\d+)\/$/);
  if (url === "/game/game-1/") {
    return {
      id: "game-1",
      variantId: "classical",
      status: "active",
      sandbox: false,
      phaseConfirmed: false,
      currentPhaseId,
      members: [member],
    };
  }
  if (phaseMatch) {
    const id = Number(phaseMatch[1]);
    return {
      id,
      name: `Phase ${id}`,
      status: id === currentPhaseId ? "active" : "completed",
      supplyCenters: [],
      units: [
        {
          type: "Army",
          dislodged: false,
          nation: england,
          province: unitProvinceByPhase[id],
        },
      ],
    };
  }
  if (url === "/game/game-1/phase-states/") {
    return [
      {
        id: `ps-${currentPhaseId}`,
        ordersConfirmed: false,
        eliminated: false,
        maxOrders: null,
        member,
        orderableProvinces: [unitProvinceByPhase[currentPhaseId]],
      },
    ];
  }
  if (url === "/game/game-1/options/") {
    const source = unitProvinceByPhase[currentPhaseId];
    return {
      orders: ["Hold", "Move"].map(orderType => ({
        source: { id: source.id, label: source.name },
        orderType: { id: orderType, label: orderType },
        target: null,
        aux: null,
        unitType: null,
        namedCoast: null,
      })),
      fieldOrder: { Hold: ["source", "orderType"], Move: ["source", "orderType"] },
    };
  }
  if (url === "/variants/") {
    return [
      {
        id: "classical",
        name: "Classical",
        nations: [england],
        provinces: [london, edinburgh],
      },
    ];
  }
  if (url.startsWith("/game/game-1/orders/") || url.endsWith("/draw-proposals/")) {
    return [];
  }
  throw new Error(`Unexpected request ${config.method ?? "GET"} ${url}`);
};

const requestsTo = (url: string) =>
  mockRequest.mock.calls.filter(([config]) => config.url === url);

const lastMapViewProps = () =>
  mockMapView.mock.calls.at(-1)?.[0] as {
    phase: { id: number };
    selected: string[];
    onClickProvince: (province: string, position: { x: number; y: number }) => void;
  };

const renderAt = (path: string, element: React.ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createMemoryRouter(
    [
      { path: "/game/:gameId/phase/:phaseId", element },
      { path: "/game/:gameId/phase/:phaseId/orders", element },
    ],
    { initialEntries: [path] }
  );
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
  return { queryClient, router };
};

const advanceCurrentPhase = async (queryClient: QueryClient, phaseId: number) => {
  currentPhaseId = phaseId;
  await act(() =>
    queryClient.refetchQueries({ queryKey: getGameRetrieveQueryKey("game-1") })
  );
};

describe("current-phase-only resources", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentPhaseId = 1;
    mockRequest.mockImplementation(async (config: AxiosRequestConfig) => serve(config));
  });

  it("loads fresh phase states under a new cache key when the current phase advances", async () => {
    const { queryClient, router } = renderAt(
      "/game/game-1/phase/1/orders",
      <OrdersScreen />
    );
    expect(await screen.findByText("Army London")).toBeInTheDocument();

    await advanceCurrentPhase(queryClient, 2);
    await act(() => router.navigate("/game/game-1/phase/2/orders"));

    expect(await screen.findByText("Army Edinburgh")).toBeInTheDocument();
    expect(requestsTo("/game/game-1/phase-states/")).toHaveLength(2);
    const phaseStatesKey = getGamePhaseStatesListQueryKey("game-1");
    expect(
      queryClient.getQueryData<PhaseState[]>([...phaseStatesKey, 1])?.[0].id
    ).toBe("ps-1");
    expect(
      queryClient.getQueryData<PhaseState[]>([...phaseStatesKey, 2])?.[0].id
    ).toBe("ps-2");
  });

  it("loads fresh order options under a new cache key when the current phase advances", async () => {
    const { queryClient, router } = renderAt("/game/game-1/phase/1", <MapScreen />);
    await waitFor(() => expect(requestsTo("/game/game-1/options/")).toHaveLength(1));

    await advanceCurrentPhase(queryClient, 2);
    await act(() => router.navigate("/game/game-1/phase/2"));

    await waitFor(() => expect(requestsTo("/game/game-1/options/")).toHaveLength(2));
    const optionsKey = getGameOptionsRetrieveQueryKey("game-1");
    await waitFor(() =>
      expect(
        queryClient.getQueryData<OrderOptionsResponse>([...optionsKey, 2])
          ?.orders[0].source?.id
      ).toBe("edi")
    );
    expect(
      queryClient.getQueryData<OrderOptionsResponse>([...optionsKey, 1])
        ?.orders[0].source?.id
    ).toBe("lon");
  });

  it("does not fetch phase states while navigating among historical phases on the orders screen", async () => {
    currentPhaseId = 3;
    const { router } = renderAt("/game/game-1/phase/1/orders", <OrdersScreen />);
    expect(await screen.findByText("Army London")).toBeInTheDocument();

    await act(() => router.navigate("/game/game-1/phase/2/orders"));

    expect(await screen.findByText("Army Edinburgh")).toBeInTheDocument();
    expect(requestsTo("/game/game-1/phase-states/")).toHaveLength(0);
    expect(screen.queryByLabelText(/Delete order for/)).not.toBeInTheDocument();
  });

  it("does not fetch options or phase states while navigating among historical phases on the map", async () => {
    currentPhaseId = 3;
    const { router } = renderAt("/game/game-1/phase/1", <MapScreen />);
    await waitFor(() => expect(lastMapViewProps()?.phase.id).toBe(1));

    await act(() => router.navigate("/game/game-1/phase/2"));

    await waitFor(() => expect(lastMapViewProps().phase.id).toBe(2));
    expect(requestsTo("/game/game-1/options/")).toHaveLength(0);
    expect(requestsTo("/game/game-1/phase-states/")).toHaveLength(0);
  });

  it("resets the order wizard and cannot create orders on a historical map", async () => {
    currentPhaseId = 3;
    const { router } = renderAt("/game/game-1/phase/3", <MapScreen />);
    await waitFor(() => expect(requestsTo("/game/game-1/options/")).toHaveLength(1));
    await waitFor(() => expect(lastMapViewProps()?.phase.id).toBe(3));

    await waitFor(() => {
      act(() => lastMapViewProps().onClickProvince("lon", { x: 10, y: 10 }));
      expect(screen.getByText("Hold")).toBeInTheDocument();
    });

    await act(() => router.navigate("/game/game-1/phase/1"));
    await waitFor(() => expect(lastMapViewProps().phase.id).toBe(1));
    expect(screen.queryByText("Hold")).not.toBeInTheDocument();

    act(() => lastMapViewProps().onClickProvince("lon", { x: 10, y: 10 }));

    expect(screen.queryByText("Hold")).not.toBeInTheDocument();
    expect(lastMapViewProps().selected).toEqual([]);

    await act(() => router.navigate("/game/game-1/phase/3"));
    await waitFor(() => expect(lastMapViewProps().phase.id).toBe(3));
    expect(screen.queryByText("Hold")).not.toBeInTheDocument();
    expect(
      mockRequest.mock.calls.filter(([config]) => config.method === "POST")
    ).toHaveLength(0);
  });
});
