import { lazy, Suspense } from "react";
import type { Order, PhaseRetrieve, Variant } from "../api/generated/endpoints";
import { InteractiveMapZoomWrapper } from "./InteractiveMap/InteractiveMapZoomWrapper";
import { resolveMapImplementation } from "./GameMapCanvas/mapImplementation";

const GameMapCanvas = lazy(() =>
  import("./GameMapCanvas/GameMapCanvas").then((module) => ({
    default: module.GameMapCanvas,
  }))
);

interface MapViewProps {
  variant: Pick<Variant, "id" | "nations" | "svgUrl">;
  phase: PhaseRetrieve;
  orders: Order[] | undefined;
  selected: string[];
  highlighted?: string[];
  civilDisorderNations?: string[];
  renderableProvinces?: string[];
  interactive?: boolean;
  onClickProvince?: (province: string, position: { x: number; y: number }) => void;
  style?: React.CSSProperties;
}

const MapView: React.FC<MapViewProps> = ({ onClickProvince, ...props }) => {
  if (resolveMapImplementation() === "leaflet") {
    return (
      <Suspense fallback={<div style={{ width: "100%", height: "100%" }} />}>
        <GameMapCanvas {...props} onClickProvince={onClickProvince} />
      </Suspense>
    );
  }

  return (
    <InteractiveMapZoomWrapper
      interactiveMapProps={{
        ...props,
        onClickProvince: onClickProvince
          ? (province, event) =>
              onClickProvince(province, { x: event.clientX, y: event.clientY })
          : undefined,
      }}
    />
  );
};

export { MapView };
export type { MapViewProps };
