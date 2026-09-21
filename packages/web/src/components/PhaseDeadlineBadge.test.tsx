import { render, screen } from "@testing-library/react";
import { afterAll, beforeAll, describe, it, expect, vi } from "vitest";
import { PhaseDeadlineBadge } from "./PhaseDeadlineBadge";
import { TooltipProvider } from "./ui/tooltip";
import { makePhase } from "@/mocks/fixtures/builders";

class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

beforeAll(() => vi.stubGlobal("ResizeObserver", ResizeObserverMock));
afterAll(() => vi.unstubAllGlobals());

const renderBadge = (ui: React.ReactElement) =>
  render(<TooltipProvider>{ui}</TooltipProvider>);

describe("PhaseDeadlineBadge", () => {
  it("renders the remaining time for an active phase", () => {
    renderBadge(
      <PhaseDeadlineBadge
        phase={makePhase(101, 1, { remainingTime: 22 * 60 * 60 })}
        isPaused={false}
      />
    );

    expect(screen.getByText("22h 0m remaining")).toBeInTheDocument();
  });

  it("renders nothing for a resolved phase", () => {
    const { container } = renderBadge(
      <PhaseDeadlineBadge
        phase={makePhase(101, 1, { status: "completed" })}
        isPaused={false}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders the paused state when the game is paused", () => {
    renderBadge(
      <PhaseDeadlineBadge phase={makePhase(101, 1)} isPaused={true} />
    );

    expect(screen.getByText("Paused")).toBeInTheDocument();
    expect(screen.queryByText(/remaining/)).not.toBeInTheDocument();
  });

  it("keeps the deadline tooltip reachable by keyboard", () => {
    renderBadge(
      <PhaseDeadlineBadge phase={makePhase(101, 1)} isPaused={false} />
    );

    expect(screen.getByText(/remaining/)).toHaveAttribute("tabindex", "0");
  });
});
