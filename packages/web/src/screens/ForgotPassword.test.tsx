import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { toast } from "sonner";
import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse } from "axios";
import { ForgotPassword } from "./ForgotPassword";

const mockMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useAuthPasswordResetCreate: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

const rateLimitedError = () => {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError(
    "Request failed with status code 429",
    AxiosError.ERR_BAD_REQUEST,
    config,
    undefined,
    { status: 429, statusText: "", data: null, headers: {}, config } as AxiosResponse
  );
};

const renderForgotPassword = () =>
  render(
    <MemoryRouter>
      <ForgotPassword />
    </MemoryRouter>
  );

describe("ForgotPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits email and shows confirmation message", async () => {
    mockMutateAsync.mockResolvedValue({});

    renderForgotPassword();

    await userEvent.type(
      screen.getByLabelText(/email/i),
      "player@example.com"
    );
    await userEvent.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    expect(mockMutateAsync).toHaveBeenCalledWith({
      data: { email: "player@example.com" },
    });
    expect(screen.getByText(/check your email/i)).toBeInTheDocument();
  });

  it("tells the user to wait when reset requests are rate limited", async () => {
    mockMutateAsync.mockRejectedValue(rateLimitedError());
    const toastErrorSpy = vi.spyOn(toast, "error");

    renderForgotPassword();

    await userEvent.type(
      screen.getByLabelText(/email/i),
      "player@example.com"
    );
    await userEvent.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    expect(toastErrorSpy).toHaveBeenCalledWith(
      "Too many attempts. Please wait a while and try again."
    );
    expect(screen.queryByText(/check your email/i)).not.toBeInTheDocument();
  });

  it("shows an error toast when the reset request fails", async () => {
    mockMutateAsync.mockRejectedValue(new Error("500"));
    const toastErrorSpy = vi.spyOn(toast, "error");

    renderForgotPassword();

    await userEvent.type(
      screen.getByLabelText(/email/i),
      "player@example.com"
    );
    await userEvent.click(
      screen.getByRole("button", { name: /send reset link/i })
    );

    expect(toastErrorSpy).toHaveBeenCalledWith("Failed to send reset link");
  });

  it("has a link back to sign in", () => {
    renderForgotPassword();

    const backLink = screen.getByRole("link", { name: /sign in/i });
    expect(backLink).toHaveAttribute("href", "/");
  });
});
