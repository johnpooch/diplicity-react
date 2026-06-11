import { fireEvent, render, screen } from "@testing-library/react";
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

vi.mock("@/components/NationFlag", () => ({ NationFlag: () => null, findNationFlagUrl: () => null, findNationColor: () => null }));

const baseMember = (overrides = {}) => ({
  id: 1,
  name: "Alice",
  picture: null,
  isCurrentUser: false,
  nation: "England",
  eliminated: false,
  kicked: false,
  isGameMaster: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  ...overrides,
});

const baseProposal = (overrides = {}) => ({
  id: 1,
  status: "pending" as const,
  createdBy: { id: 1, name: "Alice", picture: null, isCurrentUser: false, nation: "England" },
  acceptedCount: 1,
  rejectedCount: 0,
  pendingCount: 1,
  totalVotes: 2,
  includedMemberIds: [1, 2],
  myVote: { included: true, accepted: null },
  phaseId: 1,
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
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("DrawProposalsScreen (secret voting)", () => {
  beforeEach(() => {
    mockVoteMutation.mockReset();
    mockVoteMutation.mockResolvedValue({});
    mockCancelMutation.mockReset();
    mockCancelMutation.mockResolvedValue({});
    mockVariantsData.mockReturnValue([{ id: "classical", name: "Classical", nations: [] }]);
    mockGameData.mockReturnValue({
      variantId: "classical",
      sandbox: false,
      status: "active",
      members: [
        baseMember({ id: 1, name: "Alice", nation: "England", isCurrentUser: false }),
        baseMember({ id: 2, name: "Bob", nation: "France", isCurrentUser: true }),
      ],
    });
  });

  it("renders a vote tally instead of per-voter icons", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();

    expect(screen.getByText(/1 of 2 accepted/i)).toBeInTheDocument();
    // We don't render any per-voter accepted/rejected status on the active proposal.
    // The current user can still see their own vote elsewhere, but no list of
    // individual member vote states should appear.
    expect(screen.queryByText(/your vote:/i)).not.toBeInTheDocument();
  });

  it("shows the current user's own vote when they have voted", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        myVote: { included: true, accepted: true },
        acceptedCount: 2,
        pendingCount: 0,
      }),
    ]);

    const { container } = renderScreen();

    expect(screen.getByText(/your vote:/i)).toBeInTheDocument();
    // The "Accepted" span lives in a colored marker inside "Your vote:" — find it
    // by class to disambiguate from the tally line.
    expect(container.querySelector(".text-green-600")?.textContent).toBe("Accepted");
  });

  it("shows accept/reject buttons only when current user has not voted", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({ myVote: { included: true, accepted: null } }),
    ]);

    renderScreen();

    expect(screen.getByRole("button", { name: /^accept$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^reject$/i })).toBeInTheDocument();
  });

  it("hides accept/reject buttons after current user votes", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({ myVote: { included: true, accepted: false } }),
    ]);

    renderScreen();

    expect(screen.queryByRole("button", { name: /^accept$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^reject$/i })).not.toBeInTheDocument();
  });

  it("rejected tab shows tally only, no per-voter details", () => {
    mockProposalsData.mockReturnValue([
      baseProposal({
        status: "rejected" as const,
        acceptedCount: 1,
        rejectedCount: 1,
        pendingCount: 0,
      }),
    ]);

    renderScreen("/game/g1/phase/1/draw-proposals?tab=rejected");

    expect(screen.getByText(/1 of 2 accepted/i)).toBeInTheDocument();
  });

  it("clicking Accept fires the vote mutation with accepted=true", () => {
    mockProposalsData.mockReturnValue([baseProposal()]);

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: /^accept$/i }));

    expect(mockVoteMutation).toHaveBeenCalledWith({
      gameId: "g1",
      proposalId: 1,
      data: { accepted: true },
    });
  });
});
