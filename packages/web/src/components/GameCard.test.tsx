import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type { GameList } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { GameCard } from "./GameCard";

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("./GameDropdownMenu", () => ({ GameDropdownMenu: () => null }));

const buildGame = (overrides: Partial<GameList> = {}): GameList => ({
  id: "g1",
  name: "Concert of Europe",
  status: "pending",
  createdAt: "2026-10-01T00:00:00Z",
  canJoin: true,
  canLeave: false,
  canWithdraw: false,
  canDelete: false,
  canManage: false,
  gameMaster: null,
  variantId: "classical",
  phases: [],
  currentPhaseId: null,
  currentPhase: null,
  phaseConfirmed: false,
  orderStatus: null,
  memberStatus: null,
  private: false,
  anonymous: false,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  showShortGameJoinWarning: false,
  members: [],
  victory: null,
  sandbox: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 0,
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
  ...overrides,
});

const renderCard = (game: GameList) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TooltipProvider>
        <MemoryRouter>
          <GameCard
            game={game}
            variant={{ id: "classical", name: "Classical", nations: [] }}
            map={null}
          />
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );

const lockedGame = () =>
  buildGame({ canJoin: false, joinBlockedReason: "commitment_too_low" });

const tooltipText = "Your commitment is too low to join this game";

describe("GameCard", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("enables Join on a committed game the viewer can join", () => {
    renderCard(buildGame());

    expect(screen.getByRole("button", { name: "Join game" })).toBeEnabled();
    expect(screen.queryByText(tooltipText)).not.toBeInTheDocument();
  });

  it("disables Join when the viewer's commitment is too low", () => {
    renderCard(lockedGame());

    expect(screen.getByRole("button", { name: "Join game" })).toBeDisabled();
  });

  it("opens the tooltip on hover", async () => {
    const user = userEvent.setup();
    renderCard(lockedGame());

    await user.hover(screen.getByRole("button", { name: "Join game" }).parentElement!);

    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);
  });

  it("opens the tooltip on focus", async () => {
    renderCard(lockedGame());
    const trigger = screen.getByRole("button", { name: "Join game" }).parentElement!;

    act(() => trigger.focus());

    expect(trigger).toHaveFocus();
    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);
  });

  it("keeps the tooltip open after a tap and closes it on a tap outside", async () => {
    const user = userEvent.setup();
    renderCard(lockedGame());
    const trigger = screen.getByRole("button", { name: "Join game" }).parentElement!;

    await user.pointer({ keys: "[TouchA]", target: trigger });

    expect(await screen.findByRole("tooltip")).toHaveTextContent(tooltipText);

    await user.pointer({ keys: "[TouchA]", target: document.body });

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows no Join when the viewer cannot join for another reason", () => {
    renderCard(buildGame({ canJoin: false }));

    expect(screen.queryByRole("button", { name: "Join game" })).not.toBeInTheDocument();
  });
});
