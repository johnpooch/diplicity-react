import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type { UserProfile } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { CreateGame } from "./CreateGame";

let userProfile: UserProfile;

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useVariantsListSuspense: () => ({ data: [] }),
  useUserRetrieveSuspense: () => ({ data: userProfile }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

const buildUserProfile = (overrides: Partial<UserProfile> = {}): UserProfile => ({
  id: 1,
  userId: 1,
  name: "Jane Doe",
  picture: null,
  email: "jane@example.com",
  canCreateBotGames: false,
  commitment: "undefined",
  commitmentTotal: 12,
  canCreateCommittedGame: true,
  ...overrides,
});

const renderScreen = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TooltipProvider>
        <MemoryRouter>
          <CreateGame />
        </MemoryRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );

const committedSwitch = () => screen.getByRole("switch", { name: "Committed game" });

describe("CreateGame committed game switch", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("is enabled and off for a creator who meets the threshold", async () => {
    userProfile = buildUserProfile();

    renderScreen();

    expect(await screen.findByRole("switch", { name: "Committed game" })).toBeEnabled();
    expect(committedSwitch()).not.toBeChecked();
    expect(
      screen.getByText("Only players with a commitment of 10 or more can join")
    ).toBeInTheDocument();
  });

  it("is disabled with the creator's total for a creator below the threshold", async () => {
    userProfile = buildUserProfile({ commitmentTotal: 4, canCreateCommittedGame: false });

    renderScreen();

    expect(await screen.findByRole("switch", { name: "Committed game" })).toBeDisabled();
    expect(
      screen.getByText(
        "Only players with a commitment of 10 or more can join. Yours is 4, so you can't create one yet."
      )
    ).toBeInTheDocument();
  });
});
