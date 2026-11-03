import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { UserProfile } from "@/api/generated/endpoints";
import { Account } from "./Account";

const updateProfile = vi.fn();
const logout = vi.fn();
const enableMessaging = vi.fn();
let permissionDenied: boolean;

const profile: UserProfile = {
  id: 1,
  userId: 7,
  name: "Jane Doe",
  picture: null,
  email: "jane@example.com",
  canCreateBotGames: false,
  isModerator: false,
  canCreateCommittedGame: false,
};

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useUserRetrieveSuspense: () => ({ data: profile }),
  useUserUpdatePartialUpdate: () => ({
    mutateAsync: updateProfile,
    isPending: false,
  }),
  useUserPictureUpdate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUserPictureDestroy: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock("@/hooks/useLogout", () => ({ useLogout: () => logout }));

vi.mock("@/hooks/useMessaging", () => ({
  useMessaging: () => ({
    enabled: false,
    permissionDenied,
    error: null,
    enableMessaging,
    disableMessaging: vi.fn(),
  }),
}));

vi.mock("@/theme/useTheme", () => ({
  useTheme: () => ({ preference: "system", setPreference: vi.fn() }),
}));

const renderAccount = () =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <Account />
      </MemoryRouter>
    </QueryClientProvider>
  );

describe("Account", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    permissionDenied = false;
  });

  it("links to the user's profile and to account deletion", () => {
    renderAccount();

    expect(
      screen.getByRole("heading", { name: "Jane Doe" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View my profile" })
    ).toHaveAttribute("href", "/player/7");
    expect(
      screen.getByRole("link", { name: "Delete account" })
    ).toHaveAttribute("href", "/delete-account");
  });

  it("logs out", async () => {
    renderAccount();

    await userEvent.click(screen.getByRole("button", { name: "Log out" }));

    expect(logout).toHaveBeenCalled();
  });

  it("saves an edited name", async () => {
    updateProfile.mockResolvedValue({});
    renderAccount();

    await userEvent.click(screen.getByRole("button", { name: "Edit name" }));
    const input = screen.getByRole("textbox", { name: "Name" });
    await userEvent.clear(input);
    await userEvent.type(input, "Janet{Enter}");

    expect(updateProfile).toHaveBeenCalledWith({ data: { name: "Janet" } });
    expect(
      await screen.findByRole("button", { name: "Edit name" })
    ).toBeInTheDocument();
  });

  it("turns on push notifications", async () => {
    renderAccount();

    await userEvent.click(
      screen.getByRole("switch", { name: "Push notifications" })
    );

    expect(enableMessaging).toHaveBeenCalled();
  });

  it("explains why push notifications cannot be turned on", () => {
    permissionDenied = true;
    renderAccount();

    expect(
      screen.getByRole("switch", { name: "Push notifications" })
    ).toBeDisabled();
    expect(
      screen.getByText(/Reset permissions for this app/)
    ).toBeInTheDocument();
  });
});
