#!/usr/bin/env python3
"""Split legacy alphabet files into language-script pairs.

This utility reads ``data/index.json`` and, for any language entry with more
than one script, copies the legacy ``<code>.json`` alphabet into
``<code>-<script>.json`` files.  Each generated file includes a ``script``
field.  Both the public ``data`` directory and the packaged
``src/worldalphabets/data`` directory are updated.

Run this after editing ``index.json`` to add ``scripts`` arrays.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIRS = [
    REPO_ROOT / "data" / "alphabets",
    REPO_ROOT / "src" / "worldalphabets" / "data" / "alphabets",
]
INDEX_PATH = REPO_ROOT / "data" / "index.json"


def _split_for_dir(alpha_dir: Path, index_data: List[Dict[str, Any]]) -> None:
    for entry in index_data:
        code = entry.get("language")
        scripts = entry.get("scripts")
        if not code or not scripts or len(scripts) <= 1:
            continue

        legacy_path = alpha_dir / f"{code}.json"
        if not legacy_path.exists():
            continue

        with legacy_path.open("r", encoding="utf-8") as f:
            alphabet = json.load(f)

        for script in scripts:
            target = alpha_dir / f"{code}-{script}.json"
            if target.exists():
                continue

            data = dict(alphabet)
            data["script"] = script

            with target.open("w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
                out.write("\n")
            print(f"Wrote {target.relative_to(REPO_ROOT)}")

        legacy_path.unlink()
        print(f"Removed {legacy_path.relative_to(REPO_ROOT)}")


def main() -> None:  # pragma: no cover - script
    with INDEX_PATH.open("r", encoding="utf-8") as f:
        index: List[Dict[str, Any]] = json.load(f)

    for alpha_dir in DATA_DIRS:
        _split_for_dir(alpha_dir, index)


if __name__ == "__main__":  # pragma: no cover - script
    main()
