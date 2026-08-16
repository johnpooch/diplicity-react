import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { GameDetailLayout } from "./GameDetailLayout";

const mockGameData = vi.fn();
const mockDrawProposalsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieve: () => ({ data: mockGameData() }),
  useGamesDrawProposalsList: () => ({ data: mockDrawProposalsData() }),
}));

vi.mock("@/components/Navigation", () => ({
  Navigation: ({
    items,
  }: {
    items: Array<{ label: string; badge?: string; isActive?: boolean }>;
  }) => (
    <div>
      {items.map(item => (
        <div
          key={item.label}
          data-testid={`nav-${item.label}`}
          data-badge={item.badge ?? ""}
          data-active={item.isActive ? "true" : "false"}
        />
      ))}
    </div>
  ),
}));

vi.mock("@/components/GameMap", () => ({ GameMap: () => null }));
vi.mock("@/components/OfflineBanner", () => ({ OfflineBanner: () => null }));
vi.mock("@/components/SafeAreaView", () => ({
  SafeAreaView: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock("@/components/ui/sidebar", () => ({
  SidebarProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Sidebar: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SidebarHeader: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SidebarContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SidebarInset: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const renderLayout = (
  initialEntry = "/game/g1/phase/1/overview",
  child = <div>Overview</div>
) =>
  render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/*"
          element={<GameDetailLayout>{child}</GameDetailLayout>}
        />
      </Routes>
    </MemoryRouter>
  );

describe("GameDetailLayout draw-proposal notification", () => {
  it("adds a notification dot to each Overview navigation item", () => {
    mockGameData.mockReturnValue({
      status: "active",
      sandbox: false,
      members: [],
      totalUnreadMessageCount: 0,
    });
    mockDrawProposalsData.mockReturnValue([
      {
        id: 1,
        status: "pending",
        myVote: { included: true, accepted: null },
      },
    ]);

    renderLayout();

    expect(screen.getAllByTestId("nav-Overview")).toHaveLength(2);
    for (const overviewItem of screen.getAllByTestId("nav-Overview")) {
      expect(overviewItem).toHaveAttribute("data-badge", "•");
    }
  });

  it("keeps Overview active throughout the Game Info flow", () => {
    mockGameData.mockReturnValue({
      status: "active",
      sandbox: false,
      members: [],
      totalUnreadMessageCount: 0,
    });
    mockDrawProposalsData.mockReturnValue([]);

    renderLayout("/game/g1/phase/1/game-info", <div>Game Info</div>);

    for (const overviewItem of screen.getAllByTestId("nav-Overview")) {
      expect(overviewItem).toHaveAttribute("data-active", "true");
    }
  });
});
