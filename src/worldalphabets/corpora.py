"""Text corpora access.

Per-language natural-text corpora live in ``data/corpora/`` in the
WorldAlphabets repository (~400KB per language, ~74MB total). The text is
deliberately **not** packaged — wheels, sdists, npm tarballs and the C
library ship only the manifest (``SOURCES.json``) — so ``list_corpora()``
works everywhere while ``get_corpus()`` needs the actual files:

- from a repository checkout: ``get_corpus("hu", path="/path/to/WorldAlphabets/data/corpora")``
- via the ``WA_CORPORA_DIR`` environment variable
- vendored: copy the ``.txt`` files anywhere and pass ``path``

Every corpus carries a ``verify`` flag until its per-language source chain
has been confirmed licensing-clean (see SOURCES.json). Consumers must
respect it.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

__all__ = ["get_corpus", "list_corpora"]

_CORPUS_SIZE_HINT = "https://github.com/AACTools/WorldAlphabets#text-corpora"


@lru_cache(maxsize=1)
def _manifest() -> list[dict]:
    source = files("worldalphabets").joinpath("data", "corpora", "SOURCES.json")
    with source.open("r", encoding="utf-8") as fh:
        return [
            {
                "lang": meta.get("lang", name.removesuffix(".txt")),
                "mode": meta.get("mode"),
                "verify": bool(meta.get("verify")),
            }
            for name, meta in json.load(fh).items()
        ]


def list_corpora() -> list[dict]:
    """List available corpora (manifest only — no text shipped).

    Returns a list of ``{"lang", "mode", "verify"}`` dicts.
    """
    return [dict(entry) for entry in _manifest()]


def get_corpus(lang: str, path: str | None = None) -> str:
    """Return the natural-text corpus for ``lang`` (one sentence per line).

    Resolution order for the text file (deliberately not packaged — the
    full set is ~74MB): the ``path`` argument, the ``WA_CORPORA_DIR``
    environment variable, then the package data directory (present only in
    repo checkouts / vendored installs).
    """
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    env_dir = os.environ.get("WA_CORPORA_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(Path(str(files("worldalphabets").joinpath("data", "corpora"))))

    for directory in candidates:
        corpus_file = directory / f"{lang}.txt"
        if corpus_file.is_file():
            return corpus_file.read_text(encoding="utf-8")

    known = ", ".join(sorted(entry["lang"] for entry in _manifest())[:20])
    raise FileNotFoundError(
        f"Corpus text for '{lang}' not found in any of: "
        f"{', '.join(str(c) for c in candidates)}. "
        "Corpus text ships in the WorldAlphabets repository (data/corpora/) but is "
        "excluded from packages for size — pass path=, set WA_CORPORA_DIR, or vendor "
        f"the file. Available languages include: {known}… (see list_corpora()). {_CORPUS_SIZE_HINT}"
    )
