import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  GameRetrieve,
  Member,
  MemberNationPreference,
} from "@/api/generated/endpoints";
import { NationPreferenceContent } from "./NationPreferenceContent";

let game: GameRetrieve;
const retrievePreference = vi.fn();

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useGameRetrieveSuspense: () => ({ data: game }),
  useGameMemberNationPreferenceRetrieveSuspense: () => retrievePreference(),
}));

vi.mock("@/hooks/useGameVariant", () => ({ useGameVariant: () => undefined }));

const currentMember = { isCurrentUser: true, nation: null } as Member;

const buildGame = (overrides: Partial<GameRetrieve> = {}): GameRetrieve =>
  ({
    id: "g1",
    status: "pending",
    members: [currentMember],
    playerListActions: [
      { key: "edit_nation_preferences", blockedReason: null },
    ],
    ...overrides,
  }) as GameRetrieve;

const renderContent = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/game/g1"]}>
        <Routes>
          <Route
            path="/game/:gameId"
            element={<NationPreferenceContent savedPath="/game/g1" />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("NationPreferenceContent", () => {
  beforeEach(() => {
    game = buildGame();
    retrievePreference.mockReset();
    retrievePreference.mockReturnValue({
      data: { nationIds: [] } as MemberNationPreference,
    });
  });

  it("shows the preference form while preferences can be edited", () => {
    renderContent();

    expect(
      screen.getByRole("button", { name: "Save preferences" })
    ).toBeInTheDocument();
    expect(retrievePreference).toHaveBeenCalled();
  });

  it("does not request preferences once the game has started", () => {
    game = buildGame({ status: "active", playerListActions: [] });

    renderContent();

    expect(
      screen.getByText("Nation preferences are closed")
    ).toBeInTheDocument();
    expect(retrievePreference).not.toHaveBeenCalled();
  });
});
