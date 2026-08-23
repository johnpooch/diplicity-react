import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { NationPreferenceContent } from "./NationPreferenceContent";

const mockPreferenceMutateAsync = vi.fn();
const mockPreferenceRetrieve = vi.fn();

const nations = ["Austria", "England", "France"].map(name => ({
  nationId: name.toLowerCase(),
  name,
  color: "#cccccc",
  nonPlayable: false,
  flagUrl: null,
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { id: "pending-1", status: "pending", variantId: "classical", members: [] },
  }),
  useGameMemberNationPreferenceRetrieveSuspense: () => ({
    data: mockPreferenceRetrieve(),
  }),
  useGameMemberNationPreferenceUpdate: () => ({
    mutateAsync: mockPreferenceMutateAsync,
    isPending: false,
  }),
  useVariantsListSuspense: () => ({
    data: [{ id: "classical", name: "Classical", nations }],
  }),
  useVariantsRetrieve: () => ({ data: undefined }),
  getGameRetrieveQueryKey: (gameId: string) => ["games", gameId],
  getGameMemberNationPreferenceRetrieveQueryKey: (gameId: string) => [
    "nation-preference",
    gameId,
  ],
}));

const renderContent = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/nation-preference/pending-1"]}>
        <Routes>
          <Route
            path="/nation-preference/:gameId"
            element={<NationPreferenceContent />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("NationPreferenceContent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPreferenceRetrieve.mockReturnValue({ nationIds: [] });
    mockPreferenceMutateAsync.mockResolvedValue({});
  });

  it("assigns ranks in tap order", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(screen.getByRole("button", { name: /england/i }));
    await user.click(screen.getByRole("button", { name: /austria/i }));

    expect(
      within(screen.getByRole("button", { name: /england/i })).getByText("1")
    ).toBeInTheDocument();
    expect(
      within(screen.getByRole("button", { name: /austria/i })).getByText("2")
    ).toBeInTheDocument();
  });

  it("removes a ranked nation and renumbers the rest", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(screen.getByRole("button", { name: /england/i }));
    await user.click(screen.getByRole("button", { name: /austria/i }));
    await user.click(screen.getByRole("button", { name: /england/i }));

    const englandRow = screen.getByRole("button", { name: /england/i });
    expect(within(englandRow).queryByText(/^\d$/)).not.toBeInTheDocument();
    expect(
      within(screen.getByRole("button", { name: /austria/i })).getByText("1")
    ).toBeInTheDocument();
  });

  it("saves the ranked list in order", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(screen.getByRole("button", { name: /france/i }));
    await user.click(screen.getByRole("button", { name: /england/i }));
    await user.click(screen.getByRole("button", { name: /save preferences/i }));

    expect(mockPreferenceMutateAsync).toHaveBeenCalledWith({
      gameId: "pending-1",
      data: { nationIds: ["france", "england"] },
    });
  });

  it("submits an empty list as no preference", async () => {
    const user = userEvent.setup();
    renderContent();

    await user.click(screen.getByRole("button", { name: /save preferences/i }));

    expect(mockPreferenceMutateAsync).toHaveBeenCalledWith({
      gameId: "pending-1",
      data: { nationIds: [] },
    });
  });

  it("loads the existing ranking", async () => {
    mockPreferenceRetrieve.mockReturnValue({ nationIds: ["france"] });
    renderContent();

    expect(
      within(screen.getByRole("button", { name: /france/i })).getByText("1")
    ).toBeInTheDocument();
  });
});
