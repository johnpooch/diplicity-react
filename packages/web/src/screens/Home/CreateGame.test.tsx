import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver =
  globalThis.ResizeObserver ?? (ResizeObserverMock as unknown as typeof ResizeObserver);

if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList;
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
import { CreateGame, modeToBackendFields } from "./CreateGame";
import {
  getGamesFindSimilarRetrieveQueryOptions,
  useGameCreate,
  useSandboxGameCreate,
  useVariantsListSuspense,
  GameFindSimilar,
  GameList,
} from "@/api/generated/endpoints";

const mockNavigate = vi.fn();
vi.mock("react-router", async importOriginal => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/generated/endpoints", async importOriginal => {
  const actual = await importOriginal<
    typeof import("@/api/generated/endpoints")
  >();
  return {
    ...actual,
    useVariantsListSuspense: vi.fn(),
    useGameCreate: vi.fn(),
    useSandboxGameCreate: vi.fn(),
    getGamesFindSimilarRetrieveQueryOptions: vi.fn(),
  };
});

vi.mock("@/components/InteractiveMap/InteractiveMap", () => ({
  InteractiveMap: () => <div data-testid="interactive-map" />,
}));

vi.mock("@/components/UserAvatar", () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

const variantsFixture = [
  {
    id: "classical",
    name: "Classical",
    description: "",
    soloVictoryScCount: 18,
    nations: [
      { id: 1, name: "England" },
      { id: 2, name: "France" },
      { id: 3, name: "Germany" },
      { id: 4, name: "Italy" },
      { id: 5, name: "Austria" },
      { id: 6, name: "Russia" },
      { id: 7, name: "Turkey" },
    ],
    provinces: [],
    templatePhase: { id: 0, year: 1901, season: "Spring", type: "movement" },
  },
];

const matchedGame: GameList = {
  id: "matched-game",
  name: "Matched Game",
  status: "pending",
  createdAt: "2026-01-01T00:00:00Z",
  canJoin: true,
  canLeave: false,
  canDelete: false,
  variantId: "classical",
  phases: [],
  currentPhaseId: null,
  private: false,
  anonymous: false,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  nationAssignment: "random",
  members: [
    {
      id: 99,
      name: "Game Master Bob",
      picture: null,
      isCurrentUser: false,
      nation: null,
      eliminated: false,
      kicked: false,
      isGameMaster: true,
      nmrExtensionsRemaining: 0,
    },
    {
      id: 100,
      name: "Other Player",
      picture: null,
      isCurrentUser: false,
      nation: null,
      eliminated: false,
      kicked: false,
      isGameMaster: false,
      nmrExtensionsRemaining: 0,
    },
  ],
  victory: null,
  sandbox: false,
  isPaused: false,
  pausedAt: null,
  nmrExtensionsAllowed: 0,
  deadlineMode: "duration",
  fixedDeadlineTime: null,
  fixedDeadlineTimezone: null,
  movementFrequency: null,
  retreatFrequency: null,
  pressType: "full_press",
};

const renderCreateGame = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CreateGame />
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const mockedUseVariantsListSuspense = vi.mocked(useVariantsListSuspense);
const mockedUseGameCreate = vi.mocked(useGameCreate);
const mockedUseSandboxGameCreate = vi.mocked(useSandboxGameCreate);
const mockedGetFindSimilarOptions = vi.mocked(
  getGamesFindSimilarRetrieveQueryOptions
);

const stubFindSimilar = (game: GameList | null) => {
  const queryFn = vi.fn().mockResolvedValue({ game } as GameFindSimilar);
  mockedGetFindSimilarOptions.mockReturnValue({
    queryKey: ["find-similar", { game }],
    queryFn,
  } as unknown as ReturnType<typeof getGamesFindSimilarRetrieveQueryOptions>);
  return queryFn;
};

describe("modeToBackendFields", () => {
  it("maps standard mode to full press with named players", () => {
    expect(modeToBackendFields("standard")).toEqual({
      anonymous: false,
      pressType: "full_press",
    });
  });

  it("maps gunboat mode to no press with anonymous players", () => {
    expect(modeToBackendFields("gunboat")).toEqual({
      anonymous: true,
      pressType: "no_press",
    });
  });
});

describe("CreateGame — find-similar intervention", () => {
  let createGameMutateAsync: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    createGameMutateAsync = vi.fn().mockResolvedValue({ id: "created-game" });

    mockedUseVariantsListSuspense.mockReturnValue({
      data: variantsFixture,
    } as unknown as ReturnType<typeof useVariantsListSuspense>);

    mockedUseGameCreate.mockReturnValue({
      mutateAsync: createGameMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useGameCreate>);

    mockedUseSandboxGameCreate.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useSandboxGameCreate>);
  });

  const switchToDurationMode = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole("tab", { name: /duration/i }));
  };

  const submit = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole("button", { name: /create game/i }));
  };

  it("does not call find-similar when deadline mode is fixed_time", async () => {
    const user = userEvent.setup();
    const findSimilarFn = stubFindSimilar(null);
    renderCreateGame();
    await submit(user);

    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(findSimilarFn).not.toHaveBeenCalled();
    expect(mockedGetFindSimilarOptions).not.toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/game-info/created-game");
  });

  it("does not call find-similar when private is checked", async () => {
    const user = userEvent.setup();
    const findSimilarFn = stubFindSimilar(null);
    renderCreateGame();
    await switchToDurationMode(user);
    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    await submit(user);

    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(findSimilarFn).not.toHaveBeenCalled();
    expect(mockedGetFindSimilarOptions).not.toHaveBeenCalled();
  });

  it("creates the game when find-similar returns no match", async () => {
    const user = userEvent.setup();
    const findSimilarFn = stubFindSimilar(null);

    renderCreateGame();
    await switchToDurationMode(user);
    await submit(user);

    await waitFor(() => expect(findSimilarFn).toHaveBeenCalled());
    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith("/game-info/created-game");
  });

  it("shows the modal with name and member count when find-similar returns a match", async () => {
    const user = userEvent.setup();
    stubFindSimilar(matchedGame);

    renderCreateGame();
    await switchToDurationMode(user);
    await submit(user);

    await screen.findByRole("alertdialog");
    expect(screen.getByText("Matched Game")).toBeInTheDocument();
    expect(screen.getByText(/2 \/ 7 players/i)).toBeInTheDocument();
    expect(createGameMutateAsync).not.toHaveBeenCalled();
  });

  it("creates the game when 'Continue' is clicked in the modal", async () => {
    const user = userEvent.setup();
    stubFindSimilar(matchedGame);

    renderCreateGame();
    await switchToDurationMode(user);
    await submit(user);

    await screen.findByRole("alertdialog");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith("/game-info/created-game");
  });

  it("navigates to the matched game without creating when 'Join Them?' is clicked", async () => {
    const user = userEvent.setup();
    stubFindSimilar(matchedGame);

    renderCreateGame();
    await switchToDurationMode(user);
    await submit(user);

    await screen.findByRole("alertdialog");
    await user.click(screen.getByRole("button", { name: /join them/i }));

    expect(createGameMutateAsync).not.toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/game-info/matched-game");
  });
});
