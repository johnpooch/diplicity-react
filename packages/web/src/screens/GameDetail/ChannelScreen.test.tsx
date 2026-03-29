import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";

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

const mockLoggedIn = vi.fn(() => true);

vi.mock("@/auth", () => ({
  useAuth: () => ({
    loggedIn: mockLoggedIn(),
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/hooks", () => ({
  useRequiredParams: () => ({
    gameId: "1",
    phaseId: "1",
    channelId: "1",
  }),
  useDraft: () => ["", vi.fn()],
}));

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { id: "1", variantId: 1 },
  }),
  useGamesChannelsListSuspense: () => ({
    data: [
      {
        id: 1,
        name: "Public Chat",
        private: false,
        messages: [
          {
            id: 1,
            body: "Hello world",
            createdAt: "2024-01-01T00:00:00Z",
            sender: {
              nation: { name: "France" },
              picture: null,
              isCurrentUser: false,
            },
          },
        ],
      },
    ],
  }),
  useVariantsListSuspense: () => ({
    data: [{ id: 1, name: "Classical" }],
  }),
  useGamesChannelsMessagesCreateCreate: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  getGamesChannelsListQueryKey: () => ["channels"],
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
    }),
  };
});

vi.mock("@/components/NationFlag", () => ({
  NationFlag: () => <div data-testid="nation-flag" />,
}));

import { ChannelScreen } from "./ChannelScreen";

const renderComponent = () =>
  render(
    <MemoryRouter initialEntries={["/game/1/phase/1/chat/channel/1"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/chat/channel/:channelId"
          element={<ChannelScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("ChannelScreen", () => {
  it("shows message input when logged in", async () => {
    mockLoggedIn.mockReturnValue(true);
    renderComponent();

    expect(
      await screen.findByPlaceholderText("Type a message")
    ).toBeInTheDocument();
  });

  it("hides message input when not logged in", async () => {
    mockLoggedIn.mockReturnValue(false);
    renderComponent();

    expect(await screen.findByText("Hello world")).toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText("Type a message")
    ).not.toBeInTheDocument();
  });
});
