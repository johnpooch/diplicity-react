import type { ComponentProps } from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, test, expect, vi } from "vitest";

import { PlayerProfileContent } from "./PlayerProfileContent";

const renderProfile = (
  props: ComponentProps<typeof PlayerProfileContent>
) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PlayerProfileContent {...props} />
    </QueryClientProvider>
  );
};

const mockProfile = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useUsersRetrieveSuspense: () => ({ data: mockProfile() }),
}));

const nation = (name: string) => ({
  nationId: name.toLowerCase(),
  name,
  color: "#cccccc",
  nonPlayable: false,
  flagUrl: null,
});

const baseProfile = {
  id: 2,
  name: "Alice",
  picture: null,
  createdAt: "2025-01-15T12:00:00Z",
  totalGames: 12,
  soloWins: 1,
  draws: 3,
  losses: 6,
  nmrRate: 0.05,
  cdRate: 0,
  reliabilityTier: "reliable",
  commitment: "high",
  favouriteNation: { nation: nation("Austria"), gamesPlayed: 5 },
  recentResults: [
    {
      gameId: "game-1",
      gameName: "The Long Game",
      nation: nation("Austria"),
      outcome: "won" as const,
      finishedAt: "2025-08-01T12:00:00Z",
    },
  ],
};

describe("PlayerProfileContent", () => {
  test("renders the favourite nation and recent results cards", () => {
    mockProfile.mockReturnValue(baseProfile);

    renderProfile({ userId: 2 });

    expect(screen.getByText("Most Played")).toBeInTheDocument();
    expect(screen.getByText("Austria")).toBeInTheDocument();
    expect(screen.getByText("5 of 12 games")).toBeInTheDocument();
    expect(screen.getByText("Recent Results")).toBeInTheDocument();
    expect(screen.getByText("The Long Game")).toBeInTheDocument();
    expect(screen.getByText("Won")).toBeInTheDocument();
  });

  test("hides the favourite nation and recent results cards when there is no data", () => {
    mockProfile.mockReturnValue({
      ...baseProfile,
      favouriteNation: null,
      recentResults: [],
    });

    renderProfile({ userId: 2 });

    expect(screen.queryByText("Most Played")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent Results")).not.toBeInTheDocument();
  });
});
