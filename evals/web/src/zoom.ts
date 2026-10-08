export interface View {
  scale: number;
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export const IDENTITY: View = { scale: 1, x: 0, y: 0 };

export const MAX_SCALE = 4;

const WHEEL_ZOOM_SPEED = 0.005;
const WHEEL_MAX_STEP = 0.5;

const clampOffset = (offset: number, extent: number, scale: number) =>
  Math.min(0, Math.max(extent * (1 - scale), offset));

export const clampView = (view: View, size: Size): View => {
  const scale = Math.min(MAX_SCALE, Math.max(1, view.scale));
  return {
    scale,
    x: clampOffset(view.x, size.width, scale),
    y: clampOffset(view.y, size.height, scale),
  };
};

export const zoomAt = (view: View, size: Size, px: number, py: number, factor: number): View => {
  const scale = Math.min(MAX_SCALE, Math.max(1, view.scale * factor));
  const ratio = scale / view.scale;
  return clampView(
    { scale, x: px - (px - view.x) * ratio, y: py - (py - view.y) * ratio },
    size
  );
};

export const wheelFactor = (deltaY: number) =>
  Math.exp(Math.max(-WHEEL_MAX_STEP, Math.min(WHEEL_MAX_STEP, -deltaY * WHEEL_ZOOM_SPEED)));

export const panBy = (view: View, size: Size, dx: number, dy: number): View =>
  clampView({ ...view, x: view.x + dx, y: view.y + dy }, size);
