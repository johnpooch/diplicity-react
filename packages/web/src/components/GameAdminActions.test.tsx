import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { GameAdminActions } from "./GameAdminActions";

const mockPauseMutateAsync = vi.fn();
const mockUnpauseMutateAsync = vi.fn();
const mockExtendDeadlineMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGamePauseUpdate: () => ({
    mutateAsync: mockPauseMutateAsync,
    isPending: false,
  }),
  useGameUnpausePartialUpdate: () => ({
    mutateAsync: mockUnpauseMutateAsync,
    isPending: false,
  }),
  useGameExtendDeadlineUpdate: () => ({
    mutateAsync: mockExtendDeadlineMutateAsync,
    isPending: false,
  }),
  getGameRetrieveQueryKey: () => ["game"],
  getGamesListQueryKey: () => ["games"],
  getGamePhasesListQueryKey: () => ["phases"],
  getGamePhaseRetrieveQueryKey: () => ["phase"],
  DurationEnum: {
    "1_hour": "1 hour",
    "2_hours": "2 hours",
    "4_hours": "4 hours",
    "8_hours": "8 hours",
    "12_hours": "12 hours",
    "24_hours": "24 hours",
    "48_hours": "48 hours",
    "3_days": "3 days",
    "4_days": "4 days",
    "1_week": "1 week",
    "2_weeks": "2 weeks",
  },
}));

if (!Element.prototype.hasPointerCapture)
  Element.prototype.hasPointerCapture = () => false;
if (!Element.prototype.releasePointerCapture)
  Element.prototype.releasePointerCapture = () => {};
if (!Element.prototype.scrollIntoView)
  Element.prototype.scrollIntoView = () => {};

const renderActions = (game: React.ComponentProps<typeof GameAdminActions>["game"]) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <GameAdminActions game={game} />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("GameAdminActions", () => {
  beforeEach(() => {
    mockPauseMutateAsync.mockClear();
    mockUnpauseMutateAsync.mockClear();
    mockExtendDeadlineMutateAsync.mockClear();
  });

  it("shows Pause and Extend deadline for an unpaused game", () => {
    renderActions({ id: "game-1", isPaused: false });

    expect(screen.getByRole("button", { name: /pause/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /extend deadline/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /resume/i })
    ).not.toBeInTheDocument();
  });

  it("pauses the game", async () => {
    renderActions({ id: "game-1", isPaused: false });

    await userEvent.click(screen.getByRole("button", { name: /pause/i }));

    expect(mockPauseMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("shows only Resume for a paused game, with a Paused status instead of Extend deadline", () => {
    renderActions({ id: "game-1", isPaused: true });

    expect(screen.getByRole("button", { name: /resume/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /pause/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /extend deadline/i })
    ).not.toBeInTheDocument();
    expect(screen.getByText("Paused")).toBeInTheDocument();
  });

  it("resumes a paused game", async () => {
    renderActions({ id: "game-1", isPaused: true });

    await userEvent.click(screen.getByRole("button", { name: /resume/i }));

    expect(mockUnpauseMutateAsync).toHaveBeenCalledWith({ gameId: "game-1" });
  });

  it("extends the deadline with the default duration", async () => {
    renderActions({ id: "game-1", isPaused: false });

    await userEvent.click(
      screen.getByRole("button", { name: /extend deadline/i })
    );
    await userEvent.click(screen.getByRole("button", { name: "Extend" }));

    expect(mockExtendDeadlineMutateAsync).toHaveBeenCalledWith({
      gameId: "game-1",
      data: { duration: "24 hours" },
    });
  });
});
