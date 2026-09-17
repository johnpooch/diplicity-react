import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, it, expect, beforeAll } from "vitest";
import { GameDetailAppBar } from "./AppBar";

vi.mock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const setTitleWidths = (scrollWidth: number, clientWidth: number) => {
  const title = screen.getByRole("heading");
  Object.defineProperty(title, "scrollWidth", {
    configurable: true,
    value: scrollWidth,
  });
  Object.defineProperty(title, "clientWidth", {
    configurable: true,
    value: clientWidth,
  });
  return title;
};

const renderAppBar = (title: string) =>
  render(
    <MemoryRouter>
      <GameDetailAppBar title={title} />
    </MemoryRouter>
  );

describe("GameDetailAppBar title tooltip", () => {
  it("shows a tooltip with the full title when the title is truncated", async () => {
    renderAppBar("A very long game title that does not fit");
    const title = setTitleWidths(200, 100);

    await userEvent.click(title);

    expect(screen.getByRole("tooltip")).toBeInTheDocument();
  });

  it("does not show a tooltip when the title is not truncated", async () => {
    renderAppBar("Short title");
    const title = setTitleWidths(100, 100);

    await userEvent.click(title);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
