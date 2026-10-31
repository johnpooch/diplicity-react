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
  isModerator: false,
  commitment: "undefined",
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

describe("CreateGame committed game checkbox", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("is enabled and unchecked for a creator who meets the threshold", async () => {
    userProfile = buildUserProfile();

    renderScreen();

    const checkbox = await screen.findByRole("checkbox", { name: "Committed game" });
    expect(checkbox).toBeEnabled();
    expect(checkbox).not.toBeChecked();
    expect(
      screen.getByText("Only players with a commitment of 10 or more can join")
    ).toBeInTheDocument();
  });

  it("is disabled for a creator below the threshold", async () => {
    userProfile = buildUserProfile({ canCreateCommittedGame: false });

    renderScreen();

    expect(
      await screen.findByRole("checkbox", { name: "Committed game" })
    ).toBeDisabled();
    expect(
      screen.getByText("Only players with a commitment of 10 or more can join")
    ).toBeInTheDocument();
  });
});
