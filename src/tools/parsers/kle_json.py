import json
import re
from typing import List, Dict, Any

def parse_kle_json(json_content: str) -> List[Dict[str, Any]]:
    """
    Parses a Keyboard Layout Editor (KLE) JSON file and returns a list of key geometries.
    This is a simplified parser that focuses on extracting the position and size of each key.
    """
    # The KLE JSON downloaded from kbdlayout.info is not strictly valid JSON as it
    # uses unquoted object keys (e.g. ``{x:1}``).  Quote any bare keys so that the
    # standard ``json`` module can parse it without pulling in an extra
    # dependency.
    normalized = re.sub(r"([,{]\s*)([a-zA-Z0-9_]+)(?=\s*:)", r'\1"\2"', json_content)
    data = json.loads(normalized)
    keys: List[Dict[str, Any]] = []

    # These track the current position for key rendering
    cursor_x = 0.0
    cursor_y = 0.0

    for row_index, row in enumerate(data):
        # Default properties for each key
        key_props = {
            "w": 1.0,
            "h": 1.0,
            "x": 0.0,
            "y": 0.0,
        }

        for item in row:
            if isinstance(item, dict):
                # This is a metadata object, it updates the properties for the next key(s)
                key_props.update(item)
            elif isinstance(item, str):
                # This is a key

                # Apply offsets from properties
                x = cursor_x + key_props.get("x", 0.0)
                y = cursor_y + key_props.get("y", 0.0)

                # Get key dimensions
                w = key_props.get("w", 1.0)
                h = key_props.get("h", 1.0)

                keys.append({
                    "row": row_index,
                    "col": int(x),
                    "shape": {"x": x, "y": y, "w": w, "h": h}
                })

                # Advance cursor
                cursor_x = x + w

                # Reset properties for the next key in the row
                key_props = {
                    "w": 1.0,
                    "h": 1.0,
                    "x": 0.0,
                    "y": 0.0, # y offset is per-key, not cumulative in a row
                }

        # After each row, move the y cursor down and reset x
        cursor_y += 1.0
        cursor_x = 0.0

    return keys
