import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ForgotPassword } from "./ForgotPassword";

const mockMutateAsync = vi.fn();

vi.mock("@/api/generated/endpoints", () => ({
  useAuthPasswordResetCreate: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

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

  it("has a link back to sign in", () => {
    renderForgotPassword();

    const backLink = screen.getByRole("link", { name: /sign in/i });
    expect(backLink).toHaveAttribute("href", "/");
  });
});
