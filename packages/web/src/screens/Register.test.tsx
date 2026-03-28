import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Register } from "./Register";

const mockMutateAsync = vi.fn();
const mockNavigate = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/generated/endpoints", () => ({
  useAuthRegisterCreate: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}));

const renderRegister = () =>
  render(
    <MemoryRouter>
      <Register />
    </MemoryRouter>
  );

describe("Register", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits registration and navigates to check-email", async () => {
    mockMutateAsync.mockResolvedValue({});

    renderRegister();

    await userEvent.type(screen.getByLabelText(/email/i), "new@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "strongpass123");
    await userEvent.type(
      screen.getByLabelText(/confirm password/i),
      "strongpass123"
    );
    await userEvent.type(
      screen.getByLabelText(/display name/i),
      "New Player"
    );
    await userEvent.click(screen.getByRole("button", { name: /register/i }));

    expect(mockMutateAsync).toHaveBeenCalledWith({
      data: {
        email: "new@example.com",
        password: "strongpass123",
        displayName: "New Player",
      },
    });
    expect(mockNavigate).toHaveBeenCalledWith("/check-email");
  });

  it("shows validation error when passwords do not match", async () => {
    renderRegister();

    await userEvent.type(screen.getByLabelText(/email/i), "new@example.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "strongpass123");
    await userEvent.type(
      screen.getByLabelText(/confirm password/i),
      "differentpass"
    );
    await userEvent.type(
      screen.getByLabelText(/display name/i),
      "New Player"
    );
    await userEvent.click(screen.getByRole("button", { name: /register/i }));

    expect(
      await screen.findByText(/passwords do not match/i)
    ).toBeInTheDocument();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });

  it("has a link to the login page", () => {
    renderRegister();

    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toHaveAttribute("href", "/");
  });
});
