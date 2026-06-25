from typing import Optional

_PALETTES = {
    "deuteranopia": {
        "#F44336": "#D55E00",
        "#2196F3": "#0072B2",
        "#80DEEA": "#56B4E9",
        "#90A4AE": "#999999",
        "#4CAF50": "#CC79A7",
        "#F5F5F5": "#F5F5F5",
        "#FFC107": "#F0E442",
    },
    "protanopia": {
        "#F44336": "#E69F00",
        "#2196F3": "#0072B2",
        "#80DEEA": "#56B4E9",
        "#90A4AE": "#999999",
        "#4CAF50": "#CC79A7",
        "#F5F5F5": "#F5F5F5",
        "#FFC107": "#F0E442",
    },
    "tritanopia": {
        "#F44336": "#F44336",
        "#2196F3": "#009E73",
        "#80DEEA": "#80DEEA",
        "#90A4AE": "#999999",
        "#4CAF50": "#4CAF50",
        "#F5F5F5": "#F5F5F5",
        "#FFC107": "#CC79A7",
    },
}


def apply_colorblind_palette(color: str, mode: Optional[str]) -> str:
    if mode is None:
        return color
    palette = _PALETTES.get(mode, {})
    return palette.get(color.upper(), color)
