import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import { GameCard } from "./GameCard";
import { mockGames, mockSandboxGames, mockPhaseMovement } from "@/mocks";

vi.mock("@/api/generated/endpoints", async () => {
  const actual = await vi.importActual("@/api/generated/endpoints");
  return {
    ...actual,
    useGamePhaseRetrieve: () => ({ data: mockPhaseMovement }),
    useGameJoinCreate: () => ({
      mutateAsync: vi.fn(),
      isPending: false,
    }),
    getGamesListQueryKey: () => ["games"],
  };
});

const renderGameCard = (props: React.ComponentProps<typeof GameCard>) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GameCard {...props} />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const defaultProps = {
  variant: { name: "Classical Diplomacy", id: "Classical" },
  phaseId: 1,
  map: <div data-testid="map" />,
};

describe("GameCard", () => {
  describe("sandbox visual treatment", () => {
    it("displays a Sandbox badge when game.sandbox is true", () => {
      renderGameCard({
        game: mockSandboxGames[0],
        ...defaultProps,
      });
      expect(screen.getByText("Sandbox")).toBeInTheDocument();
    });

    it("does not display a Sandbox badge when game.sandbox is false", () => {
      renderGameCard({
        game: mockGames[0],
        ...defaultProps,
      });
      expect(screen.queryByText("Sandbox")).not.toBeInTheDocument();
    });

    it("hides avatar group for sandbox games", () => {
      renderGameCard({
        game: mockSandboxGames[0],
        ...defaultProps,
      });
      for (const member of mockSandboxGames[0].members.slice(0, 7)) {
        expect(
          screen.queryByText(member.name?.[0]?.toUpperCase() ?? "?")
        ).not.toBeInTheDocument();
      }
    });

    it("shows avatar group for non-sandbox games", () => {
      renderGameCard({
        game: mockGames[0],
        ...defaultProps,
      });
      expect(screen.getByText("A")).toBeInTheDocument();
    });
  });
});
