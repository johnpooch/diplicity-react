import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from lxml import etree

from common.constants import ProvinceType


SCHEMA_VERSION = 1

DVAR_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "variant.schema.yaml"


@dataclass(frozen=True)
class DvarValidationError:
    code: str
    message: str
    path: str = ""


@lru_cache(maxsize=1)
def _dvar_validator():
    with open(DVAR_SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    return Draft202012Validator(schema)


def _format_jsonschema_path(error):
    if not error.absolute_path:
        return ""
    return ".".join(str(part) for part in error.absolute_path)


def validate_dvar(dvar):
    if not isinstance(dvar, dict):
        return [DvarValidationError("INVALID_PAYLOAD", "DVAR must be a JSON object.")]

    errors = [
        DvarValidationError(
            code="SCHEMA_VIOLATION",
            message=error.message,
            path=_format_jsonschema_path(error),
        )
        for error in sorted(_dvar_validator().iter_errors(dvar), key=lambda e: e.absolute_path)
    ]
    if errors:
        return errors

    errors.extend(_validate_dvar_references(dvar))
    errors.extend(_validate_dvar_adjacencies(dvar))
    return errors


def _validate_dvar_references(dvar):
    errors = []
    nation_ids = {nation["id"] for nation in dvar["nations"]}
    province_ids = {province["id"] for province in dvar["provinces"]}
    named_coast_ids = {coast["id"] for coast in dvar.get("namedCoasts", [])}
    location_ids = province_ids | named_coast_ids

    for province in dvar["provinces"]:
        if "homeNation" in province and province["homeNation"] not in nation_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_NATION",
                    f"Province '{province['id']}' references unknown homeNation '{province['homeNation']}'.",
                    f"provinces.{province['id']}.homeNation",
                )
            )

    for coast in dvar.get("namedCoasts", []):
        if coast["parentProvince"] not in province_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_PROVINCE",
                    f"Named coast '{coast['id']}' references unknown parentProvince '{coast['parentProvince']}'.",
                    f"namedCoasts.{coast['id']}.parentProvince",
                )
            )

    initial = dvar["initialState"]
    for unit in initial["units"]:
        if unit["nation"] not in nation_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_NATION",
                    f"Initial unit at '{unit['location']}' references unknown nation '{unit['nation']}'.",
                    "initialState.units",
                )
            )
        if unit["location"] not in location_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_LOCATION",
                    f"Initial unit references unknown location '{unit['location']}'.",
                    "initialState.units",
                )
            )

    for sc in initial["supplyCenters"]:
        if sc["nation"] not in nation_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_NATION",
                    f"Initial supply center at '{sc['province']}' references unknown nation '{sc['nation']}'.",
                    "initialState.supplyCenters",
                )
            )
        if sc["province"] not in province_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_PROVINCE",
                    f"Initial supply center references unknown province '{sc['province']}'.",
                    "initialState.supplyCenters",
                )
            )

    return errors


def _validate_dvar_adjacencies(dvar):
    errors = []
    edges = {}
    for province in dvar["provinces"]:
        for adjacency in province.get("adjacencies", []):
            edges[(province["id"], adjacency["to"])] = adjacency["pass"]
    for coast in dvar.get("namedCoasts", []):
        for adjacency in coast.get("adjacencies", []):
            edges[(coast["id"], adjacency["to"])] = adjacency["pass"]

    location_ids = (
        {province["id"] for province in dvar["provinces"]}
        | {coast["id"] for coast in dvar.get("namedCoasts", [])}
    )

    for (source, target), pass_kind in edges.items():
        if target not in location_ids:
            errors.append(
                DvarValidationError(
                    "UNKNOWN_ADJACENCY",
                    f"Adjacency '{source}' → '{target}' references unknown location.",
                    f"adjacencies.{source}",
                )
            )
            continue
        reverse = edges.get((target, source))
        if reverse is None:
            errors.append(
                DvarValidationError(
                    "ASYMMETRIC_ADJACENCY",
                    f"Adjacency '{source}' → '{target}' has no matching '{target}' → '{source}' entry.",
                    f"adjacencies.{source}",
                )
            )
        elif reverse != pass_kind:
            errors.append(
                DvarValidationError(
                    "INCONSISTENT_ADJACENCY",
                    f"Adjacency '{source}' ↔ '{target}' has mismatched pass: '{pass_kind}' vs '{reverse}'.",
                    f"adjacencies.{source}",
                )
            )

    return errors


def variant_to_canonical_dict(variant):
    nations = list(variant.nations.all())
    provinces = list(variant.provinces.all())
    nation_id_by_pk = {nation.pk: nation.nation_id for nation in nations}
    province_id_by_pk = {province.pk: province.province_id for province in provinces}
    template_phase = variant.template_phase

    canonical_provinces = []
    canonical_named_coasts = []
    for province in provinces:
        if province.type == ProvinceType.NAMED_COAST:
            canonical_named_coasts.append(
                {
                    "id": province.province_id,
                    "name": province.name,
                    "parentProvince": province_id_by_pk[province.parent_id],
                    "adjacencies": province.adjacencies,
                }
            )
            continue
        canonical_province = {
            "id": province.province_id,
            "name": province.name,
            "type": province.type,
            "supplyCenter": province.supply_center,
            "adjacencies": province.adjacencies,
        }
        if province.home_nation_id is not None:
            canonical_province["homeNation"] = nation_id_by_pk[province.home_nation_id]
        canonical_provinces.append(canonical_province)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "id": variant.id,
        "name": variant.name,
        "description": variant.description,
        "author": variant.author,
        "rules": variant.rules,
        "victoryConditions": variant.victory_conditions,
        "adjudicationModifiers": variant.adjudication_modifiers,
        "phaseProgression": variant.phase_progression,
        "nations": [
            {"id": nation.nation_id, "name": nation.name, "color": nation.color}
            for nation in nations
        ],
        "provinces": canonical_provinces,
        "namedCoasts": canonical_named_coasts,
        "initialState": {
            "phase": {
                "season": template_phase.season,
                "year": template_phase.year,
                "type": template_phase.type,
            },
            "units": [
                {
                    "nation": nation_id_by_pk[unit.nation_id],
                    "type": unit.type,
                    "location": province_id_by_pk[unit.province_id],
                }
                for unit in template_phase.units.all()
            ],
            "supplyCenters": [
                {
                    "nation": nation_id_by_pk[supply_center.nation_id],
                    "province": province_id_by_pk[supply_center.province_id],
                }
                for supply_center in template_phase.supply_centers.all()
            ],
        },
    }


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


_DANGEROUS_URL_PREFIX = re.compile(r"^\s*javascript:", re.IGNORECASE)
_HREF_LIKE_ATTRS = ("href", "to")
_DANGEROUS_ELEMENTS = ("script", "foreignObject", "handler")


def sanitize_svg(svg):
    root = etree.fromstring(svg.encode())

    for element in list(root.iter()):
        if _local_name(element.tag) in _DANGEROUS_ELEMENTS:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

    for element in root.iter():
        for name in list(element.attrib):
            local = _local_name(name)
            if local.lower().startswith("on"):
                del element.attrib[name]
                continue
            if local in _HREF_LIKE_ATTRS:
                value = element.attrib.get(name, "")
                if _DANGEROUS_URL_PREFIX.match(value):
                    del element.attrib[name]

    return _strip_svg_namespace_prefix(etree.tostring(root).decode())


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


def create_variant_from_dvar(dvar, owner=None, status=None):
    from common.constants import VariantStatus
    from variant.models import Variant

    if status is None:
        status = VariantStatus.DRAFT

    variant = Variant.objects.create(
        id=dvar["id"],
        name=dvar["name"],
        description=dvar["description"],
        author=dvar.get("author", ""),
        rules=dvar.get("rules", ""),
        victory_conditions=dvar["victoryConditions"],
        adjudication_modifiers=dvar.get("adjudicationModifiers", []),
        phase_progression=dvar["phaseProgression"],
        status=status,
        owner=owner,
    )
    _build_variant_children(variant, dvar)
    return variant


def update_variant_from_dvar(variant, dvar):
    from game.models import Game
    from nation.models import Nation, NationFlag
    from phase.models import Phase
    from province.models import Province

    flag_snapshot = dict(
        NationFlag.objects.filter(nation__variant=variant).values_list(
            "nation__nation_id", "svg"
        )
    )

    Game.objects.filter(variant=variant).delete()
    Phase.objects.filter(variant=variant).delete()
    Province.objects.filter(variant=variant, parent__isnull=False).delete()
    Province.objects.filter(variant=variant).delete()
    Nation.objects.filter(variant=variant).delete()

    if hasattr(variant, "_prefetched_objects_cache"):
        variant._prefetched_objects_cache.clear()

    variant.name = dvar["name"]
    variant.description = dvar["description"]
    variant.author = dvar.get("author", "")
    variant.rules = dvar.get("rules", "")
    variant.victory_conditions = dvar["victoryConditions"]
    variant.adjudication_modifiers = dvar.get("adjudicationModifiers", [])
    variant.phase_progression = dvar["phaseProgression"]
    variant.save()

    _build_variant_children(variant, dvar)

    if flag_snapshot:
        surviving = {
            nation.nation_id: nation
            for nation in Nation.objects.filter(
                variant=variant, nation_id__in=flag_snapshot.keys()
            )
        }
        for nation_id, svg in flag_snapshot.items():
            nation = surviving.get(nation_id)
            if nation is not None:
                NationFlag.objects.create(nation=nation, svg=svg)

    return variant


@dataclass(frozen=True)
class SafeReplacementError:
    code: str
    message: str


def validate_safe_replacement(variant, dvar):
    from supply_center.models import SupplyCenter
    from unit.models import Unit

    errors = list(validate_dvar(dvar))
    if errors:
        return [SafeReplacementError(error.code, error.message) for error in errors]

    if dvar["id"] != variant.id:
        return [
            SafeReplacementError(
                "VARIANT_ID_MISMATCH",
                f"DVAR id '{dvar['id']}' does not match variant id '{variant.id}'.",
            )
        ]

    errors = []

    old_nation_ids = set(variant.nations.values_list("nation_id", flat=True))
    new_nation_ids = {nation["id"] for nation in dvar["nations"]}
    for nation_id in sorted(new_nation_ids - old_nation_ids):
        errors.append(
            SafeReplacementError(
                "NATION_ADDED",
                f"Nation '{nation_id}' is in the new DVAR but not in the existing variant.",
            )
        )
    for nation_id in sorted(old_nation_ids - new_nation_ids):
        errors.append(
            SafeReplacementError(
                "NATION_REMOVED",
                f"Nation '{nation_id}' exists in the variant but is missing from the new DVAR.",
            )
        )

    old_provinces = {
        province.province_id: province for province in variant.provinces.all()
    }
    new_province_parent_by_id = {
        province["id"]: None for province in dvar["provinces"]
    }
    for coast in dvar.get("namedCoasts", []):
        new_province_parent_by_id[coast["id"]] = coast["parentProvince"]
    new_province_sc_by_id = {
        province["id"]: province["supplyCenter"] for province in dvar["provinces"]
    }

    for province_id in sorted(set(new_province_parent_by_id) - set(old_provinces)):
        errors.append(
            SafeReplacementError(
                "PROVINCE_ADDED",
                f"Province '{province_id}' is in the new DVAR but not in the existing variant.",
            )
        )
    for province_id in sorted(set(old_provinces) - set(new_province_parent_by_id)):
        errors.append(
            SafeReplacementError(
                "PROVINCE_REMOVED",
                f"Province '{province_id}' exists in the variant but is missing from the new DVAR.",
            )
        )

    province_ids_with_units = set(
        Unit.objects.filter(province__variant=variant)
        .exclude(phase__game__isnull=True)
        .values_list("province__province_id", flat=True)
        .distinct()
    )
    for province_id in sorted(province_ids_with_units):
        if province_id not in new_province_parent_by_id or province_id not in old_provinces:
            continue
        old_parent_id = (
            old_provinces[province_id].parent.province_id
            if old_provinces[province_id].parent_id
            else None
        )
        new_parent_id = new_province_parent_by_id[province_id]
        if old_parent_id != new_parent_id:
            errors.append(
                SafeReplacementError(
                    "PARENT_CHANGED",
                    f"Province '{province_id}' has units in active games; "
                    f"its named-coast parent cannot change "
                    f"(was {old_parent_id!r}, now {new_parent_id!r}).",
                )
            )

    province_ids_with_supply_centers = set(
        SupplyCenter.objects.filter(province__variant=variant)
        .exclude(phase__game__isnull=True)
        .values_list("province__province_id", flat=True)
        .distinct()
    )
    for province_id in sorted(province_ids_with_supply_centers):
        if province_id not in new_province_sc_by_id:
            continue
        if not new_province_sc_by_id[province_id]:
            errors.append(
                SafeReplacementError(
                    "SUPPLY_CENTER_REMOVED",
                    f"Province '{province_id}' holds supply centers in active games "
                    f"but is no longer marked as a supply center in the new DVAR.",
                )
            )

    return errors


def apply_safe_replacement(variant, dvar, dsvg_text):
    from common.constants import PhaseStatus, ProvinceType
    from nation.models import Nation
    from phase.models import Phase
    from province.models import Province
    from supply_center.models import SupplyCenter
    from unit.models import Unit
    from variant.models import VariantSvg

    province_type_for = {
        "land": ProvinceType.LAND,
        "sea": ProvinceType.SEA,
        "coastal": ProvinceType.COASTAL,
    }

    variant.name = dvar["name"]
    variant.description = dvar["description"]
    variant.author = dvar.get("author", "")
    variant.rules = dvar.get("rules", "")
    variant.victory_conditions = dvar["victoryConditions"]
    variant.adjudication_modifiers = dvar.get("adjudicationModifiers", [])
    variant.phase_progression = dvar["phaseProgression"]
    variant.save()

    nation_by_id = {nation.nation_id: nation for nation in variant.nations.all()}
    for payload in dvar["nations"]:
        nation = nation_by_id[payload["id"]]
        nation.name = payload["name"]
        nation.color = payload["color"]
        nation.save()
    nation_by_id = {nation.nation_id: nation for nation in variant.nations.all()}

    province_by_id = {province.province_id: province for province in variant.provinces.all()}
    for payload in dvar["provinces"]:
        province = province_by_id[payload["id"]]
        province.name = payload["name"]
        province.type = province_type_for[payload["type"]]
        province.supply_center = payload["supplyCenter"]
        province.home_nation = nation_by_id.get(payload.get("homeNation"))
        province.parent = None
        province.adjacencies = payload.get("adjacencies", [])
        province.save()
    for payload in dvar.get("namedCoasts", []):
        province = province_by_id[payload["id"]]
        province.name = payload["name"]
        province.type = ProvinceType.NAMED_COAST
        province.supply_center = False
        province.home_nation = None
        province.parent = province_by_id[payload["parentProvince"]]
        province.adjacencies = payload.get("adjacencies", [])
        province.save()

    Phase.objects.filter(variant=variant, game__isnull=True).delete()
    initial = dvar["initialState"]
    template_phase = Phase.objects.create(
        variant=variant,
        game=None,
        ordinal=1,
        status=PhaseStatus.TEMPLATE,
        season=initial["phase"]["season"],
        year=initial["phase"]["year"],
        type=initial["phase"]["type"],
    )
    Unit.objects.bulk_create(
        [
            Unit(
                phase=template_phase,
                type=unit["type"],
                nation=nation_by_id[unit["nation"]],
                province=province_by_id[unit["location"]],
            )
            for unit in initial["units"]
        ]
    )
    SupplyCenter.objects.bulk_create(
        [
            SupplyCenter(
                phase=template_phase,
                nation=nation_by_id[sc["nation"]],
                province=province_by_id[sc["province"]],
            )
            for sc in initial["supplyCenters"]
        ]
    )

    VariantSvg.objects.update_or_create(variant=variant, defaults={"svg": dsvg_text})

    if hasattr(variant, "_prefetched_objects_cache"):
        variant._prefetched_objects_cache.clear()

    return variant


def _build_variant_children(variant, dvar):
    from common.constants import PhaseStatus, ProvinceType
    from nation.models import Nation
    from phase.models import Phase
    from province.models import Province
    from supply_center.models import SupplyCenter
    from unit.models import Unit

    province_type_for = {
        "land": ProvinceType.LAND,
        "sea": ProvinceType.SEA,
        "coastal": ProvinceType.COASTAL,
    }

    nations_to_create = [
        Nation(
            variant=variant,
            nation_id=nation["id"],
            name=nation["name"],
            color=nation["color"],
        )
        for nation in dvar["nations"]
    ]
    Nation.objects.bulk_create(nations_to_create)
    nation_by_id = {nation.nation_id: nation for nation in Nation.objects.filter(variant=variant)}

    parents_to_create = [
        Province(
            variant=variant,
            province_id=province["id"],
            name=province["name"],
            type=province_type_for[province["type"]],
            supply_center=province["supplyCenter"],
            home_nation=nation_by_id.get(province.get("homeNation")),
            adjacencies=province.get("adjacencies", []),
        )
        for province in dvar["provinces"]
    ]
    Province.objects.bulk_create(parents_to_create)
    province_by_id = {province.province_id: province for province in Province.objects.filter(variant=variant)}

    coasts_to_create = [
        Province(
            variant=variant,
            province_id=coast["id"],
            name=coast["name"],
            type=ProvinceType.NAMED_COAST,
            supply_center=False,
            parent=province_by_id[coast["parentProvince"]],
            adjacencies=coast.get("adjacencies", []),
        )
        for coast in dvar.get("namedCoasts", [])
    ]
    Province.objects.bulk_create(coasts_to_create)
    province_by_id = {province.province_id: province for province in Province.objects.filter(variant=variant)}

    initial = dvar["initialState"]
    template_phase = Phase.objects.create(
        variant=variant,
        game=None,
        ordinal=1,
        status=PhaseStatus.TEMPLATE,
        season=initial["phase"]["season"],
        year=initial["phase"]["year"],
        type=initial["phase"]["type"],
    )

    Unit.objects.bulk_create(
        [
            Unit(
                phase=template_phase,
                type=unit["type"],
                nation=nation_by_id[unit["nation"]],
                province=province_by_id[unit["location"]],
            )
            for unit in initial["units"]
        ]
    )

    SupplyCenter.objects.bulk_create(
        [
            SupplyCenter(
                phase=template_phase,
                nation=nation_by_id[sc["nation"]],
                province=province_by_id[sc["province"]],
            )
            for sc in initial["supplyCenters"]
        ]
    )
