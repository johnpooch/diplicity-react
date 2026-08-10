import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { NotFoundNotice } from "./NotFoundNotice";

describe("NotFoundNotice", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...originalLocation, href: "/game/some-game/phase/1" },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
  });

  it("navigates home when the user taps Go to my games", async () => {
    render(<NotFoundNotice />);

    await userEvent.click(screen.getByRole("button", { name: "Go to my games" }));

    expect(window.location.href).toBe("/");
  });

  it("does not offer a retry", () => {
    render(<NotFoundNotice />);

    expect(
      screen.queryByRole("button", { name: "Try Again" })
    ).not.toBeInTheDocument();
  });

  it("renders the full-screen variant heading", () => {
    render(<NotFoundNotice fullScreen />);

    expect(
      screen.getByRole("heading", { name: "This game is no longer available" })
    ).toBeInTheDocument();
  });
});
