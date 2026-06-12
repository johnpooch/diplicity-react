import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

import { ProposeDrawScreen } from "./ProposeDrawScreen";

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
const mockVariantsData = vi.fn();
const mockCreateMutation = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useGamesDrawProposalsCreateCreate: () => ({
    mutateAsync: mockCreateMutation,
    isPending: false,
  }),
  getGamesDrawProposalsListQueryKey: () => ["drawList"],
}));

vi.mock("@/components/NationFlag", () => ({ NationFlag: () => null, findNationFlagUrl: () => null, findNationColor: () => null }));

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

const renderScreen = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/game/g1/phase/1/propose-draw"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/propose-draw"
            element={<ProposeDrawScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("ProposeDrawScreen (DIAS)", () => {
  beforeEach(() => {
    mockCreateMutation.mockReset();
    mockCreateMutation.mockResolvedValue({});
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
  });

  it("lists all active non-CD members as included", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      members: [
        baseMember({ id: 1, nation: "England", civilDisorder: false }),
        baseMember({ id: 2, nation: "France", civilDisorder: false }),
      ],
    });

    renderScreen();

    expect(screen.getByText("England")).toBeInTheDocument();
    expect(screen.getByText("France")).toBeInTheDocument();
    expect(screen.queryByText("Civil Disorder")).not.toBeInTheDocument();
  });

  it("shows CD members marked as excluded", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      members: [
        baseMember({ id: 1, nation: "England", civilDisorder: false }),
        baseMember({ id: 2, nation: "France", civilDisorder: true }),
      ],
    });

    renderScreen();

    expect(screen.getByText("Civil Disorder")).toBeInTheDocument();
    expect(screen.getByText(/excluded from draw victory/i)).toBeInTheDocument();
  });

  it("does not render any SC threshold UI", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      members: [baseMember({ id: 1, civilDisorder: false })],
    });

    renderScreen();

    expect(screen.queryByText(/combined sc/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/threshold/i)).not.toBeInTheDocument();
  });

  it("submits the create-proposal mutation with an empty body", () => {
    mockGameData.mockReturnValue({
      variantId: "classical",
      members: [baseMember({ id: 1, civilDisorder: false })],
    });

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /propose draw/i }));

    expect(mockCreateMutation).toHaveBeenCalledWith({
      gameId: "g1",
      data: {},
    });
  });
});
