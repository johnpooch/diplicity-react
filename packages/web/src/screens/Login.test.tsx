import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Login } from "./Login";

const mockEmailLogin = vi.fn();

vi.mock("@/auth", () => ({
  useAuth: () => ({ login: vi.fn() }),
}));

vi.mock("@/api/generated/endpoints", async importOriginal => ({
  ...(await importOriginal<typeof import("@/api/generated/endpoints")>()),
  useAuthAppleLoginCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAuthEmailLoginCreate: () => ({
    mutateAsync: mockEmailLogin,
    isPending: false,
  }),
  useAuthLoginCreate: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock("@react-oauth/google", () => ({
  GoogleLogin: () => null,
}));

const renderLogin = () =>
  render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );

beforeEach(() => {
  mockEmailLogin.mockReset();
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("Login", () => {
  it("pre-fills the test user when VITE_PREFILL_TEST_USER is true", () => {
    vi.stubEnv("VITE_PREFILL_TEST_USER", "true");

    renderLogin();

    expect(screen.getByLabelText("Email")).toHaveValue("test-user@example.com");
    expect(screen.getByLabelText("Password")).toHaveValue("password");
    expect(mockEmailLogin).not.toHaveBeenCalled();
  });

  it("keeps the pre-filled fields editable", async () => {
    vi.stubEnv("VITE_PREFILL_TEST_USER", "true");
    const user = userEvent.setup();

    renderLogin();
    const email = screen.getByLabelText("Email");
    await user.clear(email);
    await user.type(email, "someone@example.com");

    expect(email).toHaveValue("someone@example.com");
  });

  it("leaves the form empty when VITE_PREFILL_TEST_USER is not set", () => {
    renderLogin();

    expect(screen.getByLabelText("Email")).toHaveValue("");
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });
});
