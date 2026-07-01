import { render, fireEvent, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeAll } from "vitest";
import { MapView, type MapViewProps } from "./MapView";

beforeAll(() => {
  globalThis.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof IntersectionObserver;
});

const mockGameMapCanvas = vi.fn();

vi.mock("./GameMapCanvas/GameMapCanvas", () => ({
  GameMapCanvas: (props: {
    mode?: string;
    onClickProvince?: (
      province: string,
      position: { x: number; y: number }
    ) => void;
  }) => {
    mockGameMapCanvas(props);
    return (
      <button
        data-testid="province"
        onClick={() => props.onClickProvince?.("lon", { x: 42, y: 99 })}
      />
    );
  },
}));

const baseProps: MapViewProps = {
  variant: { id: "standard", nations: [], svgUrl: null },
  phase: {} as MapViewProps["phase"],
};

const renderWithClient = (ui: React.ReactElement) =>
  render(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>);

describe("MapView", () => {
  it("renders the Leaflet host for interactive mode and forwards province clicks", async () => {
    mockGameMapCanvas.mockClear();
    const onClickProvince = vi.fn();
    renderWithClient(
      <MapView {...baseProps} mode="interactive" onClickProvince={onClickProvince} />
    );

    fireEvent.click(await screen.findByTestId("province"));

    expect(onClickProvince).toHaveBeenCalledWith("lon", { x: 42, y: 99 });
    expect(mockGameMapCanvas).toHaveBeenCalledWith(
      expect.objectContaining({ mode: "interactive" })
    );
  });

  it("does not mount the Leaflet host in static mode", () => {
    mockGameMapCanvas.mockClear();
    renderWithClient(<MapView {...baseProps} mode="static" />);

    expect(mockGameMapCanvas).not.toHaveBeenCalled();
    expect(screen.queryByTestId("province")).toBeNull();
  });
});
