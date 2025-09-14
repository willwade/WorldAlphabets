import json
from importlib.resources import files
from typing import List, Optional

INDEX_FILE = files("worldalphabets") / "data" / "index.json"
ALPHABET_DIR = files("worldalphabets") / "data" / "alphabets"

_index_data: Optional[list[dict]] = None


def get_index_data() -> list[dict]:
    """Load and cache ``index.json`` data."""

    global _index_data
    if _index_data is None:
        _index_data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return _index_data


def get_language(lang_code: str, script: Optional[str] = None) -> dict | None:
    """Return alphabet data for ``lang_code`` in ``script``.

    If ``script`` is not provided, the script from the index entry is used.
    When a script-specific alphabet file is not found, a legacy ``<lang>.json``
    file is attempted as a fallback.
    """

    entry = next(
        (item for item in get_index_data() if item["language"] == lang_code),
        None,
    )
    if entry is None:
        return None

    # Handle both old format (scripts array) and new format (single script)
    if script is None:
        # Try new format first (single script field)
        if "script" in entry:
            script = entry["script"]
        # Fall back to old format (scripts array)
        elif "scripts" in entry and entry["scripts"]:
            script = entry["scripts"][0]

    path = None
    if script:
        candidate = ALPHABET_DIR / f"{lang_code}-{script}.json"
        if candidate.is_file():
            path = candidate

    if path is None:
        candidate = ALPHABET_DIR / f"{lang_code}.json"
        if candidate.is_file():
            path = candidate

    if path is None:
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def get_scripts(lang_code: str) -> List[str]:
    """Return available script codes for ``lang_code``."""

    entry = next(
        (item for item in get_index_data() if item["language"] == lang_code),
        None,
    )
    if entry is None:
        return []
    scripts = entry.get("scripts")
    return scripts if scripts else []
