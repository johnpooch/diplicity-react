#!/usr/bin/env python3
"""
Generate youngstown-redux.json from the SVG map file.

Extracts:
- All background elements (land bg + sea-colored areas)
- All province paths with centers, supply centers, text labels
- All foreground border paths
"""

import json
import math
import re
import sys
import xml.etree.ElementTree as ET

SVG_PATH = "packages/maps/youngstown-redux/map.svg"
IDS_PATH = "packages/maps/youngstown-redux/ids.json"
OUTPUT_PATH = "packages/web/public/maps/youngstown-redux.json"

NS = "http://www.w3.org/2000/svg"


def parse_style(style_str):
    """Parse an SVG inline style string into a dict."""
    result = {}
    for part in style_str.split(";"):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def style_to_map(style_str):
    """Convert SVG style string to the JSON styles format for background elements."""
    s = parse_style(style_str)
    return {
        "fill": s.get("fill", "none"),
        "stroke": s.get("stroke", "none"),
        "strokeWidth": float(re.sub(r"[^\d.]", "", s.get("stroke-width", "1") or "1") or "1"),
    }


def rect_to_path(el):
    """Convert a <rect> SVG element to a path 'd' string."""
    x = float(el.get("x", 0))
    y = float(el.get("y", 0))
    w = float(el.get("width", 0))
    h = float(el.get("height", 0))
    return f"M {x} {y} L {x+w} {y} L {x+w} {y+h} L {x} {y+h} Z"


def first_move_point(d):
    """Extract the first absolute M or m coordinate from a path as the center point."""
    # Match first M X,Y or m X,Y (handles optional comma or space separator)
    m = re.match(r"\s*[Mm]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)[,\s]+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", d)
    if m:
        return {"x": round(float(m.group(1)), 4), "y": round(float(m.group(2)), 4)}
    return None


def path_bounding_box_center(d):
    """Estimate center using bounding box of M/L/H/V absolute commands only."""
    xs, ys = [], []
    for token in re.finditer(r"([MLml])\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)[,\s]+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", d):
        xs.append(float(token.group(2)))
        ys.append(float(token.group(3)))
    if not xs:
        return first_move_point(d)
    return {"x": round((min(xs) + max(xs)) / 2, 4), "y": round((min(ys) + max(ys)) / 2, 4)}


def apply_rotate(x, y, angle_deg, cx=0, cy=0):
    """Apply a rotate(angle, cx, cy) transform to (x, y)."""
    angle = math.radians(angle_deg)
    tx = x - cx
    ty = y - cy
    rx = tx * math.cos(angle) - ty * math.sin(angle)
    ry = tx * math.sin(angle) + ty * math.cos(angle)
    return rx + cx, ry + cy


def normalize(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def get_layer(root, layer_id):
    for child in root:
        if child.get("id") == layer_id:
            return child
    return None


def extract_background_elements(bg_layer):
    """Extract all elements from the background layer."""
    elements = []
    for el in bg_layer:
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        style_str = el.get("style", "")
        styles = style_to_map(style_str)
        el_id = el.get("id", "")

        if tag == "rect":
            d = rect_to_path(el)
        elif tag == "path":
            d = el.get("d", "")
        else:
            continue

        if not d:
            continue

        elements.append({
            "id": el_id,
            "d": d,
            "styles": styles,
        })
    return elements


def extract_borders(fg_layer):
    """Extract all border paths from the foreground layer."""
    borders = []
    for el in fg_layer:
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag != "path":
            continue
        d = el.get("d", "")
        if not d:
            continue
        borders.append({
            "id": el.get("id", ""),
            "d": d,
        })
    return borders


def extract_supply_centers(sc_layer):
    """Extract supply center positions from supply-centers layer."""
    centers = {}
    for el in sc_layer:
        el_id = el.get("id", "")
        # IDs like "ber_sc", "lon_sc", etc.  or "berCenter", "lonCenter"
        # The layer uses paths named {province_id}Center
        d = el.get("d", "")
        if not d:
            continue
        center = first_move_point(d)
        if not center:
            continue
        # Strip suffixes to get province id
        prov_id = re.sub(r"(Center|_sc|_SC|_center)$", "", el_id, flags=re.IGNORECASE)
        centers[prov_id] = center
    return centers


def extract_province_centers(pc_layer):
    """Extract province center dots from province-centers layer."""
    centers = {}
    for el in pc_layer:
        el_id = el.get("id", "")
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "circle":
            cx = el.get("cx", "")
            cy = el.get("cy", "")
            if cx and cy:
                prov_id = re.sub(r"(Center|_center|_dot)$", "", el_id, flags=re.IGNORECASE)
                try:
                    centers[prov_id] = {"x": round(float(cx), 4), "y": round(float(cy), 4)}
                except ValueError:
                    pass
        elif tag == "path":
            d = el.get("d", "")
            # Province-center dots use "m X,Y c ..." — the first coord IS the center
            center = first_move_point(d)
            if center:
                prov_id = re.sub(r"(Center|_center)$", "", el_id, flags=re.IGNORECASE)
                centers[prov_id] = center
    return centers


def _apply_transform(x, y, transform):
    """Apply SVG transform (translate, rotate) to coordinates."""
    if not transform:
        return x, y
    m = re.search(r"translate\(([-\d.]+)[,\s]+([-\d.]+)\)", transform)
    if m:
        x += float(m.group(1))
        y += float(m.group(2))
    m = re.search(r"rotate\(([-\d.]+)(?:[,\s]+([-\d.]+)[,\s]+([-\d.]+))?\)", transform)
    if m:
        angle = float(m.group(1))
        rcx = float(m.group(2)) if m.group(2) else 0.0
        rcy = float(m.group(3)) if m.group(3) else 0.0
        x, y = apply_rotate(x, y, angle, rcx, rcy)
    return x, y


def extract_text_labels(names_layer):
    """Extract text labels with their positions, handling multi-line tspans and rotation."""
    texts_by_norm = {}

    for el in names_layer:
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag not in ("text", "flowRoot", "g"):
            continue

        # Full text for province name matching
        full_text = "".join(el.itertext()).strip()
        if not full_text:
            continue

        transform = el.get("transform", "")
        style_str = el.get("style", "")
        s = parse_style(style_str)
        font_size = s.get("font-size", "16px")

        text_anchor = "middle"
        if "text-anchor:start" in style_str or "text-align:left" in style_str:
            text_anchor = "start"
        elif "text-anchor:end" in style_str or "text-align:right" in style_str:
            text_anchor = "end"

        base_styles = {
            "fontSize": font_size,
            "fontFamily": s.get("font-family", "sans-serif"),
            "textAnchor": text_anchor,
        }

        # Detect rotation angle for transform attribute
        rotation_angle = None
        if transform:
            rm = re.search(r"rotate\(([-\d.]+)", transform)
            if rm:
                rotation_angle = float(rm.group(1))

        # Collect text entries — one per tspan line
        entries = []
        children = list(el)

        if len(children) <= 1:
            # Single-line label: use the first tspan's or parent's position
            x_str = el.get("x", "")
            y_str = el.get("y", "")
            if not x_str or not y_str:
                for child in children:
                    cx = child.get("x", "")
                    cy = child.get("y", "")
                    if cx and cy:
                        x_str, y_str = cx, cy
                        break
            try:
                x = float(x_str) if x_str else 0.0
                y = float(y_str) if y_str else 0.0
            except ValueError:
                x, y = 0.0, 0.0
            x, y = _apply_transform(x, y, transform)
            entry = {
                "point": {"x": round(x, 2), "y": round(y, 2)},
                "value": full_text,
                "styles": base_styles,
            }
            if rotation_angle is not None:
                entry["transform"] = f"rotate({rotation_angle}, {round(x, 2)}, {round(y, 2)})"
            entries.append(entry)
        else:
            # Multi-line label: one entry per top-level tspan
            for child in children:
                line_text = "".join(child.itertext()).strip()
                if not line_text:
                    continue
                lx_str = child.get("x", el.get("x", ""))
                ly_str = child.get("y", el.get("y", ""))
                try:
                    lx = float(lx_str) if lx_str else 0.0
                    ly = float(ly_str) if ly_str else 0.0
                except ValueError:
                    lx, ly = 0.0, 0.0
                lx, ly = _apply_transform(lx, ly, transform)
                entry = {
                    "point": {"x": round(lx, 2), "y": round(ly, 2)},
                    "value": line_text,
                    "styles": base_styles,
                }
                if rotation_angle is not None:
                    entry["transform"] = f"rotate({rotation_angle}, {round(lx, 2)}, {round(ly, 2)})"
                entries.append(entry)

        if entries:
            # For Box labels like "Box Abcd", clean to "Box A" for matching
            # SVG has 2 tspans: "Box A" + "bcd" (connections) — keep only first
            match_text = full_text
            box_match = re.match(r"^(Box\s+[A-H])", full_text, re.IGNORECASE)
            if box_match:
                match_text = box_match.group(1)
                entries = [entries[0]]
                entries[0]["value"] = match_text

            norm = normalize(match_text)
            if norm not in texts_by_norm:
                texts_by_norm[norm] = []
            texts_by_norm[norm].extend(entries)

    return texts_by_norm


def main():
    # Load IDs mapping: province_name -> province_id
    with open(IDS_PATH) as f:
        ids_map = json.load(f)

    # Build reverse: normalize(name) -> province_id
    norm_to_id = {normalize(name): pid for name, pid in ids_map.items()}

    # Parse SVG
    tree = ET.parse(SVG_PATH)
    root = tree.getroot()

    # Get SVG dimensions
    viewbox = root.get("viewBox", "0 0 4320 2160").split()
    width = float(viewbox[2])
    height = float(viewbox[3])

    # Get layers
    bg_layer = get_layer(root, "background")
    provinces_layer = get_layer(root, "provinces")
    sc_layer = get_layer(root, "supply-centers")
    pc_layer = get_layer(root, "province-centers")
    fg_layer = get_layer(root, "foreground")
    names_layer = get_layer(root, "layer9")  # names

    print(f"Layers found: bg={bg_layer is not None}, provinces={provinces_layer is not None}, "
          f"sc={sc_layer is not None}, pc={pc_layer is not None}, "
          f"fg={fg_layer is not None}, names={names_layer is not None}")

    # 1. Background elements (land bg + all sea areas)
    background_elements = extract_background_elements(bg_layer) if bg_layer is not None else []
    print(f"Background elements: {len(background_elements)}")

    # 2. Supply centers
    sc_centers = extract_supply_centers(sc_layer) if sc_layer is not None else {}
    print(f"Supply center centers: {len(sc_centers)}")

    # 3. Province centers
    prov_centers = extract_province_centers(pc_layer) if pc_layer is not None else {}
    print(f"Province centers: {len(prov_centers)}")

    # 4. Text labels
    texts_by_norm = extract_text_labels(names_layer) if names_layer is not None else {}
    print(f"Unique text labels: {len(texts_by_norm)}")

    # 5. Province paths
    provinces = []
    matched_texts = set()

    # Build a mapping from province id -> supply center position
    # The SC layer IDs may be like "lon_sc" or just "lon" or "lonCenter"
    sc_by_id = {}
    for k, v in sc_centers.items():
        sc_by_id[k.lower()] = v

    for el in (provinces_layer or []):
        el_id = el.get("id", "")
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag != "path":
            continue
        d = el.get("d", "")
        if not d:
            continue

        style_str = el.get("style", "")
        styles = style_to_map(style_str)

        # Determine supply center position first
        sc = sc_by_id.get(el_id.lower()) or sc_by_id.get(el_id.lower() + "center")

        # Province center: prefer province-centers layer, then supply-center position
        # (supply center provinces don't appear in province-centers layer)
        # then fall back to path bounding box
        center = (
            prov_centers.get(el_id)
            or prov_centers.get(el_id + "Center")
            or sc  # supply center provinces use SC position as province center
            or path_bounding_box_center(d)
        )
        if not center:
            continue

        # Find text label - match by province ID first, then by normalized name
        prov_texts = []
        # Try to find the province name from ids_map
        prov_name = None
        for name, pid in ids_map.items():
            if pid == el_id:
                prov_name = name
                break

        if prov_name:
            norm = normalize(prov_name)
            if norm in texts_by_norm:
                prov_texts = texts_by_norm[norm]
                matched_texts.add(norm)

        prov_obj = {
            "id": el_id,
            "path": {
                "d": d,
            },
            "center": center,
        }
        if sc:
            prov_obj["supplyCenter"] = sc
        if prov_texts:
            prov_obj["text"] = prov_texts

        provinces.append(prov_obj)

    print(f"Provinces parsed: {len(provinces)}")
    print(f"With supply centers: {sum(1 for p in provinces if 'supplyCenter' in p)}")
    print(f"With text: {sum(1 for p in provinces if 'text' in p)}")

    # 6. Borders from foreground
    borders = extract_borders(fg_layer) if fg_layer is not None else []
    print(f"Border paths: {len(borders)}")

    # 7. Build output
    output = {
        "width": width,
        "height": height,
        "provinces": provinces,
        "backgroundElements": background_elements,
        "borders": borders,
        "impassableProvinces": [],
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    print(f"\nWritten to {OUTPUT_PATH}")
    size_kb = len(json.dumps(output)) / 1024
    print(f"File size: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
