import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { FindGames } from "./FindGames";
import { useGamesListInfinite } from "@/hooks/useGamesListInfinite";

const mockFetchNextPage = vi.fn();
const mockSentinelRef = { current: null };

const defaultGamesListResult = {
  data: { pages: [{ results: [] }] },
  fetchNextPage: mockFetchNextPage,
  hasNextPage: false,
  isFetchingNextPage: false,
};

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal<
    typeof import("@/api/generated/endpoints")
  >();
  return {
    ...actual,
    useVariantsListSuspense: () => ({
      data: [
        { id: "classical", name: "Classical" },
        { id: "pure", name: "Pure" },
      ],
    }),
  };
});

vi.mock("@/hooks/useGamesListInfinite", () => ({
  useGamesListInfinite: vi.fn(() => defaultGamesListResult),
}));

vi.mock("@/hooks/useInfiniteScroll", () => ({
  useInfiniteScroll: () => mockSentinelRef,
}));

vi.mock("@/components/GameCard", () => ({
  GameCard: () => <div data-testid="game-card" />,
}));

vi.mock("@/components/UserAvatar", () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

const mockUseGamesListInfinite = vi.mocked(useGamesListInfinite);

const renderFindGames = (initialEntries = ["/"]) =>
  render(
    <MemoryRouter initialEntries={initialEntries}>
      <FindGames />
    </MemoryRouter>
  );

describe("FindGames", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGamesListInfinite.mockReturnValue(defaultGamesListResult);
  });

  it("shows the filter toggle button in the header", () => {
    renderFindGames();
    expect(
      screen.getByRole("button", { name: /toggle filters/i })
    ).toBeInTheDocument();
  });

  it("hides the filter panel by default", () => {
    renderFindGames();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("shows the filter panel when the toggle button is clicked", async () => {
    renderFindGames();

    await userEvent.click(
      screen.getByRole("button", { name: /toggle filters/i })
    );

    expect(screen.getAllByRole("combobox")).toHaveLength(2);
  });

  it("hides the filter panel when the toggle button is clicked twice", async () => {
    renderFindGames();

    const toggleButton = screen.getByRole("button", {
      name: /toggle filters/i,
    });

    await userEvent.click(toggleButton);
    expect(screen.getAllByRole("combobox")).toHaveLength(2);

    await userEvent.click(toggleButton);
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("passes can_join: true to the games list query", () => {
    renderFindGames();

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({ can_join: true })
    );
  });

  it("passes variant param from URL to the games list query", () => {
    renderFindGames(["/?variant=classical"]);

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({ can_join: true, variant: "classical" })
    );
  });

  it("passes movement_phase_duration param from URL to the games list query", () => {
    renderFindGames(["/?movement_phase_duration=24+hours"]);

    expect(mockUseGamesListInfinite).toHaveBeenCalledWith(
      expect.objectContaining({
        can_join: true,
        movement_phase_duration: "24 hours",
      })
    );
  });
});
