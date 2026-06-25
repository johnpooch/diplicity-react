import L from "leaflet";
import type { Point, ViewBox } from "../InteractiveMap/dsvgParser";
import type { GestureType } from "../InteractiveMap/mapTelemetry";
import { toLatLng, viewBoxBounds } from "./leafletCoords";
import type { ProvinceRing } from "./provincePolygons";
import { buildHighlightSvg } from "./highlightSvg";

const MAX_ZOOM_FACTORS = 2;

// In CRS.Simple zoom 2 is 4x the native board size, matching the SVG map's
// maxScale of 4. The cap is absolute rather than relative to the contain fit:
// on tall/narrow viewports the contain fit is far below the fill fit, so a
// relative cap would collapse the usable zoom-in range to almost nothing.
const MAX_ABSOLUTE_ZOOM = 2;

// getBoundsZoom clamps its result to the map's current zoom range, so the floor
// is dropped well below any realistic fit zoom before querying — otherwise the
// default minimum of 0 prevents the negative zoom needed to fit a board that is
// larger than its container, leaving the user unable to zoom out to the whole
// board.
const ZOOM_QUERY_FLOOR = -10;
const FIT_EPSILON = 0.05;

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

const hitTestStyle = (): L.PathOptions => ({
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
  private highlightLayer: L.SVGOverlay | null = null;
  private overlayLayer: L.SVGOverlay | null = null;
  private readonly hitLayer: L.LayerGroup;
  private readonly polygonsByProvince = new Map<string, L.Polygon[]>();
  private provincePaths = new Map<string, string>();

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

  // The board can be viewed in two regimes, mirroring the SVG map: "fill" makes
  // the board cover the whole viewport (clamped to the board edges), "contain"
  // lets the user zoom out until the entire board is visible. fillZoom and
  // containZoom are recomputed for the current container size on every refit.
  private fill = true;
  private fillZoom = 0;
  private containZoom = 0;

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
    const highlightPane = this.map.createPane("highlightMap");
    highlightPane.style.zIndex = "350";
    highlightPane.style.pointerEvents = "none";
    this.map.createPane("overlayMap").style.zIndex = "450";
    this.map.getPane("overlayMap")!.style.pointerEvents = "none";

    this.hitLayer = L.layerGroup().addTo(this.map);

    this.refit();
    this.wireGestures();
  }

  // Recomputes the zoom limits for the current container size and applies the
  // active regime. The board is (re)fitted on the first sizing and on any later
  // resize while the user is still zoomed all the way out, so the whole-board
  // view tracks the container — but a user who has zoomed in is left untouched.
  private refit(): void {
    const size = this.map.getSize();
    if (size.x === 0 || size.y === 0) {
      this.map.fitBounds(this.bounds, { animate: false });
      return;
    }
    this.map.setMinZoom(ZOOM_QUERY_FLOOR);
    this.containZoom = this.map.getBoundsZoom(this.bounds, false);
    this.fillZoom = this.map.getBoundsZoom(this.bounds, true);
    this.map.setMaxZoom(
      Math.max(MAX_ABSOLUTE_ZOOM, this.containZoom + MAX_ZOOM_FACTORS)
    );
    this.applyRegime();
    const fitZoom = this.fill ? this.fillZoom : this.containZoom;
    if (!this.fitted || this.map.getZoom() <= fitZoom + FIT_EPSILON) {
      this.fitToRegime(false);
      this.fitted = true;
    }
  }

  // In fill mode the camera is clamped to the board edges and cannot zoom out
  // past the point where the board fills the viewport. In contain mode the
  // clamp is removed so the whole board can be framed with margins around it.
  private applyRegime(): void {
    if (this.fill) {
      this.map.setMaxBounds(this.bounds);
      this.map.setMinZoom(this.fillZoom);
    } else {
      this.map.setMaxBounds();
      this.map.setMinZoom(this.containZoom);
    }
  }

  private fitToRegime(animate: boolean): void {
    const zoom = this.fill ? this.fillZoom : this.containZoom;
    this.map.setView(this.bounds.getCenter(), zoom, { animate });
  }

  // Animate to the new regime. The zoom floor is dropped to the contain fit for
  // the duration of the transition so that raising the operational minimum
  // (which Leaflet would apply synchronously) does not snap past the animation
  // when zooming back in; the real regime is applied once the view settles.
  setFill(fill: boolean): void {
    if (this.fill === fill) return;
    this.fill = fill;
    this.map.setMaxBounds(fill ? this.bounds : undefined);
    this.map.setMinZoom(this.containZoom);
    this.map.once("zoomend", () => this.applyRegime());
    this.fitToRegime(true);
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

  setProvincePaths(paths: Map<string, string>): void {
    this.provincePaths = paths;
    this.renderHighlight();
  }

  setHitTest(rings: ProvinceRing[]): void {
    this.hitLayer.clearLayers();
    this.polygonsByProvince.clear();
    for (const ring of rings) {
      const polygon = L.polygon(ring.points.map(toLatLng), hitTestStyle());
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
    this.updateCursors();
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
    this.renderHighlight();
  }

  setStyleState(style: StyleState): void {
    this.style = style;
    this.updateCursors();
    this.renderHighlight();
  }

  // The visible highlight is drawn from the exact dSVG province shapes for only
  // the handful of active provinces, so hover/selection match the SVG map rather
  // than showing the decimated hit-test rings.
  private renderHighlight(): void {
    const svg = buildHighlightSvg({
      paths: this.provincePaths,
      viewBox: this.options.viewBox,
      selected: this.style.selected,
      highlighted: this.style.highlighted,
      renderable: this.style.renderable,
      hovered: this.hovered,
    });
    const element = new DOMParser().parseFromString(svg, "image/svg+xml")
      .documentElement as unknown as SVGElement;
    const next = L.svgOverlay(element, this.bounds, {
      interactive: false,
      pane: "highlightMap",
    }).addTo(this.map);
    if (this.highlightLayer) {
      this.map.removeLayer(this.highlightLayer);
    }
    this.highlightLayer = next;
  }

  private updateCursors(): void {
    for (const [province, polygons] of this.polygonsByProvince) {
      const renderable = this.style.renderable.has(province);
      const cursor =
        renderable && this.options.interactive ? "pointer" : "default";
      for (const polygon of polygons) {
        const element = polygon.getElement();
        if (element instanceof SVGElement || element instanceof HTMLElement) {
          element.style.cursor = cursor;
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
