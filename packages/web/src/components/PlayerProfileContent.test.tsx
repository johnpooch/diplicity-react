import { render, screen } from "@testing-library/react";
import { describe, test, expect, vi } from "vitest";

import { PlayerProfileContent } from "./PlayerProfileContent";

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
  soloWins: 3,
  draws: 2,
  losses: 7,
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
  test("renders stats, most played nation, and recent results", () => {
    mockProfile.mockReturnValue(baseProfile);

    render(<PlayerProfileContent userId={2} />);

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("25% of games")).toBeInTheDocument();
    expect(screen.getByText("Most played")).toBeInTheDocument();
    expect(screen.getByText("Austria")).toBeInTheDocument();
    expect(screen.getByText("5 of 12 games")).toBeInTheDocument();
    expect(screen.getByText("Recent results")).toBeInTheDocument();
    expect(screen.getByText("The Long Game")).toBeInTheDocument();
    expect(screen.getByText("Won")).toBeInTheDocument();
  });

  test("hides most played and recent results cards when there is no data for them", () => {
    mockProfile.mockReturnValue({
      ...baseProfile,
      favouriteNation: null,
      recentResults: [],
    });

    render(<PlayerProfileContent userId={2} />);

    expect(screen.queryByText("Most played")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent results")).not.toBeInTheDocument();
  });
});
