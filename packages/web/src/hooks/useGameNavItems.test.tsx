import { renderHook } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useGameNavItems } from "./useGameNavItems";

let mockGame: Record<string, unknown> = {};

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieve: () => ({ data: mockGame }),
}));

const wrapper =
  (initialEntry: string) =>
  ({ children }: { children: React.ReactNode }) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialEntry]}>
          <Routes>
            <Route
              path="/game/:gameId/phase/:phaseId/*"
              element={children}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

const renderNavItems = (initialEntry: string) =>
  renderHook(() => useGameNavItems(), {
    wrapper: wrapper(initialEntry),
  }).result;

describe("useGameNavItems", () => {
  beforeEach(() => {
    mockGame = { sandbox: false, totalUnreadMessageCount: 0, members: [] };
  });

  it("returns Map, Orders, Chat, Game Info, Player Info in order with substituted paths", () => {
    const result = renderNavItems("/game/game-1/phase/1/orders");

    expect(result.current.map(item => item.label)).toEqual([
      "Map",
      "Orders",
      "Chat",
      "Game Info",
      "Player Info",
    ]);
    expect(result.current.map(item => item.path)).toEqual([
      "/game/game-1/phase/1",
      "/game/game-1/phase/1/orders",
      "/game/game-1/phase/1/chat",
      "/game/game-1/phase/1/game-info",
      "/game/game-1/phase/1/player-info",
    ]);
  });

  it("filters out Chat for sandbox games", () => {
    mockGame = { ...mockGame, sandbox: true };
    const result = renderNavItems("/game/game-1/phase/1");

    expect(result.current.map(item => item.label)).toEqual([
      "Map",
      "Orders",
      "Game Info",
      "Player Info",
    ]);
  });

  it("marks the item matching the current route as active", () => {
    const result = renderNavItems("/game/game-1/phase/1/orders");

    const active = result.current.filter(item => item.isActive);
    expect(active.map(item => item.label)).toEqual(["Orders"]);
  });

  it("shows a Chat badge when there are unread messages", () => {
    mockGame = { ...mockGame, totalUnreadMessageCount: 3 };
    const result = renderNavItems("/game/game-1/phase/1");

    const chat = result.current.find(item => item.label === "Chat");
    expect(chat?.badge).toBe("•");
  });

  it("omits the Chat badge when there are no unread messages", () => {
    const result = renderNavItems("/game/game-1/phase/1");

    const chat = result.current.find(item => item.label === "Chat");
    expect(chat?.badge).toBeUndefined();
  });

  it("shows an Orders badge when the current user is in civil disorder", () => {
    mockGame = {
      ...mockGame,
      members: [{ isCurrentUser: true, civilDisorder: true }],
    };
    const result = renderNavItems("/game/game-1/phase/1");

    const orders = result.current.find(item => item.label === "Orders");
    expect(orders?.badge).toBe("•");
  });

  it("omits the Orders badge when no member is in civil disorder", () => {
    mockGame = {
      ...mockGame,
      members: [{ isCurrentUser: true, civilDisorder: false }],
    };
    const result = renderNavItems("/game/game-1/phase/1");

    const orders = result.current.find(item => item.label === "Orders");
    expect(orders?.badge).toBeUndefined();
  });

  it("carries other search params onto every item's path", () => {
    const result = renderNavItems("/game/game-1/phase/1?foo=bar");

    expect(result.current.map(item => item.path)).toEqual([
      "/game/game-1/phase/1?foo=bar",
      "/game/game-1/phase/1/orders?foo=bar",
      "/game/game-1/phase/1/chat?foo=bar",
      "/game/game-1/phase/1/game-info?foo=bar",
      "/game/game-1/phase/1/player-info?foo=bar",
    ]);
  });

  it("drops channelId from the Chat path but keeps other params while inside a chat channel", () => {
    const result = renderNavItems(
      "/game/game-1/phase/1/chat/some-channel?channelId=some-channel&foo=bar"
    );

    const chat = result.current.find(item => item.label === "Chat");
    expect(chat?.path).toBe("/game/game-1/phase/1/chat?foo=bar");
    expect(chat?.isActive).toBe(true);
  });
});
