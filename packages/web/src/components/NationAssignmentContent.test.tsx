import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { NationAssignmentContent } from "./NationAssignmentContent";

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}

const mockAssignMutateAsync = vi.fn();
const mockClearMutateAsync = vi.fn();

const nations = ["Austria", "England", "France"].map(name => ({
  nationId: name.toLowerCase(),
  name,
  color: "#cccccc",
  nonPlayable: false,
  flagUrl: null,
}));

const members = [
  { id: 1, name: "Alice", picture: null, nation: "England" },
  { id: 2, name: "Bob", picture: null, nation: null },
];

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      id: "pending-1",
      status: "pending",
      variantId: "classical",
      members,
    },
  }),
  useGameMemberNationUpdate: () => ({
    mutateAsync: mockAssignMutateAsync,
    isPending: false,
  }),
  useGameMemberNationDestroy: () => ({
    mutateAsync: mockClearMutateAsync,
    isPending: false,
  }),
  useVariantsListSuspense: () => ({
    data: [{ id: "classical", name: "Classical", nations }],
  }),
  useVariantsRetrieve: () => ({ data: undefined }),
  getGameRetrieveQueryKey: (gameId: string) => ["games", gameId],
}));

const renderContent = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/nation-assignment/pending-1"]}>
        <Routes>
          <Route
            path="/nation-assignment/:gameId"
            element={<NationAssignmentContent />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("NationAssignmentContent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAssignMutateAsync.mockResolvedValue({});
    mockClearMutateAsync.mockResolvedValue({});
  });

  it("disables nations pinned to another member", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(
      screen.getByRole("combobox", { name: /nation for bob/i })
    );

    expect(
      screen.getByRole("option", { name: /england \(assigned\)/i })
    ).toHaveAttribute("aria-disabled", "true");
    expect(
      screen.getByRole("option", { name: /^france$/i })
    ).not.toHaveAttribute("aria-disabled", "true");
  });

  it("fires one assign request when a nation is picked", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(
      screen.getByRole("combobox", { name: /nation for bob/i })
    );
    await user.click(screen.getByRole("option", { name: /^france$/i }));

    expect(mockAssignMutateAsync).toHaveBeenCalledTimes(1);
    expect(mockAssignMutateAsync).toHaveBeenCalledWith({
      gameId: "pending-1",
      memberId: 2,
      data: { nationId: "france" },
    });
    expect(mockClearMutateAsync).not.toHaveBeenCalled();
  });

  it("fires a clear request when a pinned member is set to unassigned", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(
      screen.getByRole("combobox", { name: /nation for alice/i })
    );
    await user.click(screen.getByRole("option", { name: /unassigned/i }));

    expect(mockClearMutateAsync).toHaveBeenCalledTimes(1);
    expect(mockClearMutateAsync).toHaveBeenCalledWith({
      gameId: "pending-1",
      memberId: 1,
    });
    expect(mockAssignMutateAsync).not.toHaveBeenCalled();
  });
});
