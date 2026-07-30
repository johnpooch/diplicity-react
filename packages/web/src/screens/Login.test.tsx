import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { toast } from "sonner";
import { Login } from "./Login";

const mockLogin = vi.fn();
const mockMutateAsync = vi.fn();
const mockAppleMutateAsync = vi.fn();
const mockAppleInit = vi.fn();
const mockAppleSignIn = vi.fn();

vi.mock("@/auth", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useAuthAppleLoginCreate: () => ({
    mutateAsync: mockAppleMutateAsync,
    isPending: false,
  }),
  useAuthEmailLoginCreate: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
  useAuthLoginCreate: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("@react-oauth/google", () => ({
  GoogleLogin: () => <div data-testid="google-login">Google Sign In</div>,
}));

vi.mock("@/utils/platform", () => ({
  isNativePlatform: () => false,
}));

const renderLogin = () =>
  render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );

describe("Login", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAppleSignIn.mockImplementation(() => {
      document.dispatchEvent(
        new CustomEvent("AppleIDSignInOnSuccess", {
          detail: {
            authorization: { id_token: "apple-id-token" },
            user: { name: { firstName: "Ada", lastName: "Lovelace" } },
          },
        })
      );
    });
    vi.stubGlobal("AppleID", {
      auth: { init: mockAppleInit, signIn: mockAppleSignIn },
    });
  });

  it("submits email and password and stores tokens on success", async () => {
    mockMutateAsync.mockResolvedValue({
      id: 1,
      email: "player@example.com",
      name: "Test Player",
      accessToken: "access-jwt",
      refreshToken: "refresh-jwt",
    });

    renderLogin();

    await userEvent.type(screen.getByLabelText(/email/i), "player@example.com");
    await userEvent.type(
      screen.getByLabelText(/password/i),
      "strongpass123"
    );
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(mockMutateAsync).toHaveBeenCalledWith({
      data: { email: "player@example.com", password: "strongpass123" },
    });
    expect(mockLogin).toHaveBeenCalledWith({
      accessToken: "access-jwt",
      refreshToken: "refresh-jwt",
      email: "player@example.com",
      name: "Test Player",
    });
  });

  it("shows error toast on wrong credentials", async () => {
    mockMutateAsync.mockRejectedValue(new Error("401"));
    const toastErrorSpy = vi.spyOn(toast, "error");

    renderLogin();

    await userEvent.type(screen.getByLabelText(/email/i), "player@example.com");
    await userEvent.type(
      screen.getByLabelText(/password/i),
      "wrongpass"
    );
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(toastErrorSpy).toHaveBeenCalledWith("Invalid email or password");
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it("has a link to the registration page", () => {
    renderLogin();

    const registerLink = screen.getByRole("link", { name: /register/i });
    expect(registerLink).toHaveAttribute("href", "/register");
  });

  it("has a forgot password link", () => {
    renderLogin();

    const forgotLink = screen.getByRole("link", { name: /forgot password/i });
    expect(forgotLink).toHaveAttribute("href", "/forgot-password");
  });

  it("shows Google and Apple sign-in below an OR divider", () => {
    renderLogin();

    expect(screen.getByText("OR")).toBeInTheDocument();
    expect(screen.getByTestId("google-login")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in with apple/i })).toBeInTheDocument();
  });

  it("shows App Store and Google Play badges linking to their store listings", () => {
    renderLogin();

    const appStoreLinks = screen.getAllByRole("link", {
      name: /download on the app store/i,
    });
    expect(appStoreLinks.length).toBeGreaterThan(0);
    appStoreLinks.forEach((link) =>
      expect(link).toHaveAttribute(
        "href",
        "https://apps.apple.com/app/id6759169536"
      )
    );

    const playStoreLinks = screen.getAllByRole("link", {
      name: /get it on google play/i,
    });
    expect(playStoreLinks.length).toBeGreaterThan(0);
    playStoreLinks.forEach((link) =>
      expect(link).toHaveAttribute(
        "href",
        "https://play.google.com/store/apps/details?id=com.diplicityreact.app"
      )
    );
  });

  it("signs in with Apple and stores tokens on success", async () => {
    mockAppleMutateAsync.mockResolvedValue({
      id: 2,
      email: "ada@example.com",
      name: "Ada Lovelace",
      accessToken: "apple-access-jwt",
      refreshToken: "apple-refresh-jwt",
    });

    renderLogin();

    await userEvent.click(screen.getByRole("button", { name: /sign in with apple/i }));

    expect(mockAppleMutateAsync).toHaveBeenCalledWith({
      data: {
        idToken: "apple-id-token",
        firstName: "Ada",
        lastName: "Lovelace",
      },
    });
    expect(mockLogin).toHaveBeenCalledWith({
      accessToken: "apple-access-jwt",
      refreshToken: "apple-refresh-jwt",
      email: "ada@example.com",
      name: "Ada Lovelace",
    });
  });
});
