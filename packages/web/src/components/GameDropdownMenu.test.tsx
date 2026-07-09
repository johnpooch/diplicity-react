import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect } from "vitest";
import { GameDropdownMenu } from "./GameDropdownMenu";
import {
  mockActiveGames,
  mockPendingGames,
  mockCompletedGames,
  mockSandboxGames,
} from "@/mocks/legacy";

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

const renderMenu = (game: React.ComponentProps<typeof GameDropdownMenu>["game"]) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <GameDropdownMenu
          game={game}
          onNavigateToGameInfo={() => {}}
          onNavigateToPlayerInfo={() => {}}
        />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const openMenu = async () => {
  await userEvent.click(screen.getByRole("button", { name: /game menu/i }));
};

describe("GameDropdownMenu", () => {
  it("shows 'Clone to sandbox' for an active, non-sandbox game", async () => {
    renderMenu(mockActiveGames[0]);
    await openMenu();
    expect(
      screen.getByRole("menuitem", { name: /clone to sandbox/i })
    ).toBeInTheDocument();
  });

  it("hides 'Clone to sandbox' for a pending game", async () => {
    renderMenu(mockPendingGames[0]);
    await openMenu();
    expect(
      screen.queryByRole("menuitem", { name: /clone to sandbox/i })
    ).not.toBeInTheDocument();
  });

  it("hides 'Clone to sandbox' for a completed game", async () => {
    renderMenu(mockCompletedGames[0]);
    await openMenu();
    expect(
      screen.queryByRole("menuitem", { name: /clone to sandbox/i })
    ).not.toBeInTheDocument();
  });

  it("hides 'Clone to sandbox' for a sandbox game", async () => {
    renderMenu(mockSandboxGames[0]);
    await openMenu();
    expect(
      screen.queryByRole("menuitem", { name: /clone to sandbox/i })
    ).not.toBeInTheDocument();
  });
});
