import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

import { DrawProposalsScreen } from "./DrawProposalsScreen";

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
const mockProposalsData = vi.fn();

const mockVariantsData = vi.fn();
const mockVoteMutation = vi.fn();
const mockCancelMutation = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({ data: mockGameData() }),
  useGamesDrawProposalsListSuspense: () => ({ data: mockProposalsData() }),
  useVariantsListSuspense: () => ({ data: mockVariantsData() }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamesDrawProposalsVotePartialUpdate: () => ({
    mutateAsync: mockVoteMutation,
    isPending: false,
  }),
  useGamesDrawProposalsCancelDestroy: () => ({
    mutateAsync: mockCancelMutation,
    isPending: false,
  }),
  getGamesDrawProposalsListQueryKey: () => ["drawList"],
  getGameRetrieveQueryKey: () => ["game"],
}));

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => null,
  findNationFlagUrl: () => null,
  findNationColor: () => null,
  getContrastColor: () => "#ffffff",
}));

const baseMember = (overrides = {}) => ({
  id: 1,
  name: "Alice",
  picture: null,
  isCurrentUser: false,
  nation: "England",
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  ...overrides,
});

const baseProposal = (overrides = {}) => ({
  id: 1,
  status: "pending" as const,
  createdBy: {
    id: 1,
    name: "Alice",
    picture: null,
    isCurrentUser: false,
    nation: "England",
  },
  acceptedCount: 1,
  rejectedCount: 0,
  pendingCount: 1,
  totalVotes: 2,
  includedMemberIds: [1, 2],
  myVote: { included: true, accepted: null },
  phaseId: 1,
  phaseName: "Spring 1901, Movement",
  createdAt: "2025-01-01T00:00:00Z",
  ...overrides,
});

const renderScreen = (initialPath = "/game/g1/phase/1/draw-proposals") => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/draw-proposals"
            element={<DrawProposalsScreen />}
          />
          <Route
            path="/game/:gameId/phase/:phaseId/propose-draw"
            element={<div>Propose draw screen</div>}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("DrawProposalsScreen", () => {
  beforeEach(() => {
    mockVoteMutation.mockReset();
    mockVoteMutation.mockResolvedValue({});
    mockCancelMutation.mockReset();
    mockCancelMutation.mockResolvedValue({});
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical" }]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      sandbox: false,
      status: "active",
      phases: [1],
      members: [
        baseMember({
          id: 1,
          name: "Alice",
          nation: "England",
          isCurrentUser: false,
        }),
        baseMember({
          id: 2,
          name: "Bob",
          nation: "France",
          isCurrentUser: true,
        }),
      ],
    });
  });

  it("shows the tally and vote buttons on a proposal awaiting the current user's vote", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();

    expect(screen.getByText("Draw proposed by England")).toBeInTheDocument();
    expect(screen.getByText("1 of 2 accepted")).toBeInTheDocument();
    expect(
      screen.getByText("Expires when the phase resolves")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^accept$/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^reject$/i })
    ).toBeInTheDocument();
  });

  it("does not list the nations in the draw or per-voter details", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();

    expect(screen.queryByText("England, France")).not.toBeInTheDocument();
    expect(screen.queryByText(/your vote/i)).not.toBeInTheDocument();
  });

  it("shows who is still to vote once the current user has voted", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        myVote: { included: true, accepted: true },
        acceptedCount: 2,
        pendingCount: 1,
        totalVotes: 3,
      }),
    ]);

    renderScreen();

    expect(screen.getByText("Waiting for 1 player")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^accept$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^reject$/i })
    ).not.toBeInTheDocument();
  });

  it("asks for confirmation before accepting", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({ pendingCount: 2, totalVotes: 3 }),
    ]);

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /^accept$/i }));

    expect(mockVoteMutation).not.toHaveBeenCalled();
    expect(screen.getByRole("alertdialog")).toHaveTextContent(
      "If every player accepts, the game ends in a draw"
    );

    fireEvent.click(
      within(screen.getByRole("alertdialog")).getByRole("button", {
        name: "Accept",
      })
    );

    expect(mockVoteMutation).toHaveBeenCalledWith({
      gameId: "g1",
      proposalId: 1,
      data: { accepted: true },
    });
  });

  it("warns the last player to vote that accepting ends the game", () => {
    mockProposalsData.mockReturnValue([baseProposal({ pendingCount: 1 })]);

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /^accept$/i }));

    expect(screen.getByRole("alertdialog")).toHaveTextContent(
      "The game ends now"
    );
  });

  it("asks for confirmation before rejecting", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /^reject$/i }));
    fireEvent.click(
      within(screen.getByRole("alertdialog")).getByRole("button", {
        name: "Reject",
      })
    );

    expect(mockVoteMutation).toHaveBeenCalledWith({
      gameId: "g1",
      proposalId: 1,
      data: { accepted: false },
    });
  });

  it("does not vote when the confirmation is dismissed", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /^accept$/i }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(mockVoteMutation).not.toHaveBeenCalled();
  });

  it("lets the proposer cancel their pending proposal", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        createdBy: {
          id: 2,
          name: "Bob",
          picture: null,
          isCurrentUser: true,
          nation: "France",
        },
        myVote: { included: true, accepted: true },
      }),
    ]);

    renderScreen();

    expect(screen.getByText("Draw proposed by you")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cancel proposal" }));

    expect(mockCancelMutation).toHaveBeenCalledWith({
      gameId: "g1",
      proposalId: 1,
    });
  });

  it("lists every proposal in one list in the order received", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({ id: 4, status: "pending" as const }),
      baseProposal({
        id: 3,
        status: "cancelled" as const,
        phaseName: "Fall 1901, Movement",
      }),
      baseProposal({
        id: 2,
        status: "rejected" as const,
        phaseName: "Spring 1901, Movement",
      }),
      baseProposal({
        id: 1,
        status: "expired" as const,
        phaseName: "Fall 1900, Movement",
      }),
    ]);

    renderScreen();

    const titles = screen
      .getAllByText(/^Draw (proposed|cancelled|rejected|expired)/)
      .map(element => element.textContent);
    expect(titles).toEqual([
      "Draw proposed by England",
      "Draw cancelled",
      "Draw rejected",
      "Draw expired",
    ]);
    expect(screen.getByText("Fall 1901, Movement")).toBeInTheDocument();
    expect(screen.getByText("Spring 1901, Movement")).toBeInTheDocument();
    expect(screen.getByText("Fall 1900, Movement")).toBeInTheDocument();
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  });

  it("does not offer voting on a proposal that is no longer pending", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({ status: "expired" as const }),
    ]);

    renderScreen();

    expect(
      screen.queryByRole("button", { name: /^accept$/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Expires when the phase resolves")
    ).not.toBeInTheDocument();
  });

  it("shows an accepted proposal without the tally or phase", () => {
    mockGameData.mockReturnValue({ ...mockGameData(), status: "completed" });
    mockProposalsData.mockReturnValue([
      baseProposal({
        status: "accepted" as const,
        acceptedCount: 2,
        pendingCount: 0,
        myVote: { included: true, accepted: true },
      }),
    ]);

    renderScreen();

    expect(screen.getByText("Draw accepted")).toBeInTheDocument();
    expect(screen.getByText("The game ended in a draw")).toBeInTheDocument();
    expect(screen.queryByText(/of \d+ accepted/)).not.toBeInTheDocument();
    expect(screen.queryByText("Spring 1901, Movement")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /propose draw/i })
    ).not.toBeInTheDocument();
  });

  it("offers to propose a draw when no proposal is pending", () => {
    mockProposalsData.mockReturnValue([]);

    renderScreen();

    expect(screen.getByText("No draw proposals")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "Propose Draw" }));

    expect(screen.getByText("Propose draw screen")).toBeInTheDocument();
  });

  it("does not offer to propose a draw while one is pending", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();

    expect(
      screen.queryByRole("link", { name: /propose draw/i })
    ).not.toBeInTheDocument();
  });

  it("does not offer to propose a draw after the current user's proposal this phase was rejected", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        status: "rejected" as const,
        createdBy: {
          id: 2,
          name: "Bob",
          picture: null,
          isCurrentUser: true,
          nation: "France",
        },
      }),
    ]);

    renderScreen();

    expect(
      screen.queryByRole("link", { name: /propose draw/i })
    ).not.toBeInTheDocument();
  });

  it("offers to propose a draw again after the current user cancels their proposal", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        status: "cancelled" as const,
        createdBy: {
          id: 2,
          name: "Bob",
          picture: null,
          isCurrentUser: true,
          nation: "France",
        },
      }),
    ]);

    renderScreen();

    expect(
      screen.getByRole("link", { name: "Propose Draw" })
    ).toBeInTheDocument();
  });
});
