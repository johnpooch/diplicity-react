import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass

from lxml import etree


DSVG_LAYER_ORDER = [
    "background",
    "provinces",
    "named-coasts",
    "province-names",
    "borders",
    "foreground",
]

DSVG_HIDDEN_LAYERS = ("provinces", "named-coasts")

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
_ALLOWED_ATTRIBUTE_NAMESPACES = (SVG_NAMESPACE, XLINK_NAMESPACE)


def _namespace(tag):
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


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

    etree.cleanup_namespaces(root)
    return etree.tostring(root).decode()


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

    return errors
