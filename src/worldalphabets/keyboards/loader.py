import json
from importlib.resources import files, as_file
from typing import List
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
