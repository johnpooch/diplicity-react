import type { ComponentProps } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, test, expect, vi } from "vitest";

import { PlayerProfileContent } from "./PlayerProfileContent";

const renderProfile = (props: ComponentProps<typeof PlayerProfileContent>) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PlayerProfileContent {...props} />
    </QueryClientProvider>
  );
};

const mockProfile = vi.fn();
const mockCurrentUser = vi.fn();
const mockLogout = vi.fn();
const mockUpdateName = vi.fn().mockResolvedValue(undefined);

vi.mock("@/api/generated/endpoints", () => ({
  useUsersRetrieveSuspense: () => ({ data: mockProfile() }),
  useUserRetrieveSuspense: () => ({ data: mockCurrentUser() }),
  useUserUpdatePartialUpdate: () => ({
    mutateAsync: mockUpdateName,
    isPending: false,
  }),
  getUserRetrieveQueryKey: () => ["user"],
  getUsersRetrieveQueryKey: (userId: number) => ["users", userId],
}));

vi.mock("@/hooks/useLogout", () => ({
  useLogout: () => mockLogout,
}));

vi.mock("@/components/ProfilePictureEditor", () => ({
  ProfilePictureEditor: () => <div data-testid="profile-picture-editor" />,
}));

vi.mock("@/components/AccountSettingsCard", () => ({
  AccountSettingsCard: () => <div data-testid="account-settings-card" />,
}));

const nation = (name: string) => ({
  nationId: name.toLowerCase(),
  name,
  color: "#cccccc",
  nonPlayable: false,
  flagUrl: null,
});

const baseProfile = {
  id: 2,
  name: "Alice",
  picture: null,
  createdAt: "2025-01-15T12:00:00Z",
  totalGames: 12,
  soloWins: 3,
  draws: 2,
  losses: 7,
  nmrRate: 0.05,
  cdRate: 0,
  reliabilityTier: "reliable",
  commitment: "high",
  favouriteNation: { nation: nation("Austria"), gamesPlayed: 5 },
  recentResults: [
    {
      gameId: "game-1",
      gameName: "The Long Game",
      nation: nation("Austria"),
      outcome: "won" as const,
      finishedAt: "2025-08-01T12:00:00Z",
    },
  ],
};

const currentUser = { id: 1, userId: 1, name: "Bob", picture: null };

describe("PlayerProfileContent", () => {
  test("renders stats, most played nation, and recent results", () => {
    mockProfile.mockReturnValue(baseProfile);
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ userId: 2 });

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("25% of games")).toBeInTheDocument();
    expect(screen.getByText("Most played")).toBeInTheDocument();
    expect(screen.getByText("Austria")).toBeInTheDocument();
    expect(screen.getByText("5 of 12 games")).toBeInTheDocument();
    expect(screen.getByText("Recent results")).toBeInTheDocument();
    expect(screen.getByText("The Long Game")).toBeInTheDocument();
    expect(screen.getByText("Won")).toBeInTheDocument();
  });

  test("hides most played and recent results cards when there is no data for them", () => {
    mockProfile.mockReturnValue({
      ...baseProfile,
      favouriteNation: null,
      recentResults: [],
    });
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ userId: 2 });

    expect(screen.queryByText("Most played")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent results")).not.toBeInTheDocument();
  });

  test("hides rename, log out, and account settings for another player's profile", () => {
    mockProfile.mockReturnValue(baseProfile);
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ userId: 2, showAccountSettings: true });

    expect(
      screen.queryByRole("button", { name: "Edit name" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Log out" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("account-settings-card")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("profile-picture-editor")
    ).not.toBeInTheDocument();
  });

  test("shows rename and log out, but not account settings, for the logged-in user's own profile by default", () => {
    mockProfile.mockReturnValue({ ...baseProfile, id: 1 });
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ userId: 1 });

    expect(screen.getByRole("button", { name: "Edit name" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
    expect(screen.getByTestId("profile-picture-editor")).toBeInTheDocument();
    expect(
      screen.queryByTestId("account-settings-card")
    ).not.toBeInTheDocument();
  });

  test("shows account settings for the own profile when showAccountSettings is set", () => {
    mockProfile.mockReturnValue({ ...baseProfile, id: 1 });
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ userId: 1, showAccountSettings: true });

    expect(screen.getByTestId("account-settings-card")).toBeInTheDocument();
  });

  test("defaults to the logged-in user's own profile when no userId is given", () => {
    mockProfile.mockReturnValue({ ...baseProfile, id: 1 });
    mockCurrentUser.mockReturnValue(currentUser);

    renderProfile({ showAccountSettings: true });

    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
    expect(screen.getByTestId("account-settings-card")).toBeInTheDocument();
  });

  test("logs out when Log out is clicked", async () => {
    mockProfile.mockReturnValue({ ...baseProfile, id: 1 });
    mockCurrentUser.mockReturnValue(currentUser);
    const user = userEvent.setup();

    renderProfile({ userId: 1 });
    await user.click(screen.getByRole("button", { name: "Log out" }));

    expect(mockLogout).toHaveBeenCalled();
  });

  test("refreshes both the logged-in user and this profile's cached data after a rename", async () => {
    mockProfile.mockReturnValue({ ...baseProfile, id: 1 });
    mockCurrentUser.mockReturnValue(currentUser);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <PlayerProfileContent userId={1} />
      </QueryClientProvider>
    );

    await user.click(screen.getByRole("button", { name: "Edit name" }));
    await user.clear(screen.getByDisplayValue("Alice"));
    await user.type(screen.getByRole("textbox"), "Alicia");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["user"] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["users", 1] });
  });
});
