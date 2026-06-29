import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ExpandableMapPreview } from "./ExpandableMapPreview";
import type { Variant, VariantTemplatePhase } from "@/api/generated/endpoints";

vi.mock("./MapView", () => ({
  MapView: ({ mode }: { mode?: string }) => (
    <div data-testid={`map-${mode ?? "interactive"}`} />
  ),
}));

const variant = {
  id: "classical",
  name: "Classical",
  nations: [],
  svgUrl: "https://example.com/map.svg",
} as Pick<Variant, "id" | "name" | "nations" | "svgUrl">;

const phase = {} as VariantTemplatePhase;

describe("ExpandableMapPreview", () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class {
      callback: ResizeObserverCallback;
      constructor(callback: ResizeObserverCallback) {
        this.callback = callback;
      }
      observe() {
        this.callback(
          [{ contentRect: { width: 800, height: 600 } } as ResizeObserverEntry],
          this
        );
      }
      unobserve() {}
      disconnect() {}
    };
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

  it("renders the static thumbnail with an expand control and no dialog initially", () => {
    render(<ExpandableMapPreview variant={variant} phase={phase} />);

    expect(screen.getByTestId("map-static")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Expand map preview" })
    ).toBeInTheDocument();
    expect(screen.queryByTestId("map-pannable")).not.toBeInTheDocument();
  });

  it("opens a pannable dialog with only a close button when clicked", () => {
    render(<ExpandableMapPreview variant={variant} phase={phase} />);

    fireEvent.click(screen.getByRole("button", { name: "Expand map preview" }));

    expect(screen.getByTestId("map-pannable")).toBeInTheDocument();
    expect(screen.getByText("Classical map")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Zoom in" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Zoom out" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Reset zoom" })
    ).not.toBeInTheDocument();
  });
});
