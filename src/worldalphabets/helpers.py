import json
from importlib.resources import files
from typing import Optional

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

    If ``script`` is not provided, the first script listed for the language in
    ``index.json`` is used.  When a script-specific alphabet file is not found,
    a legacy ``<lang>.json`` file is attempted as a fallback.
    """

    entry = next(
        (item for item in get_index_data() if item["language"] == lang_code),
        None,
    )
    if entry is None:
        return None

    scripts = entry.get("scripts") or []
    if script is None and scripts:
        script = scripts[0]

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
