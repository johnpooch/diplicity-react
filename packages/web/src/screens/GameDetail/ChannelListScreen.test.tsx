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

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: { id: "1", sandbox: false },
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
            body: "Hello",
            sender: { nation: { name: "France" } },
          },
        ],
      },
    ],
  }),
}));

import { ChannelListScreen } from "./ChannelListScreen";

const renderComponent = () =>
  render(
    <MemoryRouter initialEntries={["/game/1/phase/1/chat"]}>
      <Routes>
        <Route
          path="/game/:gameId/phase/:phaseId/chat"
          element={<ChannelListScreen />}
        />
      </Routes>
    </MemoryRouter>
  );

describe("ChannelListScreen", () => {
  it("shows Create Channel button when logged in", async () => {
    mockLoggedIn.mockReturnValue(true);
    renderComponent();

    expect(await screen.findByText("Create Channel")).toBeInTheDocument();
  });

  it("hides Create Channel button when not logged in", async () => {
    mockLoggedIn.mockReturnValue(false);
    renderComponent();

    expect(await screen.findByText("Public Chat")).toBeInTheDocument();
    expect(screen.queryByText("Create Channel")).not.toBeInTheDocument();
  });
});
