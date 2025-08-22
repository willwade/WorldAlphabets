from importlib.resources import files
import json
from ..models.keyboard import KeyboardLayout
from typing import List

def get_available_layouts() -> List[str]:
    """
    Returns a list of available keyboard layout IDs.
    """
    pkg = files("worldalphabets.data.layouts")
    return sorted([p.name.replace(".json","") for p in pkg.iterdir() if p.name.endswith(".json")])

def load_keyboard(layout_id: str) -> KeyboardLayout:
    """
    Loads a keyboard layout by its ID.
    """
    pkg = files("worldalphabets.data.layouts")
    try:
        with (pkg / f"{layout_id}.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        return KeyboardLayout.model_validate(data)
    except FileNotFoundError:
        raise ValueError(f"Keyboard layout '{layout_id}' not found.")
