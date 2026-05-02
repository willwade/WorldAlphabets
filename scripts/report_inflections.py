#!/usr/bin/env python3
"""Report inflection dataset coverage against frequency-list inputs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_INFLECTION_DIR = DATA_DIR / "inflections"
DEFAULT_MANIFEST = DATA_DIR / "sources" / "inflections" / "manifest.json"
FREQ_DIR = DATA_DIR / "freq" / "top1000"


def read_json(path: Path) -> Any:
    """Read JSON from a file."""

    return json.loads(path.read_text(encoding="utf-8"))


def word_count(path: Path) -> int:
    """Count non-metadata words in a words.json file."""

    data = read_json(path)
    if not isinstance(data, dict):
        return 0
    return sum(1 for key in data if not key.startswith("_"))


def csv_no_rule_count(path: Path) -> tuple[int, int]:
    """Return no_rule count and total rows for tests.csv."""

    if not path.exists():
        return 0, 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        no_rule = 0
        total = 0
        for row in csv.DictReader(handle):
            total += 1
            if (row.get("rule_id") or "").strip() == "no_rule":
                no_rule += 1
        return no_rule, total


def frequency_count(locale: str, limit: int) -> int:
    """Count available frequency tokens for a locale up to a limit."""

    path = FREQ_DIR / f"{locale}.txt"
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if count == 0 and stripped.startswith("#"):
            continue
        count += 1
        if count >= limit:
            break
    return count


def manifest_source_locales(manifest_path: Path) -> dict[str, str]:
    """Return locale -> source_locale from the generation manifest."""

    if not manifest_path.exists():
        return {}
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("targets"), list):
        return {}
    mapping: dict[str, str] = {}
    for target in manifest["targets"]:
        if not isinstance(target, dict):
            continue
        locale = target.get("locale")
        source_locale = target.get("source_locale")
        if isinstance(locale, str) and isinstance(source_locale, str):
            mapping[locale] = source_locale
    return mapping


def build_report(
    inflection_dir: Path,
    manifest_path: Path,
    expected_limit: int,
) -> list[dict[str, Any]]:
    """Build coverage rows for available locale outputs."""

    source_locales = manifest_source_locales(manifest_path)
    rows: list[dict[str, Any]] = []
    if not inflection_dir.exists():
        return rows
    for locale_dir in sorted(path for path in inflection_dir.iterdir() if path.is_dir()):
        locale = locale_dir.name
        words_path = locale_dir / "words.json"
        rules_path = locale_dir / "rules.json"
        words = word_count(words_path) if words_path.exists() else 0
        source_locale = source_locales.get(locale, locale.split("-", 1)[0])
        expected = frequency_count(source_locale, expected_limit)
        rules = 0
        tests = 0
        if rules_path.exists():
            rules_data = read_json(rules_path)
            if isinstance(rules_data, dict) and isinstance(rules_data.get("rules"), list):
                rules = len(rules_data["rules"])
            if isinstance(rules_data, dict) and isinstance(rules_data.get("tests"), list):
                tests = len(rules_data["tests"])
        no_rule_tests, csv_tests = csv_no_rule_count(locale_dir / "tests.csv")
        coverage = words / expected if expected else 0.0
        rows.append(
            {
                "locale": locale,
                "source_locale": source_locale,
                "words": words,
                "expected": expected,
                "coverage": coverage,
                "rules": rules,
                "tests": tests,
                "no_rule_tests": no_rule_tests,
                "csv_tests": csv_tests,
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_INFLECTION_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected-limit", type=int, default=100)
    parser.add_argument("--min-coverage", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Print coverage report."""

    args = parse_args()
    rows = build_report(args.data_dir, args.manifest, args.expected_limit)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print("locale\tsource\twords\texpected\tcoverage\trules\ttests\tno_rule")
        for row in rows:
            print(
                f"{row['locale']}\t{row['source_locale']}\t{row['words']}\t"
                f"{row['expected']}\t{row['coverage']:.1%}\t{row['rules']}\t"
                f"{row['tests']}\t{row['no_rule_tests']}/{row['csv_tests']}"
            )

    failed = [row for row in rows if row["coverage"] < args.min_coverage]
    if failed:
        print(
            f"error: {len(failed)} locales below {args.min_coverage:.0%} coverage",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
