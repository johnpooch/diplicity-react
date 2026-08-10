import L from "leaflet";

type LiveMap = L.Map & { _mapPane?: HTMLElement };

const onZoomTransitionEnd = (L.Map.prototype as L.Map & {
  _onZoomTransitionEnd: () => void;
})._onZoomTransitionEnd;

// Leaflet schedules two pieces of deferred work without keeping a handle to
// either, so Map.remove() has nothing to cancel: _animateZoom sets a 250ms
// timeout backstopping a transitionend that webkit may never fire, and the drag
// handler requests an animation frame at dragend to run the inertia pan. Both
// callbacks dereference _mapPane, which remove() deletes on its way out, so a
// map unmounted mid-zoom or mid-flick throws out of the leftover callback
// ("_leaflet_pos" of undefined from the zoom timer, "classList" of undefined
// from the pan frame). Skipping both entry points once the pane is gone leaves
// the pending work harmless. The zoom timer binds the method when it schedules,
// so the guard has to sit on the class rather than be applied at teardown.
const SafeMap = L.Map.extend({
  _onZoomTransitionEnd(this: LiveMap) {
    if (!this._mapPane) return;
    onZoomTransitionEnd.call(this);
  },

  panBy(this: LiveMap, offset: L.PointExpression, options?: L.PanOptions) {
    if (!this._mapPane) return this;
    return L.Map.prototype.panBy.call(this, offset, options);
  },
}) as unknown as new (container: HTMLElement, options?: L.MapOptions) => L.Map;

export const createSafeMap = (
  container: HTMLElement,
  options: L.MapOptions
): L.Map => new SafeMap(container, options);
