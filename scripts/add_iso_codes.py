#!/usr/bin/env python3
"""Add ISO 639 language codes and names to alphabet JSON files."""
from __future__ import annotations

import json
from pathlib import Path

import langcodes

ALPHABETS_DIR = Path("data/alphabets")


def main() -> None:
    for path in ALPHABETS_DIR.glob("*.json"):
        code = path.stem
        lang = langcodes.get(code)
        existing = json.loads(path.read_text(encoding="utf-8"))
        data = {
            "language": lang.language_name(),
            "iso639_3": lang.to_alpha3(),
        }
        alpha2 = lang.language
        if alpha2 and len(alpha2) == 2:
            data["iso639_1"] = alpha2
        data.update(existing)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Updated {path}")


if __name__ == "__main__":
    main()
