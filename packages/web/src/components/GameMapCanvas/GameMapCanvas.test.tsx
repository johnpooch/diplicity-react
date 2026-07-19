import { render, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { GameMapCanvas, type GameMapCanvasProps } from "./GameMapCanvas";

const { mockUseDsvg, mockControllerInstances, rasterDeferreds } = vi.hoisted(
  () => ({
    mockUseDsvg: vi.fn(),
    mockControllerInstances: [] as Array<Record<string, ReturnType<typeof vi.fn>>>,
    rasterDeferreds: [] as Array<{
      resolve: (url: string) => void;
      reject: (error: Error) => void;
    }>,
  })
);

vi.mock("../../hooks/useDsvg", () => ({
  useDsvg: () => mockUseDsvg(),
}));

vi.mock("../../utils/platform", () => ({
  isNativePlatform: () => false,
}));

vi.mock("../InteractiveMap/dsvgParser", () => ({
  parseDsvg: () => ({
    viewBox: { x: 0, y: 0, width: 100, height: 100 },
    provincePaths: new Map(),
    namedCoastPaths: new Map(),
  }),
}));

vi.mock("../InteractiveMap/mapRenderer", () => ({
  DiplicityMap: class {},
}));

vi.mock("../InteractiveMap/toRenderState", () => ({
  toRenderState: (_variant: unknown, phase: { key?: string }) => ({
    key: phase.key,
  }),
}));

vi.mock("../InteractiveMap/mapTelemetry", () => ({
  recordGesture: vi.fn(),
  recordInitialRender: vi.fn(),
  recordRasterFailure: vi.fn(),
}));

vi.mock("./mapSvgLayers", () => ({
  renderSplitSvg: (_renderer: unknown, state: { key?: string }) => ({
    base: `<svg data-key="${state.key ?? ""}"/>`,
    overlay: "<svg/>",
  }),
}));

vi.mock("./provincePolygons", () => ({
  buildProvinceRings: () => [],
}));

vi.mock("./rasterizeSvg", () => ({
  rasterizeSvg: () =>
    new Promise<string>((resolve, reject) => {
      rasterDeferreds.push({ resolve, reject });
    }),
}));

vi.mock("./GameMapController", () => ({
  GameMapController: class {
    setBase = vi.fn();
    setOverlay = vi.fn();
    setHitTest = vi.fn();
    setProvincePaths = vi.fn();
    setStyleState = vi.fn();
    setFill = vi.fn();
    focusProvinces = vi.fn();
    invalidateSize = vi.fn();
    destroy = vi.fn();

    constructor() {
      mockControllerInstances.push(
        this as unknown as Record<string, ReturnType<typeof vi.fn>>
      );
    }
  },
}));

beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
  URL.createObjectURL = vi.fn(() => "blob:mock");
  URL.revokeObjectURL = vi.fn();
});

beforeEach(() => {
  mockControllerInstances.length = 0;
  rasterDeferreds.length = 0;
});

const baseProps: GameMapCanvasProps = {
  variant: { id: "standard", nations: [], svgUrl: "/variants/standard/svg/" },
  phase: {} as GameMapCanvasProps["phase"],
  orders: [],
  selected: [],
};

const querySkeleton = (container: HTMLElement) =>
  container.querySelector('[data-slot="skeleton"]');

describe("GameMapCanvas", () => {
  it("shows a skeleton while the dsvg is loading", () => {
    mockUseDsvg.mockReturnValue({ data: undefined });

    const { container } = render(<GameMapCanvas {...baseProps} />);

    expect(querySkeleton(container)).not.toBeNull();
    expect(mockControllerInstances).toHaveLength(0);
  });

  it("removes the skeleton once the first base raster lands", async () => {
    mockUseDsvg.mockReturnValue({ data: "<svg/>" });

    const { container } = render(<GameMapCanvas {...baseProps} />);

    expect(querySkeleton(container)).not.toBeNull();
    await waitFor(() => expect(rasterDeferreds).toHaveLength(1));

    rasterDeferreds[0].resolve("blob:base");

    await waitFor(() => expect(querySkeleton(container)).toBeNull());
    expect(mockControllerInstances[0].setBase).toHaveBeenCalledWith("blob:base");
  });

  it("does not show the skeleton again while a later phase re-rasterises", async () => {
    mockUseDsvg.mockReturnValue({ data: "<svg/>" });

    const { container, rerender } = render(<GameMapCanvas {...baseProps} />);
    await waitFor(() => expect(rasterDeferreds).toHaveLength(1));
    rasterDeferreds[0].resolve("blob:base");
    await waitFor(() => expect(querySkeleton(container)).toBeNull());

    rerender(
      <GameMapCanvas
        {...baseProps}
        phase={{ key: "next" } as unknown as GameMapCanvasProps["phase"]}
      />
    );

    await waitFor(() => expect(rasterDeferreds).toHaveLength(2));
    expect(querySkeleton(container)).toBeNull();
  });
});
