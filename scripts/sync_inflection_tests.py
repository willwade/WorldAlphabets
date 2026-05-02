#!/usr/bin/env python3
"""Sync locale tests.csv files into rules.json tests arrays."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFLECTION_DIR = ROOT / "data" / "inflections"
TESTS_CSV_HEADER = ["rule_id", "inflection", "pre_words", "test_word", "updated_words"]


def tests_csv_to_array(path: Path) -> list[list[Any]]:
    """Convert tests.csv rows into rules.json tests arrays."""

    tests: list[list[Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != TESTS_CSV_HEADER:
            raise ValueError(f"{path} header must be {TESTS_CSV_HEADER}")
        for row in reader:
            pre_words = (row.get("pre_words") or "").strip()
            test_word = (row.get("test_word") or "").strip()
            updated_words = (row.get("updated_words") or "").strip()
            if not test_word or not updated_words:
                continue
            test: list[Any] = [pre_words, test_word, updated_words]
            checks: dict[str, str] = {}
            rule_id = (row.get("rule_id") or "").strip()
            inflection = (row.get("inflection") or "").strip()
            if rule_id:
                checks["rule_id"] = rule_id
            if inflection:
                checks["inflection"] = inflection
            if checks:
                test.append(checks)
            tests.append(test)
    return tests


def sync_locale(locale_dir: Path) -> bool:
    """Sync one locale's tests.csv into rules.json."""

    tests_path = locale_dir / "tests.csv"
    rules_path = locale_dir / "rules.json"
    if not tests_path.exists() or not rules_path.exists():
        return False
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    if not isinstance(rules, dict):
        raise ValueError(f"{rules_path} must contain a JSON object")
    rules["tests"] = tests_csv_to_array(tests_path)
    rules_path.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_INFLECTION_DIR)
    parser.add_argument("--locales", help="Comma-separated locale list; default all")
    return parser.parse_args()


def main() -> None:
    """Run sync."""

    args = parse_args()
    if args.locales:
        locale_dirs = [args.data_dir / item.strip() for item in args.locales.split(",") if item.strip()]
    else:
        locale_dirs = sorted(path for path in args.data_dir.iterdir() if path.is_dir())
    count = sum(1 for locale_dir in locale_dirs if sync_locale(locale_dir))
    print(f"Synced tests.csv into rules.json for {count} locales")


if __name__ == "__main__":
    main()
