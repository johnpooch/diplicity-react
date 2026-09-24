import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

import { MapScreen } from "./MapScreen";

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
const mockPhaseStatesData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamePhaseRetrieveSuspense: () => ({ data: mockPhaseData() }),
  useGameOrdersListSuspense: () => ({ data: mockOrdersData() }),
  useGamePhaseStatesListSuspense: () => ({ data: mockPhaseStatesData() }),
  useGameConfirmPhasePartialUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  getGameRetrieveQueryKey: () => ["game"],
  getGamePhaseStatesListQueryKey: () => ["phase-states"],
}));

vi.mock("@/components/GameMap", () => ({ GameMap: () => null }));
vi.mock("@/components/PhaseStepper", () => ({
  PhaseStepperTitle: () => null,
  PhaseStepperActions: () => null,
}));

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/1/phase/5"]}>
        <Routes>
          <Route path="/game/:gameId/phase/:phaseId" element={<MapScreen />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("MapScreen confirm orders button", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGameData.mockReturnValue({
      id: "1",
      currentPhaseId: 5,
      status: "active",
      sandbox: false,
      phaseConfirmed: false,
      members: [{ id: 1, isCurrentUser: true, civilDisorder: false }],
    });
    mockPhaseData.mockReturnValue({ status: "active" });
    mockOrdersData.mockReturnValue([{ source: { id: "lon" } }]);
    mockPhaseStatesData.mockReturnValue([
      {
        member: { isCurrentUser: true },
        maxOrders: null,
        orderableProvinces: [{ id: "lon" }, { id: "edi" }, { id: "lvp" }],
      },
    ]);
  });

  it("shows the submitted and required order counts", () => {
    renderScreen();
    expect(screen.getByRole("button", { name: "Confirm (1/3)" })).toBeInTheDocument();
  });

  it("reads as confirmed once orders are confirmed", () => {
    mockGameData.mockReturnValue({
      id: "1",
      currentPhaseId: 5,
      status: "active",
      sandbox: false,
      phaseConfirmed: true,
      members: [{ id: 1, isCurrentUser: true, civilDisorder: false }],
    });
    renderScreen();
    expect(screen.getByRole("button", { name: "Confirmed (1/3)" })).toBeInTheDocument();
  });

  it("hides the button on a historical phase without loading phase states", () => {
    mockGameData.mockReturnValue({
      id: "1",
      currentPhaseId: 6,
      status: "active",
      sandbox: false,
      phaseConfirmed: false,
      members: [{ id: 1, isCurrentUser: true, civilDisorder: false }],
    });
    mockPhaseData.mockReturnValue({ status: "completed" });
    renderScreen();
    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
    expect(mockPhaseStatesData).not.toHaveBeenCalled();
  });

  it("hides the button for a spectator", () => {
    mockGameData.mockReturnValue({
      id: "1",
      currentPhaseId: 5,
      status: "active",
      sandbox: false,
      phaseConfirmed: false,
      members: [{ id: 2, isCurrentUser: false, civilDisorder: false }],
    });
    renderScreen();
    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
  });

  it("hides the button when the user is in civil disorder", () => {
    mockGameData.mockReturnValue({
      id: "1",
      currentPhaseId: 5,
      status: "active",
      sandbox: false,
      phaseConfirmed: false,
      members: [{ id: 1, isCurrentUser: true, civilDisorder: true }],
    });
    renderScreen();
    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
  });

  it("hides the button when nothing is orderable", () => {
    mockPhaseStatesData.mockReturnValue([
      { member: { isCurrentUser: true }, maxOrders: null, orderableProvinces: [] },
    ]);
    renderScreen();
    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
  });
});
