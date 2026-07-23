import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ChannelScreen } from "./ChannelScreen";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockChannelsData = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      pressType: "public_press",
      status: "active",
      variantId: "standard",
      members: [{ isCurrentUser: true, nation: "England" }],
    },
  }),
  useGamesChannelsListSuspense: () => ({ data: mockChannelsData() }),
  useVariantsListSuspense: () => ({ data: [] }),
  useVariantsRetrieve: () => ({ data: undefined }),
  useGamesChannelsMessagesCreateCreate: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
  useGamesChannelsMarkReadCreate: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
  getGamesChannelsListQueryKey: () => ["channels"],
  getGameRetrieveQueryKey: () => ["game"],
}));

vi.mock("@/hooks/use-platform", () => ({
  useIsDesktopWeb: () => false,
}));

const channel = (overrides: Record<string, unknown>) => ({
  id: 1,
  name: "Bot Channel",
  private: true,
  memberIds: [1],
  unreadMessageCount: 0,
  messageLimit: null,
  memberMessageCount: null,
  messages: [],
  ...overrides,
});

const renderChannel = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/1"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/:channelId"
            element={<ChannelScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelScreen message limit", () => {
  it("shows the per-phase counter and enables input below the cap", () => {
    mockChannelsData.mockReturnValue([
      channel({ messageLimit: 10, memberMessageCount: 3 }),
    ]);

    renderChannel();

    expect(screen.getByText("3 / 10 messages this phase")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type a message")).not.toBeDisabled();
  });

  it("disables input and shows a notice when the cap is reached", () => {
    mockChannelsData.mockReturnValue([
      channel({ messageLimit: 10, memberMessageCount: 10 }),
    ]);

    renderChannel();

    expect(
      screen.getByText("Message limit reached for this phase (10)")
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type a message")).toBeDisabled();
  });

  it("shows no counter in channels without a message limit", () => {
    mockChannelsData.mockReturnValue([
      channel({ messageLimit: null, memberMessageCount: null }),
    ]);

    renderChannel();

    expect(screen.queryByText(/messages this phase/)).not.toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type a message")).not.toBeDisabled();
  });
});

describe("ChannelScreen staging chat (null nation)", () => {
  it("falls back to sender name when nation is not yet assigned", () => {
    mockChannelsData.mockReturnValue([
      channel({
        messages: [
          {
            id: 1,
            body: "Excited to play!",
            createdAt: "2024-01-15T12:00:00Z",
            sender: {
              id: 2,
              name: "Bob",
              picture: null,
              nation: null,
              isCurrentUser: false,
            },
          },
        ],
      }),
    ]);

    renderChannel();

    expect(screen.getByText("Excited to play!")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });
});
