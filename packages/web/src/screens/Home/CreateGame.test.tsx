import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import type { UserProfile, Variant } from "@/api/generated/endpoints";
import { TooltipProvider } from "@/components/ui/tooltip";
import { CreateGame } from "./CreateGame";

let userProfile: UserProfile;
let variants: Variant[] = [];

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useVariantsListSuspense: () => ({ data: variants }),
  useUserRetrieveSuspense: () => ({ data: userProfile }),
}));

vi.mock("@/hooks/use-mobile", () => ({ useIsMobile: () => false }));

vi.mock("@/components/ExpandableMapPreview", () => ({
  ExpandableMapPreview: () => null,
}));

const buildUserProfile = (overrides: Partial<UserProfile> = {}): UserProfile => ({
  id: 1,
  userId: 1,
  name: "Jane Doe",
  picture: null,
  email: "jane@example.com",
  canCreateBotGames: false,
  isModerator: false,
  canCreateCommittedGame: true,
  ...overrides,
});

const buildVariant = (overrides: Partial<Variant> = {}): Variant => ({
  id: "classical",
  name: "Classical",
  description: "",
  rules: "",
  unitScaling: 1,
  status: "published",
  official: true,
  ranked: true,
  ownerId: null,
  ownerUsername: null,
  canEdit: false,
  victoryConditions: {
    soloVictorySupplyCenters: null,
    gameEndsYear: null,
    drawAfterYear: null,
  },
  svgUrl: null,
  nations: [],
  provinces: [],
  templatePhase: { year: 1901, units: [], supplyCenters: [] },
  ...overrides,
});

const renderScreen = (initialEntry = "/create-game") =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TooltipProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
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

describe("CreateGame ranked checkbox", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  beforeEach(() => {
    userProfile = buildUserProfile();
    variants = [buildVariant()];
  });

  it("is enabled and checked for a public game on a ranked variant", async () => {
    renderScreen();

    const checkbox = await screen.findByRole("checkbox", { name: "Ranked" });
    expect(checkbox).toBeEnabled();
    expect(checkbox).toBeChecked();
  });

  it("is disabled with a reason for a variant that isn't ranked", async () => {
    variants = [buildVariant({ ranked: false })];

    renderScreen();

    const checkbox = await screen.findByRole("checkbox", { name: "Ranked" });
    expect(checkbox).toBeDisabled();
    expect(checkbox).not.toBeChecked();
    expect(
      screen.getByText("Not available for this variant yet")
    ).toBeInTheDocument();
  });

  it("is disabled with a reason for a private game", async () => {
    const user = userEvent.setup();
    renderScreen();

    await user.click(await screen.findByRole("checkbox", { name: "Private" }));

    const checkbox = screen.getByRole("checkbox", { name: "Ranked" });
    expect(checkbox).toBeDisabled();
    expect(checkbox).not.toBeChecked();
    expect(screen.getByText("Private games can't be ranked")).toBeInTheDocument();
  });

  it("is checked again when the game is made public", async () => {
    const user = userEvent.setup();
    renderScreen();
    const privateCheckbox = await screen.findByRole("checkbox", {
      name: "Private",
    });

    await user.click(privateCheckbox);
    await user.click(privateCheckbox);

    expect(screen.getByRole("checkbox", { name: "Ranked" })).toBeChecked();
  });

  it("is hidden for a sandbox game", async () => {
    renderScreen("/create-game?sandbox=true");

    await screen.findByRole("checkbox", { name: "Committed game" });
    expect(
      screen.queryByRole("checkbox", { name: "Ranked" })
    ).not.toBeInTheDocument();
  });
});
