import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type {
  ChannelDetail,
  ChannelMember,
  ChannelMessage,
  GameRetrieve,
} from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ChannelScreen } from "./ChannelScreen";

let messages: ChannelMessage[] = [];

const channel: ChannelDetail = {
  id: 5,
  name: "Public Press",
  title: "",
  private: false,
  muted: false,
  canMute: false,
  canRename: false,
  unreadMessageCount: 0,
  firstUnreadMessageId: null,
  latestMessageId: null,
  latestEventId: null,
  events: [],
};

const game = {
  id: "g1",
  status: "pending",
  pressType: "full_press",
  variantId: "classical",
  gameMaster: null,
  members: [],
} as Partial<GameRetrieve> as GameRetrieve;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useUserRetrieveSuspense: () => ({ data: { userId: 1 } }),
  useGamesChannelsRetrieveSuspense: () => ({ data: channel }),
  useGamesChannelsMessagesCreateCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useGamesChannelsMarkReadCreate: () => ({ mutateAsync: vi.fn().mockResolvedValue({}) }),
}));

vi.mock("@/hooks/useChannelMessages", () => ({
  useChannelMessages: () => ({
    messages,
    hasOlder: false,
    fetchOlder: vi.fn(),
    isFetchingOlder: false,
    isFetchOlderError: false,
  }),
}));

vi.mock("@/hooks/useGameVariant", () => ({
  useGameVariant: () => ({
    nations: [
      { nationId: "england", name: "England", color: "#2196F3", nonPlayable: false, flagUrl: "/england.svg" },
    ],
  }),
}));

vi.mock("@/hooks/use-platform", () => ({ useIsDesktopWeb: () => false }));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

const buildSender = (overrides: Partial<ChannelMember> = {}): ChannelMember => ({
  id: 2,
  userId: 2,
  name: "Alice",
  picture: null,
  isCurrentUser: false,
  isBot: false,
  nation: null,
  isGameMaster: false,
  ...overrides,
});

const buildMessage = (sender: ChannelMember): ChannelMessage => ({
  id: sender.id,
  body: `Hello from ${sender.name}`,
  sender,
  createdAt: "2026-10-01T00:00:00Z",
});

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TooltipProvider>
        <MemoryRouter initialEntries={["/game/g1/phase/7/chat/channel/5"]}>
          <Routes>
            <Route
              path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
              element={<ChannelScreen />}
            />
          </Routes>
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );

describe("ChannelScreen", () => {
  beforeAll(() => {
    Object.defineProperty(HTMLImageElement.prototype, "complete", { get: () => true });
    Object.defineProperty(HTMLImageElement.prototype, "naturalWidth", { get: () => 1 });
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("shows the profile picture of a sender without a nation", async () => {
    messages = [buildMessage(buildSender({ picture: "/alice.png" }))];
    const { container } = renderScreen();

    await screen.findByText("Hello from Alice");
    expect(container.querySelector('img[src="/alice.png"]')).toBeInTheDocument();
  });

  it("shows the initial of a sender without a nation or picture", async () => {
    messages = [buildMessage(buildSender())];
    renderScreen();

    await screen.findByText("Hello from Alice");
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("shows the flag of a sender with a nation", async () => {
    messages = [
      buildMessage(
        buildSender({
          picture: "/alice.png",
          nation: { nationId: "england", name: "England", color: "#2196F3", nonPlayable: false, flagUrl: "/england.svg" },
        })
      ),
    ];
    const { container } = renderScreen();

    await screen.findByText("Hello from Alice");
    expect(container.querySelector('img[src="/england.svg"]')).toBeInTheDocument();
    expect(container.querySelector('img[src="/alice.png"]')).not.toBeInTheDocument();
  });
});
