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
  globalThis.ResizeObserver ??
  (ResizeObserverMock as unknown as typeof ResizeObserver);

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
  const actual =
    await importOriginal<typeof import("@/api/generated/endpoints")>();
  return {
    ...actual,
    useVariantsListSuspense: vi.fn(),
    useGameCreate: vi.fn(),
    useSandboxGameCreate: vi.fn(),
    getGamesFindSimilarRetrieveQueryOptions: vi.fn(),
  };
});

vi.mock("@/components/MapPreview", () => ({
  MapPreview: () => <div data-testid="map-preview" />,
}));

vi.mock("@/components/UserAvatar", () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

const variantsFixture = [
  {
    id: "classical",
    name: "Classical",
    description: "",
    rules: "",
    status: "published",
    ownerId: null,
    ownerUsername: null,
    canEdit: false,
    victoryConditions: {
      soloVictorySupplyCenters: 18,
      gameEndsYear: null,
      drawAfterYear: null,
    },
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
  canManage: false,
  gameMaster: null,
  variantId: "classical",
  phases: [],
  currentPhaseId: null,
  currentPhase: null,
  phaseConfirmed: false,
  private: false,
  anonymous: false,
  movementPhaseDuration: "24 hours",
  retreatPhaseDuration: null,
  nationAssignment: "random",
  members: [
    {
      id: 99,
      userId: 199,
      name: "Game Master Bob",
      picture: null,
      isCurrentUser: false,
      nation: null,
      eliminated: false,
      kicked: false,
      isGameCreator: true,
      nmrExtensionsRemaining: 0,
      civilDisorder: false,
      seekingReplacement: false,
      replaceable: false,
    },
    {
      id: 100,
      userId: 200,
      name: "Other Player",
      picture: null,
      isCurrentUser: false,
      nation: null,
      eliminated: false,
      kicked: false,
      isGameCreator: false,
      nmrExtensionsRemaining: 0,
      civilDisorder: false,
      seekingReplacement: false,
      replaceable: false,
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
  totalUnreadMessageCount: 0,
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

  const goToDeadlinesStep = async (
    user: ReturnType<typeof userEvent.setup>
  ) => {
    await user.click(screen.getByRole("button", { name: /next/i }));
  };

  const switchToDurationMode = async (
    user: ReturnType<typeof userEvent.setup>
  ) => {
    await goToDeadlinesStep(user);
    await user.click(screen.getByRole("tab", { name: /duration/i }));
  };

  const submit = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole("button", { name: /next/i }));
    await user.click(screen.getByRole("button", { name: /create game/i }));
  };

  it("does not call find-similar when deadline mode is fixed_time", async () => {
    const user = userEvent.setup();
    const findSimilarFn = stubFindSimilar(null);
    renderCreateGame();
    await goToDeadlinesStep(user);
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
    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    await switchToDurationMode(user);
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

describe("CreateGame — game master option", () => {
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

  const submit = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.click(screen.getByRole("button", { name: /next/i }));
    await user.click(screen.getByRole("button", { name: /next/i }));
    await user.click(screen.getByRole("button", { name: /create game/i }));
  };

  it("disables the game master checkbox when the game is not private", () => {
    renderCreateGame();
    expect(
      screen.getByRole("checkbox", { name: /game master/i })
    ).toBeDisabled();
  });

  it("enables the game master checkbox when the game is private", async () => {
    const user = userEvent.setup();
    renderCreateGame();
    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    expect(
      screen.getByRole("checkbox", { name: /game master/i })
    ).toBeEnabled();
  });

  it("submits gameMaster false by default", async () => {
    const user = userEvent.setup();
    renderCreateGame();
    await submit(user);

    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(createGameMutateAsync.mock.calls[0][0].data.gameMaster).toBe(false);
  });

  it("submits gameMaster true when checked on a private game", async () => {
    const user = userEvent.setup();
    renderCreateGame();
    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    await user.click(screen.getByRole("checkbox", { name: /game master/i }));
    await submit(user);

    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    const payload = createGameMutateAsync.mock.calls[0][0].data;
    expect(payload.gameMaster).toBe(true);
    expect(payload.private).toBe(true);
  });

  it("resets the game master checkbox when private is unchecked", async () => {
    const user = userEvent.setup();
    renderCreateGame();
    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    await user.click(screen.getByRole("checkbox", { name: /game master/i }));
    await user.click(screen.getByRole("checkbox", { name: /private/i }));

    const gameMasterCheckbox = screen.getByRole("checkbox", {
      name: /game master/i,
    });
    expect(gameMasterCheckbox).toBeDisabled();
    expect(gameMasterCheckbox).not.toBeChecked();

    await submit(user);
    await waitFor(() => expect(createGameMutateAsync).toHaveBeenCalled());
    expect(createGameMutateAsync.mock.calls[0][0].data.gameMaster).toBe(false);
  });
});

describe("CreateGame — multi-step navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseVariantsListSuspense.mockReturnValue({
      data: variantsFixture,
    } as unknown as ReturnType<typeof useVariantsListSuspense>);

    mockedUseGameCreate.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ id: "created-game" }),
      isPending: false,
    } as unknown as ReturnType<typeof useGameCreate>);

    mockedUseSandboxGameCreate.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useSandboxGameCreate>);
  });

  it("starts on the General step with no Create Game button", () => {
    renderCreateGame();

    expect(screen.getByRole("button", { name: /next/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /create game/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("tab", { name: /duration/i })
    ).not.toBeInTheDocument();
  });

  it("advances General → Deadlines → Advanced, then back", async () => {
    const user = userEvent.setup();
    renderCreateGame();

    await user.click(screen.getByRole("button", { name: /next/i }));

    expect(screen.getByRole("tab", { name: /duration/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("checkbox", { name: /private/i })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /create game/i })
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /next/i }));

    expect(screen.getByText("Automatic Extensions")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create game/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("tab", { name: /duration/i })
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(screen.getByRole("tab", { name: /duration/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /create game/i })
    ).not.toBeInTheDocument();
  });
});

describe("CreateGame — sandbox mode", () => {
  let sandboxMutateAsync: ReturnType<typeof vi.fn>;
  let createGameMutateAsync: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    sandboxMutateAsync = vi.fn().mockResolvedValue({ id: "sandbox-game" });
    createGameMutateAsync = vi.fn().mockResolvedValue({ id: "created-game" });

    mockedUseVariantsListSuspense.mockReturnValue({
      data: variantsFixture,
    } as unknown as ReturnType<typeof useVariantsListSuspense>);

    mockedUseGameCreate.mockReturnValue({
      mutateAsync: createGameMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useGameCreate>);

    mockedUseSandboxGameCreate.mockReturnValue({
      mutateAsync: sandboxMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useSandboxGameCreate>);
  });

  const selectSandboxMode = async (
    user: ReturnType<typeof userEvent.setup>
  ) => {
    await user.click(screen.getByRole("combobox", { name: /mode/i }));
    await user.click(screen.getByRole("option", { name: /sandbox/i }));
  };

  it("disables and unchecks private and game master when sandbox is selected", async () => {
    const user = userEvent.setup();
    renderCreateGame();

    await user.click(screen.getByRole("checkbox", { name: /private/i }));
    expect(screen.getByRole("checkbox", { name: /private/i })).toBeChecked();

    await selectSandboxMode(user);

    const privateCheckbox = screen.getByRole("checkbox", { name: /private/i });
    const gameMasterCheckbox = screen.getByRole("checkbox", {
      name: /game master/i,
    });
    expect(privateCheckbox).toBeDisabled();
    expect(privateCheckbox).not.toBeChecked();
    expect(gameMasterCheckbox).toBeDisabled();
    expect(gameMasterCheckbox).not.toBeChecked();
  });

  it("shows a Create Game button on the General step (no Next) in sandbox mode", async () => {
    const user = userEvent.setup();
    renderCreateGame();

    await selectSandboxMode(user);

    expect(
      screen.getByRole("button", { name: /create game/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /next/i })
    ).not.toBeInTheDocument();
  });

  it("creates a sandbox game and navigates to it", async () => {
    const user = userEvent.setup();
    renderCreateGame();

    await selectSandboxMode(user);
    await user.click(screen.getByRole("button", { name: /create game/i }));

    await waitFor(() => expect(sandboxMutateAsync).toHaveBeenCalled());
    const payload = sandboxMutateAsync.mock.calls[0][0].data;
    expect(payload).toEqual({
      name: expect.any(String),
      variantId: "classical",
    });
    expect(createGameMutateAsync).not.toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/game/sandbox-game");
  });
});
