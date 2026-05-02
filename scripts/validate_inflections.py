#!/usr/bin/env python3
"""Validate published inflection datasets and rebuild their index."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "inflections"
VERSION = "0.1"
CARDINAL_LOCATIONS = {"n", "ne", "e", "se", "s", "sw", "w", "nw", "c"}
TESTS_CSV_HEADER = ["rule_id", "inflection", "pre_words", "test_word", "updated_words"]


@dataclass
class ValidationResult:
    """Validation state for one run."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, path: Path, message: str) -> None:
        """Record an error."""

        self.errors.append(f"{path}: {message}")

    def warning(self, path: Path, message: str) -> None:
        """Record a warning."""

        self.warnings.append(f"{path}: {message}")


def read_json(path: Path, result: ValidationResult) -> Any | None:
    """Read JSON and report parse failures."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(path, f"invalid JSON: {exc}")
    except OSError as exc:
        result.error(path, f"cannot read file: {exc}")
    return None


def require_object(path: Path, data: Any, result: ValidationResult) -> dict[str, Any] | None:
    """Require a JSON object."""

    if not isinstance(data, dict):
        result.error(path, "must contain a JSON object")
        return None
    return data


def validate_metadata(
    path: Path,
    data: dict[str, Any],
    expected_type: str,
    locale: str,
    result: ValidationResult,
) -> None:
    """Validate common top-level metadata."""

    if data.get("_type") != expected_type:
        result.error(path, f"_type must be {expected_type!r}")
    if data.get("_locale") != locale:
        result.error(path, f"_locale must be {locale!r}")
    if data.get("_version") != VERSION:
        result.warning(path, f"_version should be {VERSION!r}")


def validate_word_entry(
    path: Path,
    word: str,
    entry: Any,
    result: ValidationResult,
) -> None:
    """Validate a single words.json word entry."""

    if not isinstance(entry, dict):
        result.error(path, f"word {word!r} must be an object")
        return

    types = entry.get("types")
    if not isinstance(types, list) or not all(isinstance(item, str) for item in types):
        result.error(path, f"word {word!r} must have string-array types")
    elif not types:
        result.error(path, f"word {word!r} must have at least one type")

    inflections = entry.get("inflections")
    if not isinstance(inflections, dict):
        result.error(path, f"word {word!r} must have object inflections")

    priority = entry.get("priority")
    if priority is not None:
        if not isinstance(priority, int) or priority < 1 or priority > 10:
            result.error(path, f"word {word!r} priority must be an integer 1-10")

    antonyms = entry.get("antonyms")
    if antonyms is not None:
        if not isinstance(antonyms, list):
            result.error(path, f"word {word!r} antonyms must be an array")

    examples = entry.get("examples")
    if examples is not None:
        if not isinstance(examples, list):
            result.error(path, f"word {word!r} examples must be an array")


def validate_words(path: Path, locale: str, result: ValidationResult) -> int:
    """Validate one words.json file and return its word count."""

    data = require_object(path, read_json(path, result), result)
    if data is None:
        return 0

    validate_metadata(path, data, "words", locale, result)
    count = 0
    for word, entry in data.items():
        if word.startswith("_"):
            continue
        validate_word_entry(path, word, entry, result)
        count += 1
    return count


def validate_lookback(
    path: Path,
    rule_id: str,
    item: Any,
    result: ValidationResult,
) -> None:
    """Validate a lookback item."""

    if not isinstance(item, dict):
        result.error(path, f"rule {rule_id!r} lookback items must be objects")
        return

    if "words" in item and not isinstance(item["words"], list):
        result.error(path, f"rule {rule_id!r} lookback words must be an array")
    if "type" in item and not isinstance(item["type"], str):
        result.error(path, f"rule {rule_id!r} lookback type must be a string")
    if "optional" in item and not isinstance(item["optional"], bool):
        result.error(path, f"rule {rule_id!r} optional must be boolean")
    if "condense" in item and not isinstance(item["condense"], bool):
        result.error(path, f"rule {rule_id!r} condense must be boolean")


def validate_rule(path: Path, rule: Any, result: ValidationResult) -> None:
    """Validate one rule entry."""

    if not isinstance(rule, dict):
        result.error(path, "rules entries must be objects")
        return

    rule_id = rule.get("id")
    if not isinstance(rule_id, str) or not rule_id:
        result.error(path, "each rule must have a non-empty string id")
        rule_id = "<unknown>"

    if not isinstance(rule.get("type"), str):
        result.error(path, f"rule {rule_id!r} must have a string type")

    if "overrides" in rule:
        if not isinstance(rule["overrides"], dict):
            result.error(path, f"rule {rule_id!r} overrides must be an object")
    elif not isinstance(rule.get("inflection"), str):
        result.error(path, f"rule {rule_id!r} needs inflection or overrides")

    location = rule.get("location")
    if location is not None and location not in CARDINAL_LOCATIONS:
        result.error(path, f"rule {rule_id!r} has invalid location {location!r}")

    lookback = rule.get("lookback", [])
    if not isinstance(lookback, list):
        result.error(path, f"rule {rule_id!r} lookback must be an array")
        return
    for item in lookback:
        validate_lookback(path, rule_id, item, result)


def validate_tests(path: Path, tests: Any, result: ValidationResult) -> None:
    """Validate rule tests."""

    if tests is None:
        return
    if not isinstance(tests, list):
        result.error(path, "tests must be an array")
        return
    for index, test in enumerate(tests):
        if not isinstance(test, list) or len(test) < 3:
            result.error(path, f"test {index} must be an array with at least 3 items")


def validate_inflection_locations(
    path: Path,
    locations: Any,
    result: ValidationResult,
) -> None:
    """Validate inflection_locations."""

    if locations is None:
        return
    if not isinstance(locations, dict):
        result.error(path, "inflection_locations must be an object")
        return
    for part, criteria in locations.items():
        if not isinstance(criteria, list):
            result.error(path, f"inflection_locations.{part} must be an array")
            continue
        for item in criteria:
            if not isinstance(item, dict):
                result.error(path, f"inflection_locations.{part} entries must be objects")
                continue
            location = item.get("location")
            if location is not None and location not in CARDINAL_LOCATIONS:
                result.error(path, f"invalid cardinal location {location!r}")


def validate_rules(path: Path, locale: str, result: ValidationResult) -> int:
    """Validate one rules.json file and return its rule count."""

    data = require_object(path, read_json(path, result), result)
    if data is None:
        return 0

    validate_metadata(path, data, "rules", locale, result)
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        result.error(path, "rules must be an array")
        return 0
    seen_ids: set[str] = set()
    for rule in rules:
        validate_rule(path, rule, result)
        if isinstance(rule, dict) and isinstance(rule.get("id"), str):
            rule_id = rule["id"]
            if rule_id in seen_ids:
                result.error(path, f"duplicate rule id {rule_id!r}")
            seen_ids.add(rule_id)

    validate_tests(path, data.get("tests"), result)
    validate_inflection_locations(path, data.get("inflection_locations"), result)
    return len(rules)


def validate_tests_csv(path: Path, result: ValidationResult) -> int:
    """Validate a tests.csv file and return row count."""

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != TESTS_CSV_HEADER:
                result.error(path, f"header must be {TESTS_CSV_HEADER}")
                return 0
            count = 0
            for index, row in enumerate(reader, start=2):
                if row.get("pre_words") is None or row.get("test_word") is None:
                    result.error(path, f"row {index} is missing required columns")
                    continue
                if not (row.get("test_word") or "").strip():
                    result.error(path, f"row {index} test_word must not be empty")
                if not (row.get("updated_words") or "").strip():
                    result.error(path, f"row {index} updated_words must not be empty")
                count += 1
            return count
    except OSError as exc:
        result.error(path, f"cannot read tests.csv: {exc}")
        return 0


def build_index(data_dir: Path, locale_stats: dict[str, dict[str, int]]) -> None:
    """Write data/inflections/index.json."""

    locales: dict[str, dict[str, Any]] = {}
    available = set(locale_stats)
    for locale in sorted(locale_stats):
        stats = locale_stats[locale]
        base_locale = None
        if "-" in locale:
            candidate = locale.split("-", 1)[0]
            if candidate in available:
                base_locale = candidate
        locales[locale] = {
            "words": f"{locale}/words.json",
            "rules": f"{locale}/rules.json",
            "tests": f"{locale}/tests.csv" if stats["test_count"] else None,
            "base_locale": base_locale,
            "priority_batch": None,
            "word_count": stats["word_count"],
            "rule_count": stats["rule_count"],
            "test_count": stats["test_count"],
        }

    index = {
        "_type": "inflection_index",
        "_version": VERSION,
        "locales": locales,
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_data_dir(data_dir: Path, write_index: bool) -> ValidationResult:
    """Validate all locale directories under data_dir."""

    result = ValidationResult()
    locale_stats: dict[str, dict[str, int]] = {}

    if not data_dir.exists():
        result.warning(data_dir, "directory does not exist")
        if write_index:
            build_index(data_dir, locale_stats)
        return result

    for locale_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        locale = locale_dir.name
        words_path = locale_dir / "words.json"
        rules_path = locale_dir / "rules.json"
        if not words_path.exists():
            result.error(words_path, "missing words.json")
            continue
        if not rules_path.exists():
            result.error(rules_path, "missing rules.json")
            continue
        word_count = validate_words(words_path, locale, result)
        rule_count = validate_rules(rules_path, locale, result)
        tests_path = locale_dir / "tests.csv"
        test_count = validate_tests_csv(tests_path, result) if tests_path.exists() else 0
        locale_stats[locale] = {
            "word_count": word_count,
            "rule_count": rule_count,
            "test_count": test_count,
        }

    if write_index:
        build_index(data_dir, locale_stats)
    return result


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Validate without rebuilding index.json",
    )
    return parser.parse_args()


def main() -> None:
    """Run validation."""

    args = parse_args()
    result = validate_data_dir(args.data_dir, write_index=not args.no_index)
    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")
    if result.errors:
        sys.exit(1)
    print(f"Inflection validation passed for {args.data_dir}")


if __name__ == "__main__":
    main()
