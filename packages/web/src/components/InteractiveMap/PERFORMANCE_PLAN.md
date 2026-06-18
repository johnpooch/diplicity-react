# InteractiveMap rendering performance plan

Goal: eliminate map flicker (all devices) and improve pan/zoom FPS (old/low-end
devices), starting with Cold War and Spice Islands which are the densest maps.

This document is the source of truth for the effort and is meant to be resumed
across sessions. Update the **Status** line of each phase and the **Next action**
pointer below as work progresses.

> **Next action:** Phase 1 core landed for the **GameMap** path
> (`InteractiveMapZoomWrapper`) on branch `perf/map-viewbox-zoom`. Remaining
> before the measurement gate: (a) **on-device flicker validation** on Pixel 8a +
> iPhone + the old laptop for Cold War / Spice Islands; (b) migrate the other two
> zoom surfaces still on CSS-transform — `TutorialMap.tsx` and
> `ExpandableMapPreview.tsx` (`ZoomableMap`) — to the same split, or consciously
> defer them. Then measure gesture FPS and decide on Phases 4/2.

---

## Root cause (established)

The map is one large SVG (~840 vector paths + ~261 `<text>` labels using 4
embedded woff2 fonts; **no embedded raster images**). react-zoom-pan-pinch
(RZPP) zooms/pans by applying a CSS `transform: scale()/translate()` to the
wrapper, and the `<svg>` is force-promoted to its own GPU layer via
`transform: translateZ(0)` (`InteractiveMap.tsx:161-167`, added in `70d0ee95`).

- **Flicker (every device, incl. Pixel 8a):** CSS-scaling a vector SVG forces the
  browser to re-rasterize it to stay crisp. At `maxScale=4` on a 1500px viewBox ×
  DPR the rasterized surface is ~15,000²px — past the GPU max-texture/tile budget,
  so tiles get dropped (flicker) and under memory pressure the whole layer is
  demoted ("all provinces vanish"). The text-heavy `above` group
  (`InteractiveMap.tsx:46-69` splits the rendered SVG into `below` =
  background+province-fills and `above` = labels/borders/units/orders) is the
  costliest to re-raster, which is why the base map stays while the labels flicker.
- **Low FPS (old laptop only):** raw cost of re-rasterizing ~840 paths + 261
  custom-font labels per zoom frame. A fast GPU hides it; a weak one stalls.

The `translateZ(0)` promotion was added to fix a *different* problem (white flash
on maps with embedded **raster images**) and is counter-productive for these
vector/text maps.

## Why viewBox fixes it

Drive pan/zoom by mutating the `<svg viewBox>` instead of CSS-transforming a
rasterized layer. The `<svg>` element stays a fixed on-screen size, so the
browser only ever rasterizes ~viewport pixels **regardless of zoom level** — no
oversized texture to allocate/drop, no async re-raster-to-sharpen step. This
removes the flicker structurally on all devices, during the gesture too (the
gesture is driven by viewBox, so each frame is a complete bounded paint).

Trade-off: each gesture frame is a main-thread repaint (vs. RZPP's
compositor-only transform). Cheap on modern phones; may pressure the 16ms budget
on the old laptop. Phases 2/4 address that *if measurement shows it's needed*.

---

## Phase ordering & decision gates

```
Phase 1 (viewBox at rest + during gesture)  ──> fixes flicker everywhere
        │
        └─ MEASURE gesture FPS on the weak laptop + iPhone (WKWebView) + Pixel
              │
              ├─ FPS fine everywhere  ──────────────> DONE. Skip 2/3/4.
              │
              └─ FPS poor on weak devices
                      │
                      ├─ Phase 4 first (no UX downgrade, helps everyone)
                      │     └─ MEASURE again
                      │            ├─ enough ──> DONE
                      │            └─ not enough ─┐
                      │                           ▼
                      └─ Phase 2 (+3) raster-during-gesture, behind manual toggle
```

**Phases 2 and 4 attack the same axis (weak-device gesture FPS). You likely do
not need both.** Phase 4 has no UX cost, so try it before Phase 2. Phase 3 (font
rasterization validation) is a prerequisite *sub-task* of Phase 2, not a
standalone deliverable — it only matters if we rasterize.

---

## Phase 1 — viewBox at rest (and during gesture)

**Status:** ◐ in progress — GameMap path implemented on `perf/map-viewbox-zoom`.

### What was actually built (decision: keep RZPP, split the layers)

Rather than a from-scratch gesture hook, the GameMap surface now splits into two
stacked SVGs, which keeps RZPP's battle-tested gesture/pointer handling and all
the existing fit/center/fullscreen/bounds math while removing the flicker:

- **`MapVisual.tsx`** (new) — the visible layers (below/hover/above), a
  container-filling SVG with **no CSS transform**. Its `viewBox` is driven
  imperatively (not via JSX, to avoid React clobbering live updates). Bounded
  raster surface → no oversized texture → no flicker.
- **`MapHitLayer.tsx`** (new) — intrinsic-sized, fully **transparent** hit paths;
  this is the element RZPP CSS-transforms. Transparent ⇒ re-rasterising at any
  scale is free and never flickers, while geometry-based hit-testing still works.
- **`InteractiveMapZoomWrapper.tsx`** (rewritten) — composes the two, converts
  RZPP's `{scale, positionX, positionY}` to a `viewBox` in `onTransformed`
  (`transformToViewBox`), holds hover state, preserves the fullscreen toggle and
  gesture pointer-event suppression. `translateZ(0)` is gone from this path.
- **`mapLayers.ts`** (new) — extracted `stripSvgWrapper` /
  `splitAfterProvinceFills` / hover constants, shared with `InteractiveMap.tsx`.
- **`InteractiveMap.tsx`** — kept (still used by TutorialMap/stories); only the
  PR #634 diagnostic logging was removed. Its `translateZ(0)` was left in place to
  avoid regressing TutorialMap until that surface is migrated.

Why this over the from-scratch hook: pointer arbitration (pan vs. tap vs. pinch)
is exactly what RZPP already solves; moving the visible SVG out of the transform
tree to kill flicker while keeping RZPP for gestures is far lower risk. The
custom-hook option remains open if the two-layer alignment ever proves fragile.

Verified: `tsc -b --noEmit` clean, eslint clean, 56 map tests pass
(`GameMap`, `mapRenderer`, `dsvgParser`); static render confirmed correct on
desktop + mobile fixtures (initial fit is itself driven through the
transform→viewBox path, so correct fitting validates the conversion math).
**Not yet validated:** real flicker behaviour during live gestures on device.

### Deferred to finish Phase 1

- `TutorialMap.tsx` — still RZPP CSS-transform of a full `InteractiveMap`
  (+ a `setTransform` focus animation to port). Same split applies.
- `ExpandableMapPreview.tsx` `ZoomableMap` — its own RZPP + `dangerouslySetInnerHTML`.
- Decision taken: **skipped `non-scaling-stroke`** — strokes scaling with zoom
  matches today's behaviour, so it's out of scope for a flicker-only change.

### Architecture decision (original notes, superseded by "What was built")

RZPP's value is gesture math (wheel/drag/pinch → scale+offset) + bounds + min/max
+ centering. We only want to replace its *output* (CSS transform → viewBox).
Note momentum/inertia is **already disabled** (`velocityAnimation.disabled`,
`panning.velocityDisabled` at `InteractiveMapZoomWrapper.tsx:240-241`), so the
hard-to-reimplement part of RZPP isn't even in use.

- **Recommended: custom pan/zoom hook** writing `viewBox` directly. One
  coordinate model (viewBox), no fighting RZPP's transform. The gesture code is
  modest and the fit/center math already exists (just re-expressed in viewBox
  units). Makes Phase 2 cleaner too (derive the gesture-time CSS transform of the
  bitmap from the viewBox delta).
- Fallback: keep RZPP, read its transform state in `onTransformed`, convert to
  viewBox, neutralize its CSS transform. Less new code but constant
  coordinate-space friction.

### Implementation steps

1. Decide hook vs. RZPP (above). If custom hook: `usePanZoomViewBox` returning
   `{ viewBox, handlers }` and applying viewBox imperatively via `svgRef`
   (no React re-render per frame — same discipline as the current `transformRef`).
2. Re-express existing geometry in viewBox terms:
   - fit / contain scale (`calculateFittedScale`, `calculateContainedScale`,
     `InteractiveMapZoomWrapper.tsx:86-110`) → initial viewBox.
   - centering (`setTransform(...)` calls) → initial viewBox offset.
   - `minScale`/`maxScale` + `limitToBounds` → clamp viewBox (min size = max zoom;
     max size = fit; clamp minX/minY to map bounds).
   - fullscreen toggle (`handleToggleFullscreen`, fitted vs contained).
3. **Focal-point zoom:** wheel zooms toward cursor, pinch toward the two-finger
   midpoint — must zoom the viewBox around the focal point, not the center.
   (This is the fiddliest bit of the phase.)
4. Remove `transform: translateZ(0)` (`InteractiveMap.tsx:166`) and any
   leftover `will-change`. The `<svg>` becomes a fixed-size element.
5. **`vector-effect="non-scaling-stroke"`** on hover/selection outlines (and
   anything that should stay constant px) so stroke widths don't grow with zoom
   now that there's no CSS scale. Audit `HOVER_STROKE_WIDTH` and the
   selected/highlighted strokes in `mapRenderer.ts`.
6. Confirm province click/hover hit-testing still works at all zoom levels (the
   transparent hit-path `<g>` in `InteractiveMap.tsx:213-233` is in SVG user
   space, so it should — verify).
7. Remove the PR #634 diagnostic logging (`renderCountRef`, `performance.now`
   logs in both `InteractiveMap.tsx` and `InteractiveMapZoomWrapper.tsx`) and
   replace with a small, toggleable FPS/paint measurement used for the gate below.

### Exit criteria / measurement gate

- Flicker gone on Pixel 8a, iPhone (WKWebView), and the old laptop for Cold War +
  Spice Islands, during both drag and pinch.
- Record gesture FPS / mean frame time on each device. **If comfortably <16ms
  during gestures everywhere → ship Phase 1 alone and stop.** Otherwise proceed
  to Phase 4.

---

## Phase 4 — flatten/optimize the static layers

**Status:** ☐ not started  ·  (do before Phase 2 if Phase 1 FPS is insufficient)

The static layers (background, province-names, borders, foreground) never change
between render states; only province-fills/units/orders are dynamic.

### Render vs. upload — decision: **client-side, at load, memoized per variant. NOT at upload.**

- The layer split is already client-side (`dsvgParser.ts:108-118`); recomposing
  the static subset once per variant load is trivial and needs **no backend
  change and no migration** of stored `VariantSVG` rows.
- Keeps the raw dsvg as the single source of truth; no derived artifact to keep
  in sync. (`VariantSVG.content_hash`, `service/variant/models.py:182`, would be
  a natural cache key if we ever *do* cache a derived artifact.)
- Only move server-side if a *one-time* client flatten/raster proves too slow on
  weak devices (measure first). If so, the hook is `VariantSVG.save()`
  (`service/variant/models.py:179-185`, alongside `normalize_dsvg`/`sanitize_svg`)
  plus a data migration recomputing for existing rows + a backend rasterizer
  (e.g. resvg) — significantly more work; treat as a last resort.

### Two flavours — be precise about what each buys

- **(a) Vector flatten** — compose the static layers into one cached static `<g>`
  string once per variant; only re-inject dynamic layers on state change. Reduces
  `render()` JS cost and DOM churn on state changes. **Does NOT meaningfully cut
  per-frame paint during a viewBox gesture** — the browser still re-shapes the 261
  text runs and re-fills paths each frame. Low risk, keeps crispness.
- **(b) Raster flatten** — pre-rasterize the static layers once to a bitmap
  (`<image>`/canvas) at native resolution and sample it during paint. **This is
  what actually cuts per-frame paint cost** (no text re-shaping), but labels blur
  when zoomed past native resolution. Overlaps heavily with Phase 2's idea applied
  to the static layers only.

Pick based on the Phase 1 gate: if paint cost is dominated by text shaping (likely),
(b) is the lever; if it's DOM/JS churn, (a) suffices.

### Exit criteria

- Re-measure gesture FPS on weak devices. If acceptable → done, skip Phase 2.

---

## Phase 2 — raster-during-gesture (manual "Performance mode" toggle)

**Status:** ☐ not started  ·  (only if Phases 1+4 leave weak-device FPS poor)

During an active gesture, swap the live SVG for a single bitmap snapshot and let
that be CSS-transformed (compositor-only, smooth on weak GPUs, **no re-raster so
no flicker** — a bitmap has no crisper version to compute). On gesture end, bake
the transform into the new viewBox, re-render the live SVG, drop the bitmap.
Blurry while actively zooming in, snaps crisp on release — standard maps/PDF UX.

Lifecycle hooks already exist (`onPanningStart/Stop`, `onPinchingStart/Stop`,
`onZoomStart/Stop` at `InteractiveMapZoomWrapper.tsx:243-248`) as swap points
(or the equivalent in the custom hook).

### Toggle (decided)

- **Manual toggle only. No automatic RAM/`deviceMemory` detection for now.**
  (`navigator.deviceMemory` is Chrome-only, capped at 8, and absent in iOS
  WKWebView — the user tests on iPhone — so it's unreliable as a gate anyway.
  Auto-enable via a runtime FPS probe is a possible *future* enhancement, not now.)
- **Home: the Account screen** (`screens/Home/Account.tsx`) — add a new
  "Performance mode" setting there.
- **Persistence: mirror the theme pattern** — a `performanceModeStorage.ts`
  (boolean, localStorage) + `usePerformanceMode` hook using
  `useSyncExternalStore`, modeled on `theme/themeStorage.ts` + `theme/useTheme.ts`.
  No backend / user-profile change.
- Default: **off** (live viewBox rendering from Phase 1).

### Implementation steps

1. `performanceModeStorage.ts` + `usePerformanceMode` (copy theme pattern).
2. Account screen toggle row + test (`Account.test.tsx` exists).
3. In the map: when perf mode on, on gesture start rasterize current SVG →
   canvas, show canvas / hide SVG; CSS-transform canvas during gesture (derive
   transform from viewBox delta); on gesture stop bake → viewBox, re-render SVG,
   hide canvas. **Requires Phase 3 first.**
4. Snapshot resolution ~1.5–2× current on-screen size to limit zoom-in blur;
   cap canvas dimensions to bound memory on large screens.

### Exit criteria

- Perf mode on: smooth, flicker-free gestures on the weak laptop; crisp at rest.
- Perf mode off: unchanged Phase 1 behaviour.

---

## Phase 3 — validate SVG→canvas font rasterization

**Status:** ☐ not started  ·  (prerequisite sub-task of Phase 2)

Risk: `drawImage` of an SVG containing `@font-face` woff2 (data-URI) fonts has
historically been finicky across engines. The 4 fonts are data-URIs inside the
SVG and already loaded by the live map, so they should rasterize from the font
cache — but verify before building Phase 2 on top of it.

- No cross-origin taint risk (everything same-origin data-URIs).
- Validate on Chrome (Pixel WebView), WKWebView (iPhone), and the laptop browser
  — WebKit is the most likely to differ.
- If a font fails to rasterize: pre-warm via the FontFace API / `document.fonts.ready`
  before snapshotting, or fall back to keeping that layer live.

---

## Cross-cutting / don't forget

- **Test matrix:** old laptop browser, Pixel 8a (Capacitor Android WebView),
  iPhone (Capacitor WKWebView). WebKit SVG perf differs from Blink — measure all.
- **PR screenshots** are mandatory for visible changes (CLAUDE.md). Use the
  Spice Islands / Cold War fixtures; before/after, including mobile viewport.
- **Existing tests:** `mapRenderer.test.ts`, `mapRenderer.classical.test.ts`,
  `dsvgParser.test.ts`, `GameMap.test.tsx` — keep green; add coverage for the
  viewBox math and the new storage/hook.
- **SMIL `<animate>`** on highlighted provinces (`mapRenderer.ts:189`) freezes
  during a raster gesture — acceptable.
- **Remove** the PR #634 diagnostic logging as part of Phase 1.
- Keep changes scoped per phase so the work is shippable incrementally (Phase 1
  is a complete, valuable PR on its own).
