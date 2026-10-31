import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type { GameRetrieve } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GameInfoScreen } from "./GameInfo";

let game: GameRetrieve;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGamePhaseRetrieve: () => ({ data: undefined }),
  useUserRetrieveSuspense: () => ({ data: { canCreateBotGames: false } }),
}));

vi.mock("@/hooks/useGameVariant", () => ({ useGameVariant: () => undefined }));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("@/components/GameDropdownMenu", () => ({ GameDropdownMenu: () => null }));

const buildGame = (overrides: Partial<GameRetrieve> = {}): GameRetrieve => ({
  id: "g1",
  name: "Concert of Europe",
  status: "pending",
  createdAt: "2026-10-01T00:00:00Z",
  canJoin: false,
  canLeave: false,
  canWithdraw: false,
  isFirstYear: false,
  canDelete: false,
  canManage: false,
  canCreateChannel: false,
  gameMaster: null,
  gameMasterMemberId: null,
  phases: [],
  currentPhaseId: null,
  members: [],
  sandbox: false,
  victory: null,
  variantId: "classical",
  phaseConfirmed: false,
  orderStatus: null,
  memberStatus: null,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  showShortGameJoinWarning: false,
  private: false,
  anonymous: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 1,
  deadlineMode: "duration",
  fixedDeadlineTime: null,
  fixedDeadlineTimezone: null,
  movementFrequency: null,
  retreatFrequency: null,
  pressType: "full_press",
  commitmentRequirement: "committed",
  joinBlockedReason: null,
  musterRequired: false,
  musterDeadline: null,
  musterStatus: null,
  totalUnreadMessageCount: 0,
  actions: [],
  playerListActions: [],
  ...overrides,
});

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TooltipProvider>
        <MemoryRouter initialEntries={["/game-info/g1"]}>
          <Routes>
            <Route path="/game-info/:gameId" element={<GameInfoScreen />} />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );

const tooltipText = "Your commitment is too low to join this game";

describe("GameInfo", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  beforeEach(() => {
    game = buildGame();
  });

  it("enables Join on a committed game the viewer can join", async () => {
    game = buildGame({ canJoin: true });

    renderScreen();

    expect(await screen.findByRole("button", { name: "Join game" })).toBeEnabled();
  });

  it("disables Join when the viewer's commitment is too low", async () => {
    game = buildGame({ joinBlockedReason: "commitment_too_low" });

    renderScreen();

    expect(await screen.findByRole("button", { name: "Join game" })).toBeDisabled();
  });

  it("opens the tooltip on hover, focus and tap", async () => {
    const user = userEvent.setup();
    game = buildGame({ joinBlockedReason: "commitment_too_low" });
    renderScreen();
    const trigger = (await screen.findByRole("button", { name: "Join game" }))
      .parentElement!;

    await user.hover(trigger);
    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);
    await user.unhover(trigger);

    act(() => trigger.focus());
    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);
    act(() => trigger.blur());

    await user.pointer({ keys: "[TouchA]", target: trigger });
    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);

    await user.pointer({ keys: "[TouchA]", target: document.body });
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows no Join when the viewer cannot join for another reason", async () => {
    game = buildGame({ canLeave: true });

    renderScreen();

    expect(await screen.findByRole("button", { name: "Leave" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Join game" })).not.toBeInTheDocument();
  });
});
