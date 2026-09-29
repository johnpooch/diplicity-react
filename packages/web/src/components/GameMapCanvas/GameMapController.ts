import L from "leaflet";
import type { Point, ViewBox } from "../InteractiveMap/dsvgParser";
import type { GestureType } from "../InteractiveMap/mapTelemetry";
import { shiftedViewBoxBounds, toLatLng, viewBoxBounds } from "./leafletCoords";
import type { ProvinceRing } from "./provincePolygons";
import { focusBounds } from "./focusBounds";
import { buildHighlightSvg } from "./highlightSvg";
import {
  nearestWorldCopyIndex,
  WORLD_COPY_INDEXES,
  wrappedXNear,
} from "../InteractiveMap/mapWrap";
import { createLoadingSpinnerElement } from "../ui/loading-spinner";
import { createSafeMap } from "./safeMap";

export type MapMode = "static" | "pannable" | "interactive";

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

// Zoom levels applied per pixel of wheel delta by the custom wheel handler.
// Leaflet's built-in scroll-wheel pipeline divides the delta by a Mac-retina
// factor of devicePixelRatio*3 and then runs it through a sigmoid that crushes
// small deltas, which makes trackpad pinch crawl. The custom handler maps delta
// straight to zoom instead. WHEEL_MAX_STEP caps a single mouse-wheel notch so
// it does not leap across zoom levels.
const WHEEL_ZOOM_SPEED = 0.005;
const WHEEL_MAX_STEP = 0.5;

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
  horizontalWrap: boolean;
  mode: MapMode;
  enableHover: boolean;
  maxZoomFactor?: number;
  initialFill?: boolean;
  forceCompositeOnBase?: boolean;
  onClickProvince?: (province: string, position: Point) => void;
  onGesture: (record: GestureRecord) => void;
};

const hitTestStyle = (): L.PathOptions => ({
  stroke: false,
  fill: true,
  fillColor: "#000000",
  fillOpacity: 0,
});

const wrapLoadingIcon = (): L.DivIcon =>
  L.divIcon({
    className: "map-wrap-loading-icon",
    html: createLoadingSpinnerElement(),
    iconSize: [64, 64],
    iconAnchor: [32, 32],
  });

const CanvasOverlay = L.ImageOverlay.extend({
  _initImage(this: { _url: HTMLCanvasElement; _image: HTMLCanvasElement; _zoomAnimated: boolean }) {
    const canvas = this._url;
    this._image = canvas;
    canvas.classList.add("leaflet-image-layer");
    if (this._zoomAnimated) {
      canvas.classList.add("leaflet-zoom-animated");
    }
    canvas.onselectstart = () => false;
    canvas.onmousemove = () => false;
  },
}) as unknown as new (
  canvas: HTMLCanvasElement,
  bounds: L.LatLngBoundsExpression,
  options?: L.ImageOverlayOptions
) => L.ImageOverlay;

export class GameMapController {
  private readonly map: L.Map;
  private readonly bounds: L.LatLngBounds;
  private readonly verticalBounds: L.LatLngBounds;
  private readonly copyBounds: L.LatLngBounds[];
  private readonly options: ControllerOptions;
  private readonly wrapLoadingMarker: L.Marker | null;

  private baseLayers: L.ImageOverlay[] = [];
  private highlightLayers: L.SVGOverlay[] = [];
  private overlayLayers: L.SVGOverlay[] = [];
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

  private baseReady = false;

  private readonly container: HTMLElement;
  private wheelDelta = 0;
  private wheelPoint: L.Point | null = null;
  private wheelRaf: number | null = null;
  private compositeRaf: number | null = null;

  constructor(container: HTMLElement, options: ControllerOptions) {
    this.options = options;
    this.container = container;
    this.fill = options.initialFill ?? true;
    this.bounds = L.latLngBounds(viewBoxBounds(options.viewBox));
    this.verticalBounds = L.latLngBounds(
      [this.bounds.getSouth(), -10_000_000],
      [this.bounds.getNorth(), 10_000_000]
    );
    const copyIndexes = options.horizontalWrap ? WORLD_COPY_INDEXES : [0];
    this.copyBounds = copyIndexes.map((index) =>
      L.latLngBounds(
        shiftedViewBoxBounds(options.viewBox, index * options.viewBox.width)
      )
    );

    const crs = options.horizontalWrap
      ? (L.Util.extend({}, L.CRS.Simple, {
          wrapLng: [
            options.viewBox.minX,
            options.viewBox.minX + options.viewBox.width,
          ],
        }) as L.CRS)
      : L.CRS.Simple;

    this.map = createSafeMap(container, {
      crs,
      attributionControl: false,
      zoomControl: false,
      zoomSnap: 0,
      zoomDelta: 0.6,
      // Wheel zoom is handled manually (see onWheel) to get a responsive
      // trackpad pinch on desktop, so Leaflet's own scroll-wheel handler is off.
      scrollWheelZoom: false,
      maxBoundsViscosity: 1,
      // Clamp zoom to the limits live during a pinch instead of overshooting and
      // animating back, so a touch pinch does not leave the map in a settle
      // animation that blocks the pan that follows it.
      bounceAtZoomLimits: false,
      doubleClickZoom: false,
    });

    this.map.createPane("baseMap").style.zIndex = "200";
    const highlightPane = this.map.createPane("highlightMap");
    highlightPane.style.zIndex = "350";
    highlightPane.style.pointerEvents = "none";
    const overlayPane = this.map.createPane("overlayMap");
    overlayPane.style.zIndex = "450";
    overlayPane.style.pointerEvents = "none";
    // The units/orders overlay is applied synchronously while the base map is
    // still rasterising, so it is hidden until the first base raster lands to
    // avoid units flashing on the blank background before the map appears.
    overlayPane.style.visibility = "hidden";
    const loadingPane = this.map.createPane("wrapLoadingMap");
    loadingPane.style.zIndex = "500";
    loadingPane.style.pointerEvents = "none";

    this.wrapLoadingMarker = options.horizontalWrap
      ? L.marker(this.bounds.getCenter(), {
          icon: wrapLoadingIcon(),
          interactive: false,
          keyboard: false,
          pane: "wrapLoadingMap",
        })
      : null;

    this.hitLayer = L.layerGroup().addTo(this.map);

    this.container.addEventListener("wheel", this.onWheel, { passive: false });
    if (options.horizontalWrap) {
      this.map.on("move", this.updateWrapLoadingMarker);
      this.map.on("moveend", this.wrapCenter);
    }

    this.refit();
    this.wireGestures();
  }

  // Leaflet's built-in worldCopyJump assumes a geographic CRS and can fire its
  // drag handler before CRS.Simple has an initial view. Recenter explicitly at
  // the end of a pan instead: the neighbouring copies cover the gesture, then
  // the camera jumps by exactly one board width with no visible change.
  private wrapCenter = (): void => {
    const { minX, width } = this.options.viewBox;
    const center = this.map.getCenter();
    const wrappedX = minX + ((((center.lng - minX) % width) + width) % width);
    if (Math.abs(wrappedX - center.lng) < 0.001) return;
    this.map.setView([center.lat, wrappedX], this.map.getZoom(), {
      animate: false,
    });
  };

  // Only the canonical board and its immediate neighbours are prepared. If a
  // single long drag outruns them, place one lightweight spinner at the centre
  // of whichever further copy currently occupies the viewport. The marker is
  // recycled no matter how many board widths the gesture crosses.
  private updateWrapLoadingMarker = (): void => {
    const marker = this.wrapLoadingMarker;
    if (!marker) return;
    const canonicalCenter = this.bounds.getCenter();
    const copyIndex = nearestWorldCopyIndex(
      this.map.getCenter().lng,
      canonicalCenter.lng,
      this.options.viewBox.width
    );
    if (Math.abs(copyIndex) <= 1) {
      if (this.map.hasLayer(marker)) this.map.removeLayer(marker);
      return;
    }
    marker.setLatLng([
      canonicalCenter.lat,
      canonicalCenter.lng + copyIndex * this.options.viewBox.width,
    ]);
    if (!this.map.hasLayer(marker)) marker.addTo(this.map);
  };

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
      Math.max(
        MAX_ABSOLUTE_ZOOM,
        this.containZoom + (this.options.maxZoomFactor ?? MAX_ZOOM_FACTORS)
      )
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
      this.map.setMaxBounds(
        this.options.horizontalWrap ? this.verticalBounds : this.bounds
      );
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
    this.map.setMaxBounds(
      fill
        ? this.options.horizontalWrap
          ? this.verticalBounds
          : this.bounds
        : undefined
    );
    this.map.setMinZoom(this.containZoom);
    this.map.once("zoomend", () => this.applyRegime());
    this.fitToRegime(true);
  }

  // Frame a set of provinces, animating the camera to their padded bounding box.
  // The bounds are computed from the province path geometry (the rasterised base
  // has no per-province elements to measure), reusing the same path flattener as
  // the hit-test rings.
  focusProvinces(ids: string[], padding = 1.4, animate = true): void {
    if (ids.length === 0) return;
    const rect = focusBounds(this.provincePaths, ids, padding);
    if (!rect) return;
    const bounds = L.latLngBounds(
      toLatLng({ x: rect.minX, y: rect.minY }),
      toLatLng({ x: rect.maxX, y: rect.maxY })
    );
    const zoom = this.map.getBoundsZoom(bounds, false);
    const center = bounds.getCenter();
    if (this.options.horizontalWrap) {
      center.lng = wrappedXNear(
        center.lng,
        this.map.getCenter().lng,
        this.options.viewBox.width
      );
    }
    this.map.setView(center, zoom, { animate });
  }

  // Maps wheel delta straight to a zoom change, batched per animation frame.
  // Trackpad pinch (ctrl+wheel) and the mouse wheel both flow through here; the
  // per-event step is capped so a single mouse notch stays smooth.
  private onWheel = (event: WheelEvent): void => {
    event.preventDefault();
    let delta = event.deltaY;
    if (event.deltaMode === 1) {
      delta *= 16;
    } else if (event.deltaMode === 2) {
      delta *= this.map.getSize().y;
    }
    this.wheelDelta += delta;
    this.wheelPoint = this.map.mouseEventToContainerPoint(event);
    if (this.wheelRaf !== null) return;
    this.wheelRaf = requestAnimationFrame(() => {
      this.wheelRaf = null;
      if (!this.wheelPoint) return;
      const step = Math.max(
        -WHEEL_MAX_STEP,
        Math.min(WHEEL_MAX_STEP, -this.wheelDelta * WHEEL_ZOOM_SPEED)
      );
      this.wheelDelta = 0;
      this.map.setZoomAround(this.wheelPoint, this.map.getZoom() + step, {
        animate: false,
      });
    });
  };

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

  setBase(canvas: HTMLCanvasElement): void {
    const next = this.copyBounds.map((bounds, index) => {
      const copy = index === 0 ? canvas : this.copyCanvas(canvas);
      return new CanvasOverlay(copy, bounds, {
        interactive: false,
        pane: "baseMap",
      }).addTo(this.map);
    });
    this.removeLayers(this.baseLayers);
    this.baseLayers = next;
    if (!this.baseReady) {
      this.baseReady = true;
      this.map.getPane("overlayMap")!.style.visibility = "";
      if (this.options.forceCompositeOnBase) {
        this.nudgeComposite();
      }
    }
  }

  private copyCanvas(source: HTMLCanvasElement): HTMLCanvasElement {
    const copy = document.createElement("canvas");
    copy.width = source.width;
    copy.height = source.height;
    copy.getContext("2d")?.drawImage(source, 0, 0);
    return copy;
  }

  private removeLayers(layers: L.Layer[]): void {
    for (const layer of layers) {
      this.map.removeLayer(layer);
    }
  }

  // The base raster lands seconds after the map mounts (async SVG->PNG), and
  // Android's WebView does not always paint a layer mutated that late: the board
  // stays blank until the user pans or zooms and forces a repaint (reported as a
  // ~10s white screen that clears on the first touch of the map or zoom button).
  // Toggling the map pane's visibility for one frame re-rasterises it in place —
  // the pane is already unpainted, so hiding it is invisible and the show forces
  // the paint the WebView skipped, without moving the camera. Desktop browsers
  // repaint on layer insertion, so this is gated to native via the option.
  private nudgeComposite(): void {
    const pane = this.map.getPane("mapPane");
    if (!pane) return;
    pane.style.visibility = "hidden";
    this.compositeRaf = requestAnimationFrame(() => {
      this.compositeRaf = null;
      pane.style.visibility = "";
    });
  }

  setOverlay(svg: string): void {
    const source = new DOMParser().parseFromString(svg, "image/svg+xml")
      .documentElement as unknown as SVGElement;
    source.setAttribute("overflow", "visible");
    const next = this.copyBounds.map((bounds, index) =>
      L.svgOverlay(
        (index === 0 ? source : source.cloneNode(true)) as SVGElement,
        bounds,
        { interactive: false, pane: "overlayMap" }
      ).addTo(this.map)
    );
    this.removeLayers(this.overlayLayers);
    this.overlayLayers = next;
  }

  setProvincePaths(paths: Map<string, string>): void {
    this.provincePaths = paths;
    this.renderHighlight();
  }

  setHitTest(rings: ProvinceRing[]): void {
    this.hitLayer.clearLayers();
    this.polygonsByProvince.clear();
    for (const ring of rings) {
      for (const bounds of this.copyBounds) {
        const xOffset = bounds.getWest() - this.bounds.getWest();
        const polygon = L.polygon(
          ring.points.map((point) =>
            toLatLng({ x: point.x + xOffset, y: point.y })
          ),
          hitTestStyle()
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
    }
    this.updateHitTargets();
  }

  private handleClick(province: string, event: L.LeafletMouseEvent): void {
    if (this.options.mode !== "interactive") return;
    const original = event.originalEvent;
    this.options.onClickProvince?.(province, {
      x: original.clientX,
      y: original.clientY,
    });
  }

  private handleHover(province: string | null): void {
    if (this.options.mode !== "interactive") return;
    if (this.hovered === province) return;
    this.hovered = province;
    this.renderHighlight();
  }

  setStyleState(style: StyleState): void {
    this.style = style;
    this.updateHitTargets();
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
    const source = new DOMParser().parseFromString(svg, "image/svg+xml")
      .documentElement as unknown as SVGElement;
    const next = this.copyBounds.map((bounds, index) =>
      L.svgOverlay(
        (index === 0 ? source : source.cloneNode(true)) as SVGElement,
        bounds,
        { interactive: false, pane: "highlightMap" }
      ).addTo(this.map)
    );
    this.removeLayers(this.highlightLayers);
    this.highlightLayers = next;
  }

  // Mirrors the SVG map (InteractiveMap), where every hit path is given
  // pointer-events only when its province is renderable. Named coasts are not
  // renderable by default and their hit shapes overlap the parent province, so
  // leaving them interactive would let them intercept the hover and suppress the
  // highlight. Disabling pointer events on non-renderable shapes lets the hover
  // fall through to the renderable province beneath.
  private updateHitTargets(): void {
    for (const [province, polygons] of this.polygonsByProvince) {
      const renderable = this.style.renderable.has(province);
      const cursor =
        renderable && this.options.mode === "interactive"
          ? "pointer"
          : "default";
      for (const polygon of polygons) {
        const element = polygon.getElement();
        if (element instanceof SVGElement || element instanceof HTMLElement) {
          element.style.cursor = cursor;
          element.style.pointerEvents = renderable ? "" : "none";
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
    if (this.wheelRaf !== null) {
      cancelAnimationFrame(this.wheelRaf);
    }
    if (this.compositeRaf !== null) {
      cancelAnimationFrame(this.compositeRaf);
    }
    this.container.removeEventListener("wheel", this.onWheel);
    this.map.off("move", this.updateWrapLoadingMarker);
    this.map.off("moveend", this.wrapCenter);
    this.map.remove();
  }
}
