import L from "leaflet";
import type { Point, ViewBox } from "../InteractiveMap/dsvgParser";
import type { GestureType } from "../InteractiveMap/mapTelemetry";
import { toLatLng, viewBoxBounds } from "./leafletCoords";
import type { ProvinceRing } from "./provincePolygons";

const MAX_ZOOM_FACTORS = 2;

const SELECTED_STROKE = "#FFFFFF";
const SELECTED_FILL_OPACITY = 0.8;
const HOVER_FILL_OPACITY = 0.6;
const HIGHLIGHTED_FILL_OPACITY = 0.25;
const ACTIVE_STROKE_WIDTH = 5;

export type StyleState = {
  selected: Set<string>;
  highlighted: Set<string>;
  renderable: Set<string>;
};

export type GestureRecord = {
  gestureType: GestureType;
  durationMs: number;
  frameMs: number[];
};

type ControllerOptions = {
  viewBox: ViewBox;
  interactive: boolean;
  enableHover: boolean;
  onClickProvince?: (province: string, position: Point) => void;
  onGesture: (record: GestureRecord) => void;
};

const emptyStyle = (): L.PathOptions => ({
  stroke: false,
  fill: true,
  fillColor: "#000000",
  fillOpacity: 0,
});

export class GameMapController {
  private readonly map: L.Map;
  private readonly bounds: L.LatLngBounds;
  private readonly options: ControllerOptions;

  private baseLayer: L.ImageOverlay | null = null;
  private overlayLayer: L.SVGOverlay | null = null;
  private readonly hitLayer: L.LayerGroup;
  private readonly polygonsByProvince = new Map<string, L.Polygon[]>();

  private style: StyleState = {
    selected: new Set(),
    highlighted: new Set(),
    renderable: new Set(),
  };
  private hovered: string | null = null;

  private gestureType: GestureType | null = null;
  private gestureStart = 0;
  private frameTimes: number[] = [];
  private lastFrame: number | null = null;
  private rafId: number | null = null;
  private fitted = false;

  constructor(container: HTMLElement, options: ControllerOptions) {
    this.options = options;
    this.bounds = L.latLngBounds(viewBoxBounds(options.viewBox));

    this.map = L.map(container, {
      crs: L.CRS.Simple,
      attributionControl: false,
      zoomControl: false,
      zoomSnap: 0,
      zoomDelta: 0.6,
      wheelPxPerZoomLevel: 120,
      maxBoundsViscosity: 1,
      doubleClickZoom: false,
    });

    this.map.createPane("baseMap").style.zIndex = "200";
    this.map.createPane("overlayMap").style.zIndex = "450";
    this.map.getPane("overlayMap")!.style.pointerEvents = "none";

    this.hitLayer = L.layerGroup().addTo(this.map);

    this.refit();
    this.wireGestures();
  }

  // Clamps the zoom range to the board and fits the whole board on the first
  // sizing. Later resizes only recompute the limits — they never yank the user's
  // current zoom/pan back to the fitted view.
  private refit(): void {
    const size = this.map.getSize();
    if (size.x === 0 || size.y === 0) {
      this.map.fitBounds(this.bounds, { animate: false });
      return;
    }
    const fitZoom = this.map.getBoundsZoom(this.bounds, false);
    this.map.setMinZoom(fitZoom);
    this.map.setMaxZoom(fitZoom + MAX_ZOOM_FACTORS);
    this.map.setMaxBounds(this.bounds);
    if (!this.fitted) {
      this.map.fitBounds(this.bounds, { animate: false });
      this.fitted = true;
    }
  }

  private beginGesture(type: GestureType): void {
    if (this.gestureType !== null) return;
    this.gestureType = type;
    this.gestureStart = performance.now();
    this.frameTimes = [];
    this.lastFrame = null;
    const tick = (): void => {
      if (this.gestureType === null) return;
      const now = performance.now();
      if (this.lastFrame !== null) {
        this.frameTimes.push(now - this.lastFrame);
      }
      this.lastFrame = now;
      this.rafId = requestAnimationFrame(tick);
    };
    this.rafId = requestAnimationFrame(tick);
  }

  private endGesture(): void {
    if (this.gestureType === null) return;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.options.onGesture({
      gestureType: this.gestureType,
      durationMs: performance.now() - this.gestureStart,
      frameMs: this.frameTimes,
    });
    this.gestureType = null;
    this.frameTimes = [];
    this.lastFrame = null;
  }

  private wireGestures(): void {
    this.map.on("zoomstart", () => this.beginGesture("zoom"));
    this.map.on("dragstart", () => this.beginGesture("pan"));
    this.map.on("zoomend", () => this.endGesture());
    this.map.on("dragend", () => this.endGesture());
    this.map.on("moveend", () => this.endGesture());
  }

  setBase(pngUrl: string): void {
    const next = L.imageOverlay(pngUrl, this.bounds, {
      interactive: false,
      pane: "baseMap",
    }).addTo(this.map);
    if (this.baseLayer) {
      this.map.removeLayer(this.baseLayer);
    }
    this.baseLayer = next;
  }

  setOverlay(svg: string): void {
    const element = new DOMParser().parseFromString(svg, "image/svg+xml")
      .documentElement as unknown as SVGElement;
    const next = L.svgOverlay(element, this.bounds, {
      interactive: false,
      pane: "overlayMap",
    }).addTo(this.map);
    if (this.overlayLayer) {
      this.map.removeLayer(this.overlayLayer);
    }
    this.overlayLayer = next;
  }

  setHitTest(rings: ProvinceRing[]): void {
    this.hitLayer.clearLayers();
    this.polygonsByProvince.clear();
    for (const ring of rings) {
      const polygon = L.polygon(
        ring.points.map(toLatLng),
        emptyStyle()
      );
      polygon.on("click", (event) => this.handleClick(ring.id, event));
      if (this.options.enableHover) {
        polygon.on("mouseover", () => this.handleHover(ring.id));
        polygon.on("mouseout", () => this.handleHover(null));
      }
      polygon.addTo(this.hitLayer);
      const existing = this.polygonsByProvince.get(ring.id);
      if (existing) {
        existing.push(polygon);
      } else {
        this.polygonsByProvince.set(ring.id, [polygon]);
      }
    }
    this.applyStyles();
  }

  private handleClick(province: string, event: L.LeafletMouseEvent): void {
    if (!this.options.interactive) return;
    const original = event.originalEvent;
    this.options.onClickProvince?.(province, {
      x: original.clientX,
      y: original.clientY,
    });
  }

  private handleHover(province: string | null): void {
    if (!this.options.interactive) return;
    if (this.hovered === province) return;
    this.hovered = province;
    this.applyStyles();
  }

  setStyleState(style: StyleState): void {
    this.style = style;
    this.applyStyles();
  }

  private styleFor(province: string): L.PathOptions {
    const selected = this.style.selected.has(province);
    const highlighted = this.style.highlighted.has(province);
    const hovered =
      this.hovered === province && this.style.renderable.has(province);

    const activeFill = (fillOpacity: number): L.PathOptions => ({
      stroke: true,
      color: SELECTED_STROKE,
      weight: ACTIVE_STROKE_WIDTH,
      fill: true,
      fillColor: "#FFFFFF",
      fillOpacity,
      fillRule: "evenodd",
    });

    if (selected) return activeFill(SELECTED_FILL_OPACITY);
    if (hovered) return activeFill(HOVER_FILL_OPACITY);
    if (highlighted) return activeFill(HIGHLIGHTED_FILL_OPACITY);
    return emptyStyle();
  }

  private applyStyles(): void {
    for (const [province, polygons] of this.polygonsByProvince) {
      const style = this.styleFor(province);
      const renderable = this.style.renderable.has(province);
      for (const polygon of polygons) {
        polygon.setStyle(style);
        const element = polygon.getElement();
        if (element instanceof SVGElement || element instanceof HTMLElement) {
          element.style.cursor =
            renderable && this.options.interactive ? "pointer" : "default";
        }
      }
    }
  }

  invalidateSize(): void {
    this.map.invalidateSize({ animate: false });
    this.refit();
  }

  destroy(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
    }
    this.map.remove();
  }
}
