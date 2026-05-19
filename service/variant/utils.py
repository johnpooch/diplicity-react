import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass

from lxml import etree


DSVG_LAYER_ORDER = [
    "background",
    "provinces",
    "named-coasts",
    "unit-positions",
    "province-names",
    "borders",
    "foreground",
]

DSVG_HIDDEN_LAYERS = ("provinces", "named-coasts", "unit-positions")

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
INKSCAPE_NAMESPACE = "http://www.inkscape.org/namespaces/inkscape"
_ALLOWED_ATTRIBUTE_NAMESPACES = (SVG_NAMESPACE, XLINK_NAMESPACE)

GODIP_LAYER_TARGETS = {
    "background": "background",
    "provinces": "provinces",
    "foreground": "foreground",
    "names": "province-names",
    "province-centers": "unit-positions",
}

GODIP_RUNTIME_LAYERS = {
    "units",
    "orders",
    "highlights",
}

GODIP_SUPPLY_CENTER_LAYER = "supply-centers"
GODIP_SUPPLY_CENTER_ART_LAYER = "supply-centers foreground copy"

GODIP_DECORATIVE_LAYERS = {"noise"}

_GODIP_CENTER_SUFFIX = "Center"
_COORDINATE_PATTERN = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")

_GODIP_IGNORED_ELEMENTS = {"metadata", "namedview", "title", "desc"}


def _namespace(tag):
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


POSITION_MARKER_LAYERS = ("unit-positions", "supply-centers")
POSITION_MARKER_RADIUS = "10"


def normalize_dsvg(svg):
    root = etree.fromstring(svg.encode())

    foreign_elements = [
        element for element in root.iter() if _namespace(element.tag) not in (None, SVG_NAMESPACE)
    ]
    for element in foreign_elements:
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    etree.strip_elements(root, etree.Comment, with_tail=False)
    etree.strip_elements(root, f"{{{SVG_NAMESPACE}}}metadata", with_tail=False)

    for element in root.iter():
        for name in list(element.attrib):
            attribute_namespace = _namespace(name)
            if attribute_namespace is not None and attribute_namespace not in _ALLOWED_ATTRIBUTE_NAMESPACES:
                del element.attrib[name]
            elif attribute_namespace is None and name.startswith("data-"):
                del element.attrib[name]

    _set_position_marker_radius(root)

    etree.cleanup_namespaces(root)
    return _strip_svg_namespace_prefix(etree.tostring(root).decode())


def _set_position_marker_radius(root):
    for layer_id in POSITION_MARKER_LAYERS:
        layer = next(
            (
                child
                for child in root
                if _local_name(child.tag) == "g" and child.get("id") == layer_id
            ),
            None,
        )
        if layer is None:
            continue
        for circle in layer.iter(f"{{{SVG_NAMESPACE}}}circle"):
            circle.set("r", POSITION_MARKER_RADIUS)


_SVG_PREFIX_OPEN = re.compile(r"<svg:")
_SVG_PREFIX_CLOSE = re.compile(r"</svg:")
_SVG_PREFIX_DECL = re.compile(r'\sxmlns:svg="[^"]*"')


def _strip_svg_namespace_prefix(svg):
    svg = _SVG_PREFIX_OPEN.sub("<", svg)
    svg = _SVG_PREFIX_CLOSE.sub("</", svg)
    svg = _SVG_PREFIX_DECL.sub("", svg)
    return svg


def _svg_element(local_name):
    return etree.Element(f"{{{SVG_NAMESPACE}}}{local_name}")


def _polygon_to_path(polygon):
    path = _svg_element("path")
    for name, value in polygon.attrib.items():
        if _local_name(name) != "points":
            path.set(name, value)
    points = " ".join(polygon.get("points", "").split())
    path.set("d", f"M {points} Z")
    return path


def _flatten_province_group(group):
    path = _svg_element("path")
    province_id = group.get("id")
    if province_id:
        path.set("id", province_id)
    style = group.get("style")
    if style:
        path.set("style", style)
    segments = []
    for element in group.iter():
        local = _local_name(element.tag)
        if local == "path" and element.get("d"):
            segments.append(element.get("d"))
        elif local == "polygon" and element.get("points"):
            segments.append("M " + " ".join(element.get("points").split()) + " Z")
    path.set("d", " ".join(segments))
    return path


def _godip_province_path(element):
    local = _local_name(element.tag)
    if local == "path":
        return element
    if local == "polygon":
        return _polygon_to_path(element)
    if local == "g":
        return _flatten_province_group(element)
    return None


def _godip_center_anchor(d):
    if not d:
        return None
    numbers = _COORDINATE_PATTERN.findall(d)
    if len(numbers) < 2:
        return None
    return numbers[0], numbers[1]


def _godip_center_circle(element):
    if _local_name(element.tag) != "path":
        return None
    element_id = element.get("id") or ""
    if element_id.endswith(_GODIP_CENTER_SUFFIX):
        element_id = element_id[: -len(_GODIP_CENTER_SUFFIX)]
    anchor = _godip_center_anchor(element.get("d"))
    if not element_id or anchor is None:
        return None
    circle = _svg_element("circle")
    circle.set("id", element_id)
    circle.set("cx", anchor[0])
    circle.set("cy", anchor[1])
    return circle


def convert_godip_dsvg(svg):
    root = etree.fromstring(svg.encode())

    label_attribute = f"{{{INKSCAPE_NAMESPACE}}}label"
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        label = element.get(label_attribute)
        if label:
            element.set("id", label)

    warnings = []
    defs_elements = []
    godip_layers = {}
    noise_elements = []
    godip_supply_centers = None
    supply_center_art = []

    for child in list(root):
        if not isinstance(child.tag, str):
            continue
        local = _local_name(child.tag)
        child_id = child.get("id")
        if local in ("defs", "style"):
            defs_elements.append(child)
            continue
        if child_id in GODIP_DECORATIVE_LAYERS:
            noise_elements.append(child)
            continue
        if local != "g":
            if local not in _GODIP_IGNORED_ELEMENTS:
                warnings.append(f"Dropped unrecognized top-level <{local}> element (id={child_id!r}).")
            continue
        if child_id in GODIP_LAYER_TARGETS:
            godip_layers[GODIP_LAYER_TARGETS[child_id]] = child
        elif child_id == GODIP_SUPPLY_CENTER_LAYER:
            godip_supply_centers = child
            if not _is_hidden(child):
                supply_center_art.append(child)
        elif child_id == GODIP_SUPPLY_CENTER_ART_LAYER:
            supply_center_art.append(child)
        elif child_id in GODIP_RUNTIME_LAYERS:
            continue
        else:
            warnings.append(f"Dropped unrecognized layer <g id={child_id!r}>.")

    provinces_layer = _svg_element("g")
    provinces_layer.set("id", "provinces")
    provinces_layer.set("style", "display:none")
    named_coasts_layer = _svg_element("g")
    named_coasts_layer.set("id", "named-coasts")
    named_coasts_layer.set("style", "display:none")

    godip_provinces = godip_layers.get("provinces")
    if godip_provinces is None:
        warnings.append("Input has no 'provinces' layer.")
    else:
        for element in list(godip_provinces):
            path = _godip_province_path(element)
            if path is None:
                warnings.append(
                    f"Dropped non-province <{_local_name(element.tag)}> in provinces layer."
                )
                continue
            if "/" in (path.get("id") or ""):
                named_coasts_layer.append(path)
            else:
                provinces_layer.append(path)

    unit_positions_layer = _svg_element("g")
    unit_positions_layer.set("id", "unit-positions")
    unit_positions_layer.set("style", "display:none")

    godip_province_centers = godip_layers.get("unit-positions")
    if godip_province_centers is None:
        warnings.append("Input has no 'province-centers' layer.")
    if godip_supply_centers is None:
        warnings.append("Input has no 'supply-centers' layer.")

    for source_layer, source_name in (
        (godip_province_centers, "province-centers"),
        (godip_supply_centers, "supply-centers"),
    ):
        if source_layer is None:
            continue
        for element in list(source_layer):
            circle = _godip_center_circle(element)
            if circle is None:
                warnings.append(
                    f"Dropped non-position <{_local_name(element.tag)}> in '{source_name}' layer."
                )
                continue
            unit_positions_layer.append(circle)

    if not any("/" in (circle.get("id") or "") for circle in unit_positions_layer):
        warnings.append("'unit-positions' layer has no named-coast entries.")

    background_layer = godip_layers.get("background")
    if background_layer is None:
        background_layer = _svg_element("g")
        warnings.append("Synthesized empty 'background' layer.")
    background_layer.set("id", "background")

    province_names_layer = godip_layers.get("province-names")
    if province_names_layer is None:
        province_names_layer = _svg_element("g")
    province_names_layer.set("id", "province-names")

    borders_layer = _svg_element("g")
    borders_layer.set("id", "borders")

    foreground_layer = godip_layers.get("foreground")
    if foreground_layer is None:
        foreground_layer = _svg_element("g")
    foreground_layer.set("id", "foreground")
    for noise in noise_elements:
        if _local_name(noise.tag) == "g":
            for element in list(noise):
                foreground_layer.append(element)
        else:
            foreground_layer.append(noise)
    for art_layer in supply_center_art:
        for element in list(art_layer):
            foreground_layer.append(element)

    for child in list(root):
        root.remove(child)
    for defs in defs_elements:
        root.append(defs)
    root.append(background_layer)
    root.append(provinces_layer)
    root.append(named_coasts_layer)
    root.append(unit_positions_layer)
    root.append(province_names_layer)
    root.append(borders_layer)
    root.append(foreground_layer)

    return normalize_dsvg(etree.tostring(root).decode()), warnings


@dataclass(frozen=True)
class DsvgValidationError:
    code: str
    message: str


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _is_hidden(element):
    if element.get("display") == "none":
        return True
    for declaration in element.get("style", "").split(";"):
        prop, _, value = declaration.partition(":")
        if prop.strip().lower() == "display" and value.strip().lower() == "none":
            return True
    return False


def validate_dsvg(svg, variant=None):
    try:
        root = ElementTree.fromstring(svg)
    except ElementTree.ParseError as exc:
        return [DsvgValidationError("MALFORMED_XML", f"SVG is not well-formed XML: {exc}.")]

    errors = []
    layer_elements = [child for child in root if _local_name(child.tag) == "g"]
    layer_ids = [element.get("id") for element in layer_elements]

    for layer in DSVG_LAYER_ORDER:
        if layer not in layer_ids:
            errors.append(DsvgValidationError("MISSING_LAYER", f"Required layer '{layer}' is missing."))

    for layer_id in layer_ids:
        if layer_id not in DSVG_LAYER_ORDER:
            errors.append(
                DsvgValidationError("UNEXPECTED_LAYER", f"Unexpected top-level layer '{layer_id}'.")
            )

    present = [layer_id for layer_id in layer_ids if layer_id in DSVG_LAYER_ORDER]
    expected = [layer for layer in DSVG_LAYER_ORDER if layer in present]
    if present != expected:
        errors.append(
            DsvgValidationError(
                "LAYER_OUT_OF_ORDER",
                "Layers must appear in this order: " + ", ".join(DSVG_LAYER_ORDER) + ".",
            )
        )

    layers_by_id = {element.get("id"): element for element in layer_elements}
    for layer_id in DSVG_HIDDEN_LAYERS:
        element = layers_by_id.get(layer_id)
        if element is not None and not _is_hidden(element):
            errors.append(
                DsvgValidationError(
                    "LAYER_NOT_HIDDEN", f"Layer '{layer_id}' must be hidden with display:none."
                )
            )

    provinces_layer = layers_by_id.get("provinces")
    if provinces_layer is not None:
        for element in provinces_layer.iter():
            if _local_name(element.tag) == "path" and not element.get("id"):
                errors.append(
                    DsvgValidationError(
                        "PROVINCE_MISSING_ID", "A path in the 'provinces' layer is missing an id."
                    )
                )

    named_coasts_layer = layers_by_id.get("named-coasts")
    if named_coasts_layer is not None:
        for element in named_coasts_layer.iter():
            if _local_name(element.tag) != "path":
                continue
            parent, separator, coast = (element.get("id") or "").partition("/")
            if not (separator and parent and coast):
                errors.append(
                    DsvgValidationError(
                        "NAMED_COAST_INVALID_ID",
                        f"Named-coast path id '{element.get('id') or ''}' must use the form 'parent/coast'.",
                    )
                )

    for layer_id in POSITION_MARKER_LAYERS:
        layer = layers_by_id.get(layer_id)
        if layer is None:
            continue
        bad_ids = [
            element.get("id") or "<unnamed>"
            for element in layer.iter()
            if _local_name(element.tag) == "circle"
            and element.get("r") != POSITION_MARKER_RADIUS
        ]
        if bad_ids:
            preview = ", ".join(bad_ids[:5])
            if len(bad_ids) > 5:
                preview += f" (+{len(bad_ids) - 5} more)"
            errors.append(
                DsvgValidationError(
                    "MARKER_NOT_VISIBLE",
                    f"Circles in '{layer_id}' must have r='{POSITION_MARKER_RADIUS}' "
                    f"so positions are visible when the layer is unhidden. "
                    f"Offending ids: {preview}.",
                )
            )

    if variant is not None and provinces_layer is not None:
        svg_province_ids = {
            element.get("id")
            for element in provinces_layer.iter()
            if _local_name(element.tag) == "path" and element.get("id")
        }
        variant_province_ids = set(
            variant.provinces.filter(parent__isnull=True).values_list("province_id", flat=True)
        )
        for province_id in sorted(svg_province_ids - variant_province_ids):
            errors.append(
                DsvgValidationError(
                    "UNKNOWN_PROVINCE",
                    f"Province '{province_id}' is not a province of variant '{variant.id}'.",
                )
            )
        for province_id in sorted(variant_province_ids - svg_province_ids):
            errors.append(
                DsvgValidationError(
                    "MISSING_PROVINCE",
                    f"Variant province '{province_id}' has no path in the 'provinces' layer.",
                )
            )

    if variant is not None and named_coasts_layer is not None:
        svg_named_coast_ids = {
            element.get("id")
            for element in named_coasts_layer.iter()
            if _local_name(element.tag) == "path" and element.get("id")
        }
        variant_named_coast_ids = set(
            variant.provinces.filter(parent__isnull=False).values_list("province_id", flat=True)
        )
        for named_coast_id in sorted(svg_named_coast_ids - variant_named_coast_ids):
            errors.append(
                DsvgValidationError(
                    "UNKNOWN_NAMED_COAST",
                    f"Named coast '{named_coast_id}' is not a named coast of variant '{variant.id}'.",
                )
            )
        for named_coast_id in sorted(variant_named_coast_ids - svg_named_coast_ids):
            errors.append(
                DsvgValidationError(
                    "MISSING_NAMED_COAST",
                    f"Variant named coast '{named_coast_id}' has no path in the 'named-coasts' layer.",
                )
            )

    unit_positions_layer = layers_by_id.get("unit-positions")
    if variant is not None and unit_positions_layer is not None:
        svg_unit_position_ids = {
            element.get("id")
            for element in unit_positions_layer.iter()
            if _local_name(element.tag) == "circle" and element.get("id")
        }
        variant_position_ids = set(variant.provinces.values_list("province_id", flat=True))
        for position_id in sorted(svg_unit_position_ids - variant_position_ids):
            errors.append(
                DsvgValidationError(
                    "UNKNOWN_UNIT_POSITION",
                    f"Unit position '{position_id}' is not a province or named coast of variant '{variant.id}'.",
                )
            )
        for position_id in sorted(variant_position_ids - svg_unit_position_ids):
            errors.append(
                DsvgValidationError(
                    "MISSING_UNIT_POSITION",
                    f"Variant province or named coast '{position_id}' has no circle in the 'unit-positions' layer.",
                )
            )

    return errors
