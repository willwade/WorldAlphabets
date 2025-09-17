import json
from importlib.resources import files, as_file
from typing import Dict, Iterable, List
from pathlib import Path

from ..models.keyboard import KeyboardLayout

with as_file(files("worldalphabets")) as p:
    _PACKAGE_PATH = Path(p)
DATA_DIR = _PACKAGE_PATH.parent.parent / "data"
LAYOUTS_DIR = DATA_DIR / "layouts"

def get_available_layouts() -> List[str]:
    """
    Returns a list of available keyboard layout IDs.
    """
    if not LAYOUTS_DIR.is_dir():
        return []
    return sorted([p.name.replace(".json","") for p in LAYOUTS_DIR.iterdir() if p.name.endswith(".json")])

def load_keyboard(layout_id: str) -> KeyboardLayout:
    """
    Loads a keyboard layout by its ID.
    """
    layout_path = LAYOUTS_DIR / f"{layout_id}.json"
    try:
        with open(layout_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return KeyboardLayout.model_validate(data)
    except FileNotFoundError:
        raise ValueError(f"Keyboard layout '{layout_id}' not found.")


DEFAULT_LAYERS: tuple[str, ...] = (
    "base",
    "shift",
    "caps",
    "altgr",
    "shift_altgr",
    "ctrl",
    "alt",
)


def extract_layers(
    layout: KeyboardLayout, layers: Iterable[str] | None = None
) -> Dict[str, Dict[str, str]]:
    """Return a mapping of layer name to key legends for the given layout."""

    result: Dict[str, Dict[str, str]] = {}
    target_layers = list(layers) if layers is not None else list(DEFAULT_LAYERS)

    for layer in target_layers:
        layer_values: Dict[str, str] = {}
        for key in layout.keys:
            if key.legends is None:
                continue
            value = getattr(key.legends, layer, None)
            if not value:
                continue
            pos = key.pos or key.vk or key.sc
            if pos:
                layer_values[str(pos)] = value
        if layer_values:
            result[layer] = layer_values

    return result
