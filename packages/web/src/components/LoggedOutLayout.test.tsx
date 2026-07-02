import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router";
import { describe, it, expect, vi, beforeAll } from "vitest";

import { LoggedOutLayout } from "./LoggedOutLayout";

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

const renderLayout = () =>
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route
          path="/"
          element={
            <LoggedOutLayout>
              <div>content</div>
            </LoggedOutLayout>
          }
        />
        <Route path="/login" element={<div>login screen</div>} />
        <Route path="/register" element={<div>register screen</div>} />
      </Routes>
    </MemoryRouter>
  );

describe("LoggedOutLayout", () => {
  it("renders its children", () => {
    renderLayout();
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("navigates to /login when a 'Sign in' control is clicked", async () => {
    renderLayout();

    await userEvent.click(
      screen.getAllByRole("button", { name: /sign in/i })[0]
    );

    expect(screen.getByText("login screen")).toBeInTheDocument();
  });

  it("navigates to /register when a 'Create account' control is clicked", async () => {
    renderLayout();

    await userEvent.click(
      screen.getAllByRole("button", { name: /create account/i })[0]
    );

    expect(screen.getByText("register screen")).toBeInTheDocument();
  });
});
