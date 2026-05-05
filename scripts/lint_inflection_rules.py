#!/usr/bin/env python3
"""Validate and fix inflection rules across all locales.

Checks every rule in every locale's rules.json for:
  1. lookback is an array of valid objects
  2. Rule has either 'overrides' dict or 'inflection'+'location' strings
  3. inflection key exists in the locale's words.json
  4. No extra disallowed fields (description, etc.)

Invalid rules are removed. Summary is printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"


def load_locale_words(locale: str) -> set[str]:
    path = INFLECTION_DIR / locale / "words.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for word, entry in data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        infl = entry.get("inflections", {})
        if isinstance(infl, dict):
            keys.update(k for k in infl if k != "regulars")
    return keys


def lint_rule(
    rule: Any,
    idx: int,
    valid_infl_keys: set[str],
) -> Tuple[List[str], bool]:
    errors: List[str] = []
    rid = rule.get("id", f"rule[{idx}]") if isinstance(rule, dict) else f"rule[{idx}]"

    if not isinstance(rule, dict):
        return [f"{rid}: not a dict, got {type(rule).__name__}"], False

    # check lookback
    lb = rule.get("lookback")
    if not isinstance(lb, list):
        errors.append(f"{rid}: lookback must be array, got {type(lb).__name__}")
        return errors, False
    if len(lb) == 0:
        errors.append(f"{rid}: lookback is empty array")
        return errors, False
    for j, item in enumerate(lb):
        if not isinstance(item, dict):
            errors.append(f"{rid}: lookback[{j}] must be dict")
        elif "words" not in item and not (
            item.get("optional") and item.get("type")
        ):
            errors.append(
                f"{rid}: lookback[{j}] needs 'words' or optional+type"
            )

    # check overrides or inflection+location
    has_overrides = isinstance(rule.get("overrides"), dict) and bool(
        rule["overrides"]
    )
    has_inflection = isinstance(rule.get("inflection"), str) and bool(
        rule["inflection"]
    )
    has_location = isinstance(rule.get("location"), str) and bool(
        rule["location"]
    )

    if not has_overrides and not (has_inflection and has_location):
        if has_inflection and not has_location:
            errors.append(f"{rid}: has inflection but missing location")
        elif has_location and not has_inflection:
            errors.append(f"{rid}: has location but missing inflection")
        else:
            errors.append(
                f"{rid}: needs 'overrides' dict or "
                "'inflection'+'location' strings"
            )
        return errors, False

    # check inflection key exists in words data
    if has_inflection and valid_infl_keys:
        infl = rule["inflection"]
        if infl not in valid_infl_keys:
            errors.append(
                f"{rid}: inflection '{infl}' not found in words.json"
            )
            return errors, False

    # strip disallowed fields
    for bad_key in ("description", "desc", "note", "example"):
        if bad_key in rule:
            del rule[bad_key]

    return errors, True


def lint_join_rule(rule: Any, idx: int) -> List[str]:
    errors: List[str] = []
    rid = rule.get("id", f"join[{idx}]") if isinstance(rule, dict) else f"join[{idx}]"
    if not isinstance(rule, dict):
        return [f"{rid}: not a dict, got {type(rule).__name__}"]
    if not isinstance(rule.get("prev"), (list, str)):
        errors.append(f"{rid}: prev must be string or array")
    if "next" not in rule and "next_match" not in rule:
        errors.append(f"{rid}: must have 'next' or 'next_match'")
    if not isinstance(rule.get("result", ""), str):
        errors.append(f"{rid}: result must be string")
    return errors


def lint_locale(locale: str, fix: bool = False) -> Dict[str, Any]:
    rules_path = INFLECTION_DIR / locale / "rules.json"
    if not rules_path.exists():
        return {"locale": locale, "error": "no rules.json"}

    data = json.loads(rules_path.read_text(encoding="utf-8"))
    rules_list = data.get("rules", [])
    valid_infl_keys = load_locale_words(locale)

    total = len(rules_list)
    valid_rules: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    all_errors: List[str] = []

    for i, rule in enumerate(rules_list):
        errors, is_valid = lint_rule(rule, i, valid_infl_keys)
        all_errors.extend(errors)
        if is_valid:
            rid = rule.get("id", "")
            if rid in seen_ids:
                all_errors.append(f"{rid}: duplicate rule id")
                continue
            seen_ids.add(rid)
            valid_rules.append(rule)

    removed = total - len(valid_rules)

    join_rules = data.get("join", [])
    join_errors: List[str] = []
    if isinstance(join_rules, list):
        for i, jr in enumerate(join_rules):
            join_errors.extend(lint_join_rule(jr, i))
    all_errors.extend(join_errors)

    if fix and removed > 0:
        data["rules"] = valid_rules
        rules_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {
        "locale": locale,
        "total": total,
        "valid": len(valid_rules),
        "removed": removed,
        "errors": all_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix", action="store_true", help="Remove invalid rules"
    )
    parser.add_argument(
        "--locales",
        default=None,
        help="Comma-separated locales (default: all with rules)",
    )
    args = parser.parse_args()

    if args.locales:
        locales = [loc.strip() for loc in args.locales.split(",")]
    else:
        locales = sorted(
            d.name
            for d in INFLECTION_DIR.iterdir()
            if d.is_dir() and (d / "rules.json").exists()
        )

    grand_total = 0
    grand_valid = 0
    grand_removed = 0
    problem_locales = []

    for locale in locales:
        result = lint_locale(locale, fix=args.fix)
        if "error" in result:
            continue
        total = result["total"]
        valid = result["valid"]
        removed = result["removed"]
        grand_total += total
        grand_valid += valid
        grand_removed += removed

        status = "OK" if removed == 0 else f"FIXED ({removed} removed)"
        print(f"  {locale:<8s} {valid:3d}/{total:3d} valid  {status}")

        if result["errors"]:
            problem_locales.append((locale, result["errors"]))

    print(f"\n{'='*50}")
    print(
        f"Total: {grand_valid}/{grand_total} valid "
        f"({grand_removed} removed)"
    )

    if problem_locales and not args.fix:
        print("\nRun with --fix to remove invalid rules")
    if problem_locales and args.fix:
        print("\nRemoved rules details:")
        for locale, errors in problem_locales:
            for e in errors:
                print(f"  {locale}: {e}")

    if grand_removed > 0 and not args.fix:
        sys.exit(1)


if __name__ == "__main__":
    main()
