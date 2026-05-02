#!/usr/bin/env python3
"""Import demo-tools flat inflection assets into WorldAlphabets layout."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = Path("/Users/willwade/GitHub/demo-tools/public/inflections")
DEFAULT_OUT_DIR = ROOT / "data" / "inflections"


def import_locale(source_dir: Path, out_dir: Path, locale: str) -> None:
    """Import words/rules/tests files for one locale when present."""

    locale_dir = out_dir / locale
    locale_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        source_dir / f"words-{locale}.json": locale_dir / "words.json",
        source_dir / f"rules-{locale}.json": locale_dir / "rules.json",
        source_dir / f"tests-{locale}.csv": locale_dir / "tests.csv",
    }
    copied = 0
    for source, target in mapping.items():
        if source.exists():
            shutil.copy2(source, target)
            if target.suffix == ".json":
                data = json.loads(target.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data["_locale"] = locale
                    target.write_text(
                        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
            copied += 1
    print(f"Imported {copied} files for {locale}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--locales",
        default="en,es",
        help="Comma-separated locale list to import",
    )
    return parser.parse_args()


def main() -> None:
    """Run import."""

    args = parse_args()
    locales = [locale.strip() for locale in args.locales.split(",") if locale.strip()]
    for locale in locales:
        import_locale(args.source_dir, args.out_dir, locale)


if __name__ == "__main__":
    main()
