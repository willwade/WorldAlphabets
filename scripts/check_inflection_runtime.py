#!/usr/bin/env python3
"""Run inflection rule tests using demo-tools-compatible lookup semantics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFLECTION_DIR = ROOT / "data" / "inflections"


@dataclass
class CheckFailure:
    """One failed runtime test."""

    locale: str
    index: int
    message: str


def read_json(path: Path) -> Any:
    """Read JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_locale(data_dir: Path, locale: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[list[Any]]]:
    """Load words, rules, and tests for a locale."""

    words_data = read_json(data_dir / locale / "words.json")
    rules_data = read_json(data_dir / locale / "rules.json")
    if not isinstance(words_data, dict) or not isinstance(rules_data, dict):
        raise ValueError(f"{locale}: words and rules must be objects")
    words = []
    for word, entry in words_data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        item = dict(entry)
        item["word"] = word
        words.append(item)
    rules = rules_data.get("rules", [])
    tests = rules_data.get("tests", [])
    if not isinstance(rules, list) or not isinstance(tests, list):
        raise ValueError(f"{locale}: rules/tests must be arrays")
    return words, rules, tests


def item_matches(check: dict[str, Any], item: dict[str, Any]) -> bool:
    """Return True if a prior word item matches one lookback check."""

    label = str(item.get("word", "")).lower()
    if isinstance(check.get("words"), list):
        matching = label in check["words"]
    elif isinstance(check.get("type"), str):
        types = item.get("types", [])
        matching = isinstance(types, list) and check["type"] in types
    else:
        matching = True

    if matching and isinstance(check.get("match"), str):
        matching = re.search(check["match"], label) is not None
    if matching and isinstance(check.get("non_match"), str):
        matching = re.search(check["non_match"], label) is None
    return matching


def matches_rule(rule: dict[str, Any], buttons: list[dict[str, Any]]) -> bool | dict[str, Any]:
    """Mirror demo-tools rules.js matches_rule behavior."""

    lookback = rule.get("lookback", [])
    if not isinstance(lookback, list):
        return False

    history_idx = len(buttons) - 1
    valid = True
    condenses: list[int] = []
    for idx in range(len(lookback) - 1, -1, -1):
        check = lookback[idx]
        pre_check = lookback[idx - 1] if idx > 0 else None
        if not isinstance(check, dict):
            return False
        item = buttons[history_idx] if history_idx >= 0 else None
        if item is None:
            if not check.get("optional"):
                valid = False
        else:
            matching = item_matches(check, item)
            pre_matching = isinstance(pre_check, dict) and item_matches(pre_check, item)
            pre_optional = pre_check.get("optional") if isinstance(pre_check, dict) else None
            if matching and check.get("optional") and pre_matching and not pre_optional:
                matching = False
            if matching:
                if check.get("condense"):
                    condenses.append(history_idx)
                history_idx -= 1
            elif not check.get("optional"):
                valid = False
        if not valid:
            break
    if valid and condenses:
        return {"condense_items": condenses}
    return bool(valid)


def lookup(
    words: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    lookup_word: str,
    prior_words: str,
) -> dict[str, Any]:
    """Mirror the relevant demo-tools lookup behavior."""

    parts = prior_words.split()
    prior_buttons = []
    for part in parts:
        found = next((word for word in words if word.get("word") == part), None)
        prior_buttons.append(found or {"word": part})

    found_words = [word for word in words if word.get("word") == lookup_word]
    found_types: dict[str, bool] = {}
    matching_rules: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_type = rule.get("type")
        if not isinstance(rule_type, str):
            continue
        if found_types.get(rule_type) and rule_type != "override":
            continue
        matches = matches_rule(rule, prior_buttons)
        if matches:
            matched_rule = dict(rule)
            if isinstance(matches, dict):
                matched_rule.update(matches)
            matching_rules.append(matched_rule)
            found_types[rule_type] = True

    result_words = []
    for found_word in found_words:
        result_word = dict(found_word)
        inflections: dict[str, Any] = {}
        for rule in matching_rules:
            if rule.get("type") == "override" and isinstance(rule.get("overrides"), dict):
                for key, value in rule["overrides"].items():
                    inflections.setdefault(
                        key,
                        {
                            "type": "override",
                            "word": value,
                            "id": rule.get("id"),
                            "condense_items": rule.get("condense_items"),
                        },
                    )
            else:
                rule_type = rule.get("type")
                if isinstance(rule_type, str):
                    inflections[rule_type] = rule

        replacement = None
        found_word_value = found_word.get("word")
        direct = inflections.get(found_word_value) if isinstance(found_word_value, str) else None
        if isinstance(direct, dict) and direct.get("word"):
            replacement = direct["word"]
            result_word["replacement"] = replacement
            result_word["condense_items"] = direct.get("condense_items")
            result_word["rule_id"] = direct.get("id")
        else:
            replacement_rule = None
            types = found_word.get("types", [])
            if isinstance(types, list):
                for part in types:
                    if part in inflections:
                        replacement_rule = replacement_rule or inflections[part]
            if isinstance(replacement_rule, dict):
                forms = found_word.get("inflections", {})
                inflection = replacement_rule.get("inflection")
                if isinstance(forms, dict) and isinstance(inflection, str):
                    replacement = forms.get(inflection) or found_word.get("word")
                else:
                    replacement = found_word.get("word")
                result_word["replacement"] = replacement
                result_word["rule_type"] = inflection
                result_word["condense_items"] = replacement_rule.get("condense_items")
                result_word["rule_id"] = replacement_rule.get("id")
        result_words.append(result_word)
    return {"words": result_words, "rules": matching_rules}


def result_string(pre_text: str, word_result: dict[str, Any]) -> str:
    """Build the expected output phrase from a lookup word result."""

    replacement = str(word_result.get("replacement") or word_result.get("word") or "")
    condense_items = word_result.get("condense_items")
    if isinstance(condense_items, list):
        prior = pre_text.split()
        prior = [word for index, word in enumerate(prior) if index not in condense_items]
        return (" ".join(prior + [replacement])).strip()
    return (pre_text + " " + replacement).strip()


def check_locale(data_dir: Path, locale: str) -> list[CheckFailure]:
    """Run runtime tests for a locale."""

    words, rules, tests = load_locale(data_dir, locale)
    failures: list[CheckFailure] = []
    for index, test in enumerate(tests):
        if not isinstance(test, list) or len(test) < 3:
            failures.append(CheckFailure(locale, index, "test must be an array of at least 3 items"))
            continue
        pre_text = str(test[0])
        test_word = str(test[1])
        expected = str(test[2])
        checks = test[3] if len(test) > 3 and isinstance(test[3], dict) else {}
        result = lookup(words, rules, test_word, pre_text)
        if not result["words"]:
            failures.append(CheckFailure(locale, index, f"word not found: {test_word}"))
            continue
        first = result["words"][0]
        actual = result_string(pre_text, first)
        if actual != expected:
            failures.append(
                CheckFailure(locale, index, f"expected {expected!r}, got {actual!r}")
            )
        expected_rule = checks.get("rule_id")
        if expected_rule and expected_rule != (first.get("rule_id") or "no_rule"):
            failures.append(
                CheckFailure(
                    locale,
                    index,
                    f"expected rule {expected_rule!r}, got {first.get('rule_id') or 'no_rule'!r}",
                )
            )
        expected_inflection = checks.get("inflection")
        if expected_inflection and expected_inflection != first.get("rule_type"):
            failures.append(
                CheckFailure(
                    locale,
                    index,
                    f"expected inflection {expected_inflection!r}, got {first.get('rule_type')!r}",
                )
            )
    return failures


def available_test_locales(data_dir: Path) -> list[str]:
    """Return locales whose rules.json contains tests."""

    locales = []
    for locale_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        rules_path = locale_dir / "rules.json"
        if not rules_path.exists():
            continue
        rules = read_json(rules_path)
        if isinstance(rules, dict) and isinstance(rules.get("tests"), list) and rules["tests"]:
            locales.append(locale_dir.name)
    return locales


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_INFLECTION_DIR)
    parser.add_argument("--locales", help="Comma-separated locales; default all with tests")
    parser.add_argument("--allow-failures", action="store_true")
    parser.add_argument("--limit", type=int, default=20, help="Failure display limit")
    return parser.parse_args()


def main() -> None:
    """Run runtime checks."""

    args = parse_args()
    locales = (
        [item.strip() for item in args.locales.split(",") if item.strip()]
        if args.locales
        else available_test_locales(args.data_dir)
    )
    failures: list[CheckFailure] = []
    for locale in locales:
        locale_failures = check_locale(args.data_dir, locale)
        print(f"{locale}: {len(locale_failures)} failures")
        failures.extend(locale_failures)

    for failure in failures[: args.limit]:
        print(f"{failure.locale} test {failure.index}: {failure.message}")
    if len(failures) > args.limit:
        print(f"... {len(failures) - args.limit} more failures")
    if failures and not args.allow_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
