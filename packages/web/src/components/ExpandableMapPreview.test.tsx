import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { ExpandableMapPreview } from "./ExpandableMapPreview";
import type { Variant, VariantTemplatePhase } from "@/api/generated/endpoints";

vi.mock("./MapPreview", () => ({
  MapPreview: () => <div data-testid="map-preview" />,
}));

vi.mock("react-zoom-pan-pinch", () => ({
  TransformWrapper: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transform-wrapper">{children}</div>
  ),
  TransformComponent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="transform-component">{children}</div>
  ),
}));

vi.mock("../hooks/useDsvg", () => ({
  useDsvg: () => ({ data: '<svg viewBox="0 0 100 100"></svg>' }),
}));

vi.mock("./InteractiveMap/mapRenderer", () => ({
  DiplicityMap: class {
    render() {
      return "<svg></svg>";
    }
  },
}));

vi.mock("./InteractiveMap/toRenderState", () => ({
  toRenderState: () => ({}),
}));

const variant = {
  name: "Classical",
  nations: [],
  svgUrl: "https://example.com/map.svg",
} as Pick<Variant, "name" | "nations" | "svgUrl">;

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

  it("renders the preview with an expand control and no dialog initially", () => {
    render(<ExpandableMapPreview variant={variant} phase={phase} />);

    expect(screen.getByTestId("map-preview")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Expand map preview" })
    ).toBeInTheDocument();
    expect(screen.queryByTestId("transform-wrapper")).not.toBeInTheDocument();
  });

  it("opens a zoomable dialog with only a close button when clicked", () => {
    render(<ExpandableMapPreview variant={variant} phase={phase} />);

    fireEvent.click(screen.getByRole("button", { name: "Expand map preview" }));

    expect(screen.getByTestId("transform-wrapper")).toBeInTheDocument();
    expect(screen.getByText("Classical map")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Zoom in" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Zoom out" })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Reset zoom" })
    ).not.toBeInTheDocument();
  });
});
