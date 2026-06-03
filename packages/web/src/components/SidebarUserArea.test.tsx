import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { MemoryRouter } from "react-router";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

const mockLoggedIn = vi.fn(() => false);

vi.mock("@/auth", () => ({
  useAuth: () => ({
    loggedIn: mockLoggedIn(),
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/api/generated/endpoints", () => ({
  useUserRetrieveSuspense: () => ({
    data: { name: "Test User", picture: null },
  }),
}));

import { SidebarProvider } from "@/components/ui/sidebar";
import { SidebarUserArea } from "./SidebarUserArea";

const renderComponent = () =>
  render(
    <MemoryRouter>
      <SidebarProvider>
        <SidebarUserArea />
      </SidebarProvider>
    </MemoryRouter>
  );

describe("SidebarUserArea", () => {
  it("shows sign-in button when not logged in", () => {
    mockLoggedIn.mockReturnValue(false);
    renderComponent();

    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("shows user profile when logged in", () => {
    mockLoggedIn.mockReturnValue(true);
    renderComponent();

    expect(screen.getByText("Test User")).toBeInTheDocument();
  });
});
