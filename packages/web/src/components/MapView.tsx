import type { Order, PhaseRetrieve, Variant } from "../api/generated/endpoints";
import { InteractiveMapZoomWrapper } from "./InteractiveMap/InteractiveMapZoomWrapper";

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
