import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import L from "leaflet";
import { GameMapController } from "./GameMapController";

type TestableController = {
  map: L.Map;
  preparedBaseCopies: Set<number>;
};

const createContainer = (): HTMLElement => {
  const container = document.createElement("div");
  Object.defineProperty(container, "clientWidth", { value: 800 });
  Object.defineProperty(container, "clientHeight", { value: 600 });
  document.body.appendChild(container);
  return container;
};

const createCanvas = (): HTMLCanvasElement => {
  const canvas = document.createElement("canvas");
  canvas.width = 400;
  canvas.height = 200;
  return canvas;
};

describe("GameMapController horizontal wrapping", () => {
  let callbacks: Map<number, FrameRequestCallback>;
  let nextAnimationFrameId: number;

  beforeEach(() => {
    callbacks = new Map();
    nextAnimationFrameId = 1;
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      const id = nextAnimationFrameId++;
      callbacks.set(id, callback);
      return id;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation((id) => {
      callbacks.delete(id);
    });
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  const flushAnimationFrame = (): void => {
    const current = [...callbacks.values()];
    callbacks.clear();
    for (const callback of current) callback(performance.now());
  };

  const createController = (container: HTMLElement): GameMapController =>
    new GameMapController(container, {
      viewBox: { minX: 0, minY: 0, width: 1000, height: 600 },
      horizontalWrap: true,
      mode: "pannable",
      enableHover: false,
      onGesture: vi.fn(),
    });

  it("paints the centre before allocating either neighbour", () => {
    const container = createContainer();
    const controller = createController(container);

    controller.setBase(createCanvas());

    expect(container.querySelectorAll("canvas.leaflet-image-layer")).toHaveLength(1);
    expect(
      [...(controller as unknown as TestableController).preparedBaseCopies]
    ).toEqual([0]);

    flushAnimationFrame();
    expect(container.querySelectorAll("canvas.leaflet-image-layer")).toHaveLength(1);

    flushAnimationFrame();
    expect(container.querySelectorAll("canvas.leaflet-image-layer")).toHaveLength(2);

    flushAnimationFrame();
    expect(container.querySelectorAll("canvas.leaflet-image-layer")).toHaveLength(3);

    controller.destroy();
  });

  it("prepares the approached neighbour first when dragging starts early", () => {
    const container = createContainer();
    const controller = createController(container);
    const testable = controller as unknown as TestableController;
    controller.setBase(createCanvas());

    const center = testable.map.getCenter();
    testable.map.fire("dragstart");
    testable.map.setView([center.lat, center.lng + 100], testable.map.getZoom(), {
      animate: false,
    });
    testable.map.fire("dragend");

    flushAnimationFrame();
    flushAnimationFrame();

    expect([...testable.preparedBaseCopies]).toEqual([0, 1]);

    controller.destroy();
  });
});
