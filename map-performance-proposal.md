## A proposal to step back and rethink the map, empirically

First — thank you for the diagnosis above. The GPU-layer / re-rasterisation analysis is genuinely good detective work, and the "oversized resident bitmap vs. text re-raster" framing is almost certainly correct as far as it goes. I want to build on it, but also argue that we should **widen the frame before we commit to another round of fixes**, because I think the solutions we've tried so far are treating symptoms of a deeper cause.

### Why I think we're playing whack-a-mole

The last few changes have each been locally reasonable and individually defensible, but the pattern worries me:

- Remove `will-change` → revert it.
- Add a transform cache of 50 → reduce to 5 → drop it entirely.
- Add `translateZ(0)` → propose removing it.
- CSS-transform zoom → viewBox-driven zoom (#789).

Every one of these was a plausible fix for one symptom on one device. The problem is we have **no baseline and no cross-device measurement**, so we can't actually say whether any of them helped. #789 is the clearest example: it was verified as fixing the flicker on a Pixel 8a, and it visibly *regressed* pan/zoom on my iPhone (side-by-side video on the PR). That's not bad luck — it's the inevitable result of optimising without a measurement that generalises across devices.

I don't want to merge another change that "feels better on the device the author happened to test on."

### The root cause is heavier than the GPU layer

I measured the classical dSVG to get some hard numbers:

- **1,091 KB total**, of which **903 KB is raw path geometry** (`d` attributes). No embedded rasters at all.
- **16,871 path drawing commands** across 144 paths.
- **Two single paths are ~139 KB each** (the sea/landmass and the borders).

That geometry is the real cost, and it explains why both approaches we've tried disappoint:

- **CSS-transform the whole SVG** (current `main`): the browser rasterises once into a GPU layer, then transforms the bitmap — cheap to move, but the layer goes oversized at zoom → re-raster under memory pressure → the flicker described above.
- **Drive `viewBox` every frame** (#789): no oversized layer, so no flicker — but now the browser must **re-tessellate and re-paint ~17k path commands on the CPU every gesture frame**. A fast Pixel holds 60fps; my iPhone goes CPU-bound and janks.

In other words, #789 didn't remove the cost — it **moved it from the GPU to the CPU**, and the trade went the wrong way on my device. Flattening static layers (solution 3 above) helps the React/DOM side but doesn't change the fact that we're asking the browser to paint ~17k bezier commands live.

### The reframe: we should never be painting that geometry live

Here's the key realisation. **Canvas and WebGL are not automatically faster than SVG** — if you redraw 17k path commands per frame on a canvas, you've rebuilt #789's jank with a different API. The thing that actually buys performance, in SVG, Canvas, or WebGL alike, is one invariant:

> **Rasterise the expensive static layer once. Each frame, move only a camera and repaint the light overlay.**

The base map (landmasses, borders, province fills, names) only changes on phase/ownership — never during a gesture. The overlay (units, orders, hover, selection) is tiny. So we should never be re-painting the heavy geometry during pan/zoom.

This is also, incidentally, how Google Maps / Mapbox actually work. They don't render "massively complex SVG very effectively" — **they never render complex SVG at all.** They simplify geometry per zoom level, tile and clip it, and push pre-tessellated triangles to the GPU. The lesson isn't "browsers are fine with complex vectors"; it's "preprocess the geometry so the browser never has to paint the complex thing live."

### Proposed architecture — three layers, and buy the viewport

I'd like us to stop hand-rolling the pan/zoom/compositing machinery (we currently own a 270-line zoom wrapper, a 710-line string renderer, and a 560-line SVG-primitive builder) and instead **lean on a battle-tested library** that has solved interactive pan/zoom-a-big-thing on mobile a million times. My current candidate is **Leaflet with `CRS.Simple`**, because it gives us the viewport *and* vector hit-testing *and* pinned overlays in one well-trodden API. OpenSeadragon is the alternative if deep-zoom tiling of the base image becomes the dominant concern; a WebGL/Pixi renderer stays as an escape hatch only if measurement proves a library can't hold frame rate.

The model is three clean layers:

| Layer | Source | Cost | Changes |
|---|---|---|---|
| **Base (visual)** | Full-detail SVG → **rasterised once** to an image/tiles | One-time raster | Per phase only |
| **Hit-test** | **Simplified / decimated** province polygons | Cheap | Built once per variant |
| **Overlay** | Units + order arrows from our existing geometry | Light | On interaction/phase |

Two things make this much lower-risk than it sounds:

1. **A soft base map at our 4× max zoom is acceptable** (confirmed). That single concession lets the base be a bitmap and removes the hardest constraint.
2. **The hard, correctness-critical logic is renderer-agnostic and survives the rewrite.** `orderGeometry.ts` (convoy routing, support staggering, b-spline attachment, head-to-head curves) is pure `Point`-in/`Point`-out maths. Only the *paint* layer (`svgPrimitives.ts` string-building) gets replaced. We are **not** reimplementing Diplomacy order rendering from scratch.

### Build it standalone, with diagnostics and perf as first-party concerns

I feel strongly that if we're rewriting, we should **not** instrument the existing map — that's throwing measurement at a component we're about to delete. Instead, the new component should treat observability and performance as part of its contract from day one:

- **Build it as an isolated workspace package** (`packages/map`) with a **frozen public interface** mirroring today's `InteractiveMap` props (variant + phase + orders + selection in, `onClickProvince` out). Isolation forces a clean boundary and keeps it from being shaped by the code around it; the eventual swap is a one-line dependency change. The one rule: build it against our **real dumped fixtures** (`classicalMap.dsvg` + the fixture game states), not toy data, so it still meets real integration constraints.
- **A performance harness as a budget that exists *before* the implementation.** A bench route renders a chosen variant; Playwright + CDP drives a scripted pan/zoom under CPU throttling and captures p95 frame time / long-tasks / paint cost. We write the budget as a failing gate (e.g. *p95 frame < 16ms at 6× CPU throttle on Spice Islands*) and build until it's green. This is the thing whose absence let #789 ship a regression — it makes "feels worse" into a number.
- **Telemetry as a built-in seam.** The component takes a telemetry sink (we already run Sentry + Honeycomb) and emits gesture frame-timing and interaction latency tagged with variant-id and device-class, by construction. From day one we'd see real-user numbers across the device spread.
- **A golden variant set** (cheapest / median / Cold War / Spice Islands) so both the harness and telemetry span the real complexity range.

### On the complex SVGs — optimise *after*, with one exception

We haven't really decided what to do about the heavy variants. My answer: **defer it.** The rasterise-once architecture turns the 17k-command paint from a per-frame cost into a once-per-phase cost, which makes the source SVG's visual complexity almost irrelevant to felt pan/zoom performance. Optimising the source paths first would be tuning the input to a subsystem we're about to make insensitive to it.

The **one** piece of geometry work we need regardless is generating the **decimated hit-test polygons** — click/hover detection doesn't need coastline detail, and a polygon simplified at ~5px tolerance detects taps identically while being cheap to render. That's a small, testable build step that ships with v1. Cosmetic SVG optimisation (svgo, path simplification for download size / raster cost) becomes a later, independent knob we reach for only if the harness shows initial load or phase-change raster still hitches.

### Suggested sequence

1. **Tooling first:** an SVG-complexity analyser (rank variants by path-command count, not KB), the Playwright+CDP perf harness, and the telemetry seam.
2. **Budgets:** define perf budgets against the golden variant set *before* writing the component.
3. **Build** the new map in `packages/map` (Leaflet `CRS.Simple`, three-layer model, `orderGeometry` carried over intact) until it satisfies the budgets — proved on one surface (GameMap) first.
4. **Drop-in replace**, then migrate Tutorial and ExpandableMapPreview.
5. **Optimise source SVGs** only where the harness still shows it matters.

### What I'd like to decide here

- Are we agreed that the next step is **measurement infrastructure + a from-scratch component**, rather than another iteration on the CSS-transform/viewBox path?
- Any objection to **buying the viewport** (Leaflet/OSD) rather than continuing to own the gesture and compositing code?
- Is everyone comfortable with the **soft-base-map-at-zoom** trade, which is what unlocks the whole simpler approach?

I'd rather spend a week building the harness and a clean component than another month merging device-specific tweaks we can't measure. Keen to hear where this lands for people.
