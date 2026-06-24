import { render, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MapView, type MapViewProps } from "./MapView";

vi.mock("./InteractiveMap/InteractiveMapZoomWrapper", () => ({
  InteractiveMapZoomWrapper: ({
    interactiveMapProps,
  }: {
    interactiveMapProps: {
      onClickProvince?: (
        province: string,
        event: { clientX: number; clientY: number }
      ) => void;
    };
  }) => (
    <button
      data-testid="province"
      onClick={() =>
        interactiveMapProps.onClickProvince?.("lon", {
          clientX: 42,
          clientY: 99,
        })
      }
    />
  ),
}));

const baseProps: MapViewProps = {
  variant: { id: "standard", nations: [], svgUrl: null },
  phase: {} as MapViewProps["phase"],
  orders: undefined,
  selected: [],
};

describe("MapView", () => {
  it("adapts the SVG click event into renderer-agnostic client coordinates", () => {
    const onClickProvince = vi.fn();
    const { getByTestId } = render(
      <MapView {...baseProps} onClickProvince={onClickProvince} />
    );

    fireEvent.click(getByTestId("province"));

    expect(onClickProvince).toHaveBeenCalledWith("lon", { x: 42, y: 99 });
  });
});
