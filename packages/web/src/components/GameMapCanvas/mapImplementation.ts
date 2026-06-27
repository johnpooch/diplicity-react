import type { MapImplementation } from "../InteractiveMap/mapTelemetry";

const LEAFLET_VALUES = new Set(["leaflet", "canvas"]);

// Dev-only opt-in for the new Leaflet map. The default stays "svg" so production
// behaviour is unchanged; the new map is selected with `?map=leaflet` (also
// `?map=canvas`) or by setting localStorage["map:impl"]. The query param wins so
// a link can force either implementation regardless of the stored preference.
export const resolveMapImplementation = (): MapImplementation => {
  try {
    const param = new URLSearchParams(window.location.search).get("map");
    if (param !== null) {
      return LEAFLET_VALUES.has(param) ? "leaflet" : "svg";
    }
    const stored = window.localStorage.getItem("map:impl");
    if (stored !== null && LEAFLET_VALUES.has(stored)) {
      return "leaflet";
    }
  } catch {
    return "svg";
  }
  return "svg";
};
