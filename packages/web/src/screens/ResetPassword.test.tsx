import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ResetPassword } from "./ResetPassword";

const mockMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useAuthPasswordResetConfirmCreate: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

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

  it("shows the invalid link state for other failures", async () => {
    mockMutateAsync.mockRejectedValue({
      response: { data: { nonFieldErrors: ["Invalid or expired reset link."] } },
    });

    renderResetPassword();
    await submitPassword("strongpass123");

    expect(await screen.findByText("Reset failed")).toBeInTheDocument();
  });
});
