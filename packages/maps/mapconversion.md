# Map Conversion Guide

## Workflow

1. Place the source SVG in `packages/maps/<variant>/map.svg`
2. Create `packages/maps/<variant>/ids.json` (see below)
3. Build map-parse: `cd packages/map-parse && npm run build`
4. Generate the map JSON:
   ```
   npm run cli -- ../maps/<variant>/map.svg ../maps/<variant>/ids.json ../../packages/web/public/maps/<variant>.json
   ```
5. Verify the output (see checklist below)

---

## ids.json

Maps SVG text element IDs → province IDs used by the game engine. Every `<text>` element in the `#names` layer whose SVG `id` doesn't already match a province ID must have an entry here.

```json
{
  "Bulgaria": "bul",
  "BAY-OF-BENGAL": "bob"
}
```

---

## Common pitfalls

### 1. Coastal sub-province labels (SC / EC / WC)

Provinces with named coasts (e.g. `bul/sc`, `bul/ec`) have small abbreviation labels on the map. Their SVG text elements often have generic or mismatched IDs.

**How to find them:**
- Grep the SVG for `id="[A-Z]*/[se]c"` to list all sub-province paths and their centers.
- For each sub-province, find the text element whose tspan coordinates are closest to that center.
- Check the text element's `id` attribute (not the tspan id).

**Add to ids.json:**
```json
"SC": "bul/sc",
"text333": "bul/ec"
```

**Watch out for:** The SVG id and the visible text content can disagree. An element with `id="EC"` may contain the text "WC" — match by spatial proximity to the province center, not by the id name.

### 2. Multi-word labels split across tspans

Large water bodies (seas, oceans, bays) often split their label across multiple `<tspan>` elements, one word (or line) each:

```xml
<text id="BAY-OF-BENGAL">
  <tspan x="1073" y="1034">BAY</tspan>
  <tspan x="1081" y="1058">OF</tspan>
  <tspan x="1042" y="1082">BENGAL</tspan>
</text>
```

The serializer joins tspan content with spaces for the `value` field and stores individual tspan positions in the `tspans` array. The renderer uses the tspan positions to recreate the stacked layout. This is handled automatically — but if you see a label like `BAYOFBENGAL` in the output, it means the serializer is using `textContent` instead of the tspan-aware path (check `TextSerializer`).

### 3. Text elements with no matching province

Any `<text>` element in `#names` whose id is not in `ids.json` and doesn't already match a province id is silently dropped. After generation, run the verification script below to catch orphaned text.

### 4. Matrix transforms on text and font-size mismatch

Some labels use a full `matrix(a,b,c,d,e,f)` transform (e.g. Primorsky Krai) rather than a simple `rotate(angle)`. When Inkscape decomposes a rotation into a matrix it writes a computed, inflated value into the `style` attribute's `font-size` while keeping the intended visual size in the element's `font-size` attribute. The two values will disagree only on matrix-transformed elements.

The serializer always prefers the `font-size` attribute over the style value, so this is handled automatically. If a label with a matrix transform appears too large in the rendered output, check that the SVG element has an explicit `font-size` attribute set to the correct visual size — if it is missing, the inflated style value will be used instead.

### 5. Sub-province text labels and the renderer

Text labels are rendered in two passes in `InteractiveMap.tsx`:

1. **Provinces in `provincesToRender`** — text rendered alongside the province path. This list normally contains only main provinces; sub-provinces only appear here when highlighted for interaction.
2. **Provinces NOT in `provincesToRender`** — rendered as a separate always-visible pass. This is how coastal sub-province labels (SC / EC / WC) stay on screen during normal gameplay even though their province paths are hidden.

The consequence: if a sub-province's text is not showing up, first check that the province exists in the map JSON with a non-empty `text` array (see verification script). If the data is correct, the issue is likely that the province ID was accidentally added to `renderableProvinces` but then filtered out — or the reverse.

---

## Verification checklist

After generating the JSON, run this script to catch common problems:

```python
import json, math

with open("packages/web/public/maps/<variant>.json") as f:
    data = json.load(f)

provinces = {p["id"]: p for p in data["provinces"]}

# 1. Sub-provinces missing text labels
missing = [p["id"] for p in data["provinces"] if "/" in p["id"] and not p.get("text")]
if missing:
    print("MISSING text on sub-provinces:", missing)

# 2. Text values that look like concatenated multi-word labels
for p in data["provinces"]:
    for t in p.get("text", []):
        v = t["value"]
        if " " not in v and len(v) > 6 and any(c.isupper() for c in v[1:]):
            print(f"POSSIBLY CONCATENATED — {p['id']}: {repr(v)}")

# 3. Provinces with no text at all (expected to have names)
for p in data["provinces"]:
    if not p.get("text"):
        print(f"NO TEXT — {p['id']}")
```

Also do a visual pass: zoom into the map corners and edges where small labels tend to get clipped, and check all water bodies for correct multi-line stacking.
