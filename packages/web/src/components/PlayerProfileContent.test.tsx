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
  nmrCount: 3,
  cdRate: 0,
  reliabilityTier: "reliable",
  commitment: "high",
};

describe("PlayerProfileContent", () => {
  test("renders the player's name and stat tiles", () => {
    mockProfile.mockReturnValue(baseProfile);

    renderProfile({ userId: 2 });

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Games")).toBeInTheDocument();
    expect(screen.getByText("Victory")).toBeInTheDocument();
    expect(screen.getByText("25% of games")).toBeInTheDocument();
    expect(screen.getByText("Draws")).toBeInTheDocument();
    expect(screen.getByText("Reliability")).toBeInTheDocument();
    expect(screen.getByText("95%")).toBeInTheDocument();
    expect(screen.getByText("3 missed deadlines")).toBeInTheDocument();
  });

  test("omits the victory hint when the player has no games", () => {
    mockProfile.mockReturnValue({
      ...baseProfile,
      totalGames: 0,
      soloWins: 0,
    });

    renderProfile({ userId: 2 });

    expect(screen.queryByText(/of games/)).not.toBeInTheDocument();
  });

  test("uses the singular form for exactly one missed deadline", () => {
    mockProfile.mockReturnValue({ ...baseProfile, nmrCount: 1 });

    renderProfile({ userId: 2 });

    expect(screen.getByText("1 missed deadline")).toBeInTheDocument();
  });

  test("omits the reliability hint when the player has no missed deadlines", () => {
    mockProfile.mockReturnValue({ ...baseProfile, nmrCount: 0 });

    renderProfile({ userId: 2 });

    expect(screen.queryByText(/missed deadline/)).not.toBeInTheDocument();
  });
});
