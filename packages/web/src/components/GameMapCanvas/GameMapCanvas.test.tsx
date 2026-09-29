import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GameMapCanvas, type GameMapCanvasProps } from "./GameMapCanvas";

const testState = vi.hoisted(() => ({
  controllers: [] as Array<{
    destroy: ReturnType<typeof vi.fn>;
    focusProvinces: ReturnType<typeof vi.fn>;
    invalidateSize: ReturnType<typeof vi.fn>;
    setBase: ReturnType<typeof vi.fn>;
    setFill: ReturnType<typeof vi.fn>;
    setHitTest: ReturnType<typeof vi.fn>;
    setOverlay: ReturnType<typeof vi.fn>;
    setProvincePaths: ReturnType<typeof vi.fn>;
    setStyleState: ReturnType<typeof vi.fn>;
  }>,
}));

vi.mock("./GameMapController", () => ({
  GameMapController: class {
    destroy = vi.fn();
    focusProvinces = vi.fn();
    invalidateSize = vi.fn();
    setBase = vi.fn();
    setFill = vi.fn();
    setHitTest = vi.fn();
    setOverlay = vi.fn();
    setProvincePaths = vi.fn();
    setStyleState = vi.fn();

    constructor() {
      testState.controllers.push(this);
    }
  },
}));

vi.mock("../../hooks/useDsvg", () => ({
  useDsvg: () => ({
    data: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
      <g id="provinces" style="display:none"><path id="alpha" d="M0 0 L50 0 L50 50 L0 50 Z"/></g>
      <g id="unit-positions" style="display:none"><circle id="alpha" cx="25" cy="25"/></g>
    </svg>`,
  }),
}));

vi.mock("./rasterizeSvg", () => ({
  rasterizeSvg: vi.fn(() => new Promise<HTMLCanvasElement>(() => {})),
}));

vi.mock("../InteractiveMap/mapTelemetry", () => ({
  recordGesture: vi.fn(),
  recordInitialRender: vi.fn(),
  recordRasterFailure: vi.fn(),
}));

vi.mock("../../utils/platform", () => ({
  isNativePlatform: () => false,
}));

const phase = {
  units: [],
  supplyCenters: [],
} as unknown as GameMapCanvasProps["phase"];

const baseVariant = {
  id: "test",
  nations: [],
  svgUrl: "/test.svg",
  mapOptions: { horizontalWrap: false },
  unitScaling: 1,
} as GameMapCanvasProps["variant"];

describe("GameMapCanvas controller replacement", () => {
  it("rehydrates interaction state when horizontal wrapping changes", () => {
    testState.controllers.length = 0;
    const { rerender } = render(
      <GameMapCanvas
        variant={baseVariant}
        phase={phase}
        orders={[]}
        selected={["alpha"]}
        highlighted={["alpha"]}
        renderableProvinces={["alpha"]}
        focus={["alpha"]}
      />
    );

    expect(testState.controllers).toHaveLength(1);
    const first = testState.controllers[0];

    rerender(
      <GameMapCanvas
        variant={{
          ...baseVariant,
          mapOptions: { horizontalWrap: true },
        }}
        phase={phase}
        orders={[]}
        selected={["alpha"]}
        highlighted={["alpha"]}
        renderableProvinces={["alpha"]}
        focus={["alpha"]}
      />
    );

    expect(first.destroy).toHaveBeenCalledOnce();
    expect(testState.controllers).toHaveLength(2);
    const replacement = testState.controllers[1];
    expect(replacement.setProvincePaths).toHaveBeenCalled();
    expect(replacement.setHitTest).toHaveBeenCalled();
    expect(replacement.setFill).toHaveBeenCalledWith(false);
    expect(replacement.focusProvinces).toHaveBeenCalledWith(["alpha"]);
    expect(replacement.setStyleState).toHaveBeenCalledWith({
      selected: new Set(["alpha"]),
      highlighted: new Set(["alpha"]),
      renderable: new Set(["alpha"]),
    });
  });
});
