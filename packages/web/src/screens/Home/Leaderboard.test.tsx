import { act, render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  LeaderboardEntry,
  PaginatedLeaderboardEntryList,
} from "@/api/generated/endpoints";
import { Leaderboard } from "./Leaderboard";

const leaderboardList = vi.fn<() => Promise<PaginatedLeaderboardEntryList>>();
let observerCallbacks: IntersectionObserverCallback[];

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  leaderboardList: () => leaderboardList(),
  useUserRetrieveSuspense: () => ({
    data: { id: 1, userId: 7, name: "Jane Doe", picture: null },
  }),
}));

const entry = (rank: number, userId: number, name: string, rating: number): LeaderboardEntry => ({
  rank,
  userId,
  name,
  picture: null,
  rating,
});

const page = (
  results: LeaderboardEntry[],
  own: LeaderboardEntry | null = null
): PaginatedLeaderboardEntryList => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  own,
});

const renderLeaderboard = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <Leaderboard />
      </MemoryRouter>
    </QueryClientProvider>
  );

const reportOwnRowVisible = (isIntersecting: boolean) =>
  act(() =>
    observerCallbacks.forEach(callback =>
      callback(
        [{ isIntersecting } as IntersectionObserverEntry],
        {} as IntersectionObserver
      )
    )
  );

describe("Leaderboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    observerCallbacks = [];
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(callback: IntersectionObserverCallback) {
          observerCallbacks.push(callback);
        }
        observe() {}
        disconnect() {}
      }
    );
  });

  it("shows an empty state when nobody is ranked", async () => {
    leaderboardList.mockResolvedValue(page([]));

    renderLeaderboard();

    expect(await screen.findByText("No ranked players yet")).toBeInTheDocument();
  });

  it("lists players by rank with rounded ratings linking to their profiles", async () => {
    leaderboardList.mockResolvedValue(
      page([entry(1, 3, "Ada", 1712.6), entry(2, 4, "Grace", 1650.2)])
    );

    renderLeaderboard();

    const ada = await screen.findByRole("link", { name: /Ada/ });
    expect(ada).toHaveAttribute("href", "/player/3");
    expect(within(ada).getByText("#1")).toBeInTheDocument();
    expect(within(ada).getByText("1,713")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Grace/ })).toHaveAttribute(
      "href",
      "/player/4"
    );
  });

  it("pins the user's own row when it is not on screen", async () => {
    const own = entry(41, 7, "Jane Doe", 1520);
    leaderboardList.mockResolvedValue(page([entry(1, 3, "Ada", 1712)], own));

    renderLeaderboard();

    const pinned = await screen.findByRole("link", { name: /Jane Doe/ });
    expect(pinned).toHaveAttribute("aria-current", "true");
    expect(within(pinned).getByText("#41")).toBeInTheDocument();
  });

  it("highlights the user's own row and unpins it while it is visible", async () => {
    const own = entry(2, 7, "Jane Doe", 1600);
    leaderboardList.mockResolvedValue(page([entry(1, 3, "Ada", 1712), own], own));

    renderLeaderboard();

    expect(await screen.findAllByRole("link", { name: /Jane Doe/ })).toHaveLength(2);

    reportOwnRowVisible(true);

    expect(screen.getByRole("link", { name: /Jane Doe/ })).toHaveAttribute(
      "aria-current",
      "true"
    );
  });

  it("does not pin a row for a user who is not ranked", async () => {
    leaderboardList.mockResolvedValue(page([entry(1, 3, "Ada", 1712)]));

    renderLeaderboard();

    expect(await screen.findByRole("link", { name: /Ada/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { current: true })).not.toBeInTheDocument();
  });
});
