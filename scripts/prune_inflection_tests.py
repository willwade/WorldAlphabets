#!/usr/bin/env python3
"""Remove generated test suites whose no_rule ratio is too high."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFLECTION_DIR = ROOT / "data" / "inflections"


def no_rule_ratio(path: Path) -> tuple[float, int, int]:
    """Return no_rule ratio, no_rule count, and total rows."""

    if not path.exists():
        return 0.0, 0, 0
    total = 0
    no_rule = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            if (row.get("rule_id") or "").strip() == "no_rule":
                no_rule += 1
    return (no_rule / total if total else 0.0), no_rule, total


def clear_rules_tests(locale_dir: Path) -> None:
    """Clear rules.json tests array for one locale."""

    rules_path = locale_dir / "rules.json"
    if not rules_path.exists():
        return
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data["tests"] = []
        rules_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_INFLECTION_DIR)
    parser.add_argument("--locales", help="Comma-separated locales to force-prune")
    parser.add_argument("--max-no-rule-ratio", type=float, default=0.35)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Prune bad generated tests."""

    args = parse_args()
    force_locales = (
        {item.strip() for item in args.locales.split(",") if item.strip()}
        if args.locales
        else set()
    )
    for locale_dir in sorted(path for path in args.data_dir.iterdir() if path.is_dir()):
        tests_path = locale_dir / "tests.csv"
        ratio, no_rule, total = no_rule_ratio(tests_path)
        force = locale_dir.name in force_locales and tests_path.exists()
        if force or (total and ratio > args.max_no_rule_ratio):
            print(
                f"{locale_dir.name}: pruning {no_rule}/{total} no_rule "
                f"({ratio:.1%})" + (" forced" if force else "")
            )
            if not args.dry_run:
                tests_path.unlink()
                clear_rules_tests(locale_dir)


if __name__ == "__main__":
    main()
