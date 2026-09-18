import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CommunityChat } from "./CommunityChat";

const mockFetchChannels = vi.fn();
let mockConfigured = true;

vi.mock("@/api/cssFeed", () => ({
  fetchWatchedChannels: () => mockFetchChannels(),
  generalChannelId: "10",
  get cssFeedConfigured() {
    return mockConfigured;
  },
}));

const cssFeedMessage = (overrides = {}) => ({
  id: "1",
  channelId: "10",
  authorId: "20",
  authorName: "Alice",
  authorAvatar: null,
  content: "Hello general",
  createdAt: "2026-05-01T12:00:00Z",
  editedAt: null,
  attachments: [],
  ...overrides,
});

const cssFeedChannel = (overrides = {}) => ({
  id: "10",
  name: "general",
  guildId: "1",
  messages: [cssFeedMessage()],
  ...overrides,
});

const renderCommunityChat = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CommunityChat />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

beforeEach(() => {
  mockConfigured = true;
  mockFetchChannels.mockReset();
});

describe("CommunityChat", () => {
  it("renders nothing when css-feed is not configured", () => {
    mockConfigured = false;

    const { container } = renderCommunityChat();

    expect(container).toBeEmptyDOMElement();
  });

  it("shows messages from the general channel by default", async () => {
    mockFetchChannels.mockResolvedValue([cssFeedChannel()]);

    renderCommunityChat();

    expect(await screen.findByText("Hello general")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("shows an empty notice when the selected channel has no messages", async () => {
    mockFetchChannels.mockResolvedValue([cssFeedChannel({ messages: [] })]);

    renderCommunityChat();

    expect(await screen.findByText("No messages yet")).toBeInTheDocument();
  });

  it("shows a notice pointing to Discord above the messages", async () => {
    mockFetchChannels.mockResolvedValue([cssFeedChannel()]);

    renderCommunityChat();

    expect(await screen.findByText("Hello general")).toBeInTheDocument();
    expect(screen.getByText("More messages on Discord")).toBeInTheDocument();
  });

  it("opens discord when the more-messages notice is clicked", async () => {
    mockFetchChannels.mockResolvedValue([cssFeedChannel()]);
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);

    const user = userEvent.setup();
    renderCommunityChat();

    await user.click(await screen.findByText("More messages on Discord"));

    expect(openSpy).toHaveBeenCalledWith(
      "https://discord.gg/cwjzxEqTuN",
      "_blank",
      "noopener,noreferrer"
    );
  });

  it("switches channels via the channel switcher", async () => {
    mockFetchChannels.mockResolvedValue([
      cssFeedChannel(),
      cssFeedChannel({
        id: "11",
        name: "off-topic",
        messages: [cssFeedMessage({ id: "2", content: "Off topic hello" })],
      }),
    ]);

    const user = userEvent.setup();
    renderCommunityChat();

    await screen.findByText("Hello general");
    await user.click(screen.getByRole("button", { name: /general\. Choose channel/i }));
    await user.click(screen.getByRole("button", { name: "#off-topic" }));

    expect(await screen.findByText("Off topic hello")).toBeInTheDocument();
  });

  it("shows the discord invite blurb when the feed request fails", async () => {
    mockFetchChannels.mockRejectedValue(new Error("network error"));

    renderCommunityChat();

    expect(await screen.findByText("Join the community")).toBeInTheDocument();
  });
});
