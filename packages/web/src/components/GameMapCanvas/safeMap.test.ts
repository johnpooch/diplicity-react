import { describe, it, expect, afterEach, vi } from "vitest";
import L from "leaflet";
import { createSafeMap } from "./safeMap";

type ZoomAnimation = {
  _animateZoom: (center: L.LatLng, zoom: number, startAnim: boolean) => void;
};

const mountMap = (): L.Map => {
  const container = document.createElement("div");
  Object.defineProperty(container, "clientWidth", { value: 800 });
  Object.defineProperty(container, "clientHeight", { value: 600 });
  document.body.appendChild(container);
  const map = createSafeMap(container, { crs: L.CRS.Simple });
  map.setView([0, 0], 1);
  return map;
};

describe("createSafeMap", () => {
  afterEach(() => {
    vi.useRealTimers();
    document.body.innerHTML = "";
  });

  it("ignores the zoom transition timer left pending by a removed map", () => {
    vi.useFakeTimers();
    const map = mountMap();
    (map as L.Map & ZoomAnimation)._animateZoom(L.latLng(1, 1), 2, true);

    map.remove();

    expect(() => vi.advanceTimersByTime(300)).not.toThrow();
  });

  it("ignores an inertia pan deferred past a removed map", () => {
    const map = mountMap();

    map.remove();

    expect(() => map.panBy([40, 40], { animate: true })).not.toThrow();
  });

  it("still runs the zoom transition on a live map", () => {
    vi.useFakeTimers();
    const map = mountMap();
    const zoomEnd = vi.fn();
    map.on("moveend", zoomEnd);

    (map as L.Map & ZoomAnimation)._animateZoom(L.latLng(1, 1), 2, true);
    vi.advanceTimersByTime(300);

    expect(zoomEnd).toHaveBeenCalled();
    expect(map.getZoom()).toBe(2);
  });

  it("still pans a live map", () => {
    const map = mountMap();
    const before = map.getCenter();

    map.panBy([40, 40], { animate: false });

    expect(map.getCenter()).not.toEqual(before);
  });
});
