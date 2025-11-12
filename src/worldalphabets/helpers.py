import json
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import List, Optional

DATA_ROOT = files("worldalphabets") / "data"
INDEX_FILE = DATA_ROOT / "index.json"
ALPHABET_DIR = DATA_ROOT / "alphabets"

_index_data: Optional[list[dict]] = None


def _joinpath(base: Traversable, *parts: str) -> Traversable:
    """Join importlib Traversable segments in a Py3.8-compatible way."""
    for part in parts:
        base = base.joinpath(part)
    return base


def _load_json(candidate: Traversable) -> dict | None:
    """Load JSON from a Traversable if it exists."""
    try:
        content = candidate.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None
    return json.loads(content)


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

    candidates: list[Traversable] = []
    if script:
        candidates.append(
            _joinpath(DATA_ROOT, lang_code, "alphabet", f"{lang_code}-{script}.json")
        )
    candidates.append(
        _joinpath(DATA_ROOT, lang_code, "alphabet", f"{lang_code}.json")
    )
    if script:
        candidates.append(ALPHABET_DIR / f"{lang_code}-{script}.json")
    candidates.append(ALPHABET_DIR / f"{lang_code}.json")

    for candidate in candidates:
        data = _load_json(candidate)
        if data is not None:
            return data

    return None


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
