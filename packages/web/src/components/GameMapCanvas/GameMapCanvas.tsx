import { useEffect, useMemo, useRef } from "react";
import "leaflet/dist/leaflet.css";
import type { Order, PhaseRetrieve, Variant } from "../../api/generated/endpoints";
import { parseDsvg } from "../InteractiveMap/dsvgParser";
import { DiplicityMap } from "../InteractiveMap/mapRenderer";
import { toRenderState } from "../InteractiveMap/toRenderState";
import { recordGesture, recordInitialRender } from "../InteractiveMap/mapTelemetry";
import { useDsvg } from "../../hooks/useDsvg";
import { isNativePlatform } from "../../utils/platform";
import { GameMapController, type GestureRecord } from "./GameMapController";
import { renderSplitSvg } from "./mapSvgLayers";
import { rasterizeSvg } from "./rasterizeSvg";
import { buildProvinceRings } from "./provincePolygons";

type VariantForMap = Pick<Variant, "id" | "nations" | "svgUrl">;

type GameMapCanvasProps = {
  variant: VariantForMap;
  phase: PhaseRetrieve;
  orders: Order[] | undefined;
  selected: string[];
  highlighted?: string[];
  civilDisorderNations?: string[];
  renderableProvinces?: string[];
  interactive?: boolean;
  onClickProvince?: (province: string, position: { x: number; y: number }) => void;
  style?: React.CSSProperties;
};

const GameMapCanvas: React.FC<GameMapCanvasProps> = (props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<GameMapController | null>(null);
  const basePngRef = useRef<string | null>(null);
  const initialRecordedRef = useRef(false);

  const { data: dsvg } = useDsvg(props.variant.svgUrl);

  const parsed = useMemo(() => (dsvg ? parseDsvg(dsvg) : null), [dsvg]);
  const renderer = useMemo(() => (dsvg ? new DiplicityMap(dsvg) : null), [dsvg]);

  const rings = useMemo(
    () =>
      parsed
        ? buildProvinceRings(
            new Map([...parsed.provincePaths, ...parsed.namedCoastPaths])
          )
        : null,
    [parsed]
  );

  const civilDisorderNations = props.civilDisorderNations;

  // The base raster depends only on board ownership (province fills, supply
  // centres, names, borders), so it is rendered with no orders and re-rasterised
  // only when the phase changes — never on a per-order interaction.
  const baseState = useMemo(
    () => toRenderState(props.variant, props.phase, [], [], [], []),
    [props.variant, props.phase]
  );

  const baseSvg = useMemo(
    () =>
      renderer && parsed
        ? renderSplitSvg(renderer, baseState, parsed.viewBox).base
        : null,
    [renderer, parsed, baseState]
  );

  // The overlay (units + order arrows) is a light vector layer repainted on
  // every interaction, so it carries the live orders.
  const overlaySvg = useMemo(
    () =>
      renderer && parsed
        ? renderSplitSvg(
            renderer,
            toRenderState(
              props.variant,
              props.phase,
              props.orders ?? [],
              [],
              [],
              civilDisorderNations ?? []
            ),
            parsed.viewBox
          ).overlay
        : null,
    [renderer, parsed, props.variant, props.phase, props.orders, civilDisorderNations]
  );

  // Keep the latest interaction callbacks in refs so the map is created once and
  // never torn down just because a handler identity changed.
  const onClickRef = useRef(props.onClickProvince);
  const variantIdRef = useRef(props.variant.id);
  onClickRef.current = props.onClickProvince;
  variantIdRef.current = props.variant.id;

  useEffect(() => {
    if (!containerRef.current || !parsed) return;

    const handleGesture = (record: GestureRecord): void => {
      recordGesture({
        variantId: variantIdRef.current,
        gestureType: record.gestureType,
        durationMs: record.durationMs,
        frameMs: record.frameMs,
        implementation: "leaflet",
      });
    };

    const controller = new GameMapController(containerRef.current, {
      viewBox: parsed.viewBox,
      interactive: props.interactive ?? false,
      enableHover: (props.interactive ?? false) && !isNativePlatform(),
      onClickProvince: (province, position) =>
        onClickRef.current?.(province, position),
      onGesture: handleGesture,
    });
    controllerRef.current = controller;

    const resizeObserver = new ResizeObserver(() => controller.invalidateSize());
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      controller.destroy();
      controllerRef.current = null;
      if (basePngRef.current) {
        URL.revokeObjectURL(basePngRef.current);
        basePngRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- create the map once per parsed dSVG; live values flow through refs and dedicated effects
  }, [parsed]);

  useEffect(() => {
    if (controllerRef.current && rings) {
      controllerRef.current.setHitTest(rings);
    }
  }, [rings]);

  useEffect(() => {
    const controller = controllerRef.current;
    if (!controller || baseSvg === null || !parsed) return;

    let cancelled = false;
    const t0 = performance.now();
    const { width, height } = parsed.viewBox;
    rasterizeSvg(baseSvg, width, height)
      .then((pngUrl) => {
        if (cancelled) {
          URL.revokeObjectURL(pngUrl);
          return;
        }
        controller.setBase(pngUrl);
        if (basePngRef.current) {
          URL.revokeObjectURL(basePngRef.current);
        }
        basePngRef.current = pngUrl;
        if (!initialRecordedRef.current) {
          initialRecordedRef.current = true;
          const renderMs = performance.now() - t0;
          recordInitialRender({
            variantId: variantIdRef.current,
            renderMs,
            implementation: "leaflet",
          });
          containerRef.current?.setAttribute(
            "data-initial-render-ms",
            renderMs.toFixed(2)
          );
          containerRef.current?.setAttribute("data-map-ready", "true");
        }
      })
      .catch(() => {
        /* a failed raster leaves the previous base in place */
      });

    return () => {
      cancelled = true;
    };
  }, [baseSvg, parsed]);

  useEffect(() => {
    if (controllerRef.current && overlaySvg !== null) {
      controllerRef.current.setOverlay(overlaySvg);
    }
  }, [overlaySvg]);

  useEffect(() => {
    if (!controllerRef.current) return;
    controllerRef.current.setStyleState({
      selected: new Set(props.selected),
      highlighted: new Set(props.highlighted ?? []),
      renderable: new Set(
        props.renderableProvinces ?? rings?.map((ring) => ring.id) ?? []
      ),
    });
  }, [props.selected, props.highlighted, props.renderableProvinces, rings]);

  return (
    <div
      ref={containerRef}
      data-map-impl="leaflet"
      style={{ width: "100%", height: "100%", background: "#fff", ...props.style }}
    />
  );
};

export { GameMapCanvas };
export type { GameMapCanvasProps };
