import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ChannelCreateScreen } from "./ChannelCreateScreen";

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

const member = (id: number, nation: string, overrides = {}) => ({
  id,
  userId: id,
  name: `Player ${id}`,
  picture: null,
  isCurrentUser: false,
  isBot: false,
  commitment: null,
  nation,
  eliminated: false,
  kicked: false,
  isGameCreator: false,
  nmrExtensionsRemaining: 0,
  civilDisorder: false,
  seekingReplacement: false,
  replaceable: false,
  ...overrides,
});

vi.mock("@/api/generated/endpoints", () => ({
  useGameRetrieveSuspense: () => ({
    data: {
      members: [
        member(1, "England", { isCurrentUser: true }),
        member(2, "Italy", { kicked: true, name: "Departed Player" }),
        member(3, "Italy", { name: "The Dealmaker" }),
      ],
    },
  }),
  useGamesChannelsCreateCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  getGamesChannelsListQueryKey: (gameId: string) => [`/game/${gameId}/channels/`],
}));

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/game-1/phase/1/chat/create"]}>
        <Routes>
          <Route
            path="/game/:gameId/phase/:phaseId/chat/create"
            element={<ChannelCreateScreen />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("ChannelCreateScreen", () => {
  it("offers the replacement for a seat but not the member it replaced", () => {
    renderScreen();

    expect(screen.getByText("The Dealmaker")).toBeInTheDocument();
    expect(screen.queryByText("Departed Player")).not.toBeInTheDocument();
    expect(screen.getAllByText("Italy")).toHaveLength(1);
  });
});
