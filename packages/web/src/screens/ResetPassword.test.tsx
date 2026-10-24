import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { toast } from "sonner";
import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse } from "axios";
import { ResetPassword } from "./ResetPassword";

const mockMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useAuthPasswordResetConfirmCreate: () => ({
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

const renderResetPassword = () =>
  render(
    <MemoryRouter initialEntries={["/reset-password?uid=abc&token=def"]}>
      <ResetPassword />
    </MemoryRouter>
  );

const submitPassword = async (password: string) => {
  await userEvent.type(screen.getByLabelText(/new password/i), password);
  await userEvent.type(screen.getByLabelText(/confirm password/i), password);
  await userEvent.click(
    screen.getByRole("button", { name: /reset password/i })
  );
};

describe("ResetPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits the new password and shows confirmation", async () => {
    mockMutateAsync.mockResolvedValue({});

    renderResetPassword();
    await submitPassword("strongpass123");

    expect(mockMutateAsync).toHaveBeenCalledWith({
      data: {
        uid: "abc",
        token: "def",
        newPassword: "strongpass123",
        confirmPassword: "strongpass123",
      },
    });
    expect(await screen.findByText("Password reset!")).toBeInTheDocument();
  });

  it("keeps the form open with the server's password validation error", async () => {
    mockMutateAsync.mockRejectedValue({
      response: { data: { newPassword: ["This password is too common."] } },
    });

    renderResetPassword();
    await submitPassword("password123");

    expect(
      await screen.findByText("This password is too common.")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeInTheDocument();
  });

  it("keeps the form open and tells the user to wait when rate limited", async () => {
    mockMutateAsync.mockRejectedValue(rateLimitedError());
    const toastErrorSpy = vi.spyOn(toast, "error");

    renderResetPassword();
    await submitPassword("strongpass123");

    expect(toastErrorSpy).toHaveBeenCalledWith(
      "Too many attempts. Please wait a while and try again."
    );
    expect(
      screen.getByRole("button", { name: /reset password/i })
    ).toBeInTheDocument();
  });

  it("shows the invalid link state for other failures", async () => {
    mockMutateAsync.mockRejectedValue({
      response: { data: { nonFieldErrors: ["Invalid or expired reset link."] } },
    });

    renderResetPassword();
    await submitPassword("strongpass123");

    expect(await screen.findByText("Reset failed")).toBeInTheDocument();
  });
});
