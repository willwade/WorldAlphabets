#!/usr/bin/env python3
"""Generate tests from existing rules for all locales.

Each rule's lookback triggers + overrides/inflections define test cases
that are guaranteed to align with the rule engine.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"


def build_multi_step_combos(steps: List[Dict[str, Any]]) -> List[str]:
    """Build combined pre_text strings from multi-step lookback."""
    from itertools import product

    word_lists = [step["words"][:2] for step in steps]
    combos = []
    for combo in product(*word_lists):
        combos.append(" ".join(combo))
    return combos


def generate_tests_from_rules(locale: str) -> List[List[Any]]:
    rules_path = INFLECTION_DIR / locale / "rules.json"
    words_path = INFLECTION_DIR / locale / "words.json"

    rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
    words_data = json.loads(words_path.read_text(encoding="utf-8"))

    rule_list = rules_data.get("rules", [])
    tests: List[List[Any]] = []

    word_entries: Dict[str, Any] = {}
    for w, entry in words_data.items():
        if w.startswith("_") or not isinstance(entry, dict):
            continue
        word_entries[w] = entry

    override_words_by_trigger: Dict[str, set] = defaultdict(set)
    for r in rule_list:
        if not isinstance(r, dict):
            continue
        if isinstance(r.get("overrides"), dict):
            for lb in r.get("lookback", []):
                if isinstance(lb, dict) and "words" in lb:
                    for tw in lb["words"]:
                        override_words_by_trigger[tw].update(r["overrides"].keys())

    for rule in rule_list:
        if not isinstance(rule, dict):
            continue
        rid = rule.get("id", "")
        lookback = rule.get("lookback", [])
        overrides = rule.get("overrides", {})
        inflection = rule.get("inflection", "")

        mandatory_steps: List[Dict[str, Any]] = [
            lb for lb in lookback
            if isinstance(lb, dict) and "words" in lb and not lb.get("optional")
        ]

        if not mandatory_steps:
            continue

        single_step = len(mandatory_steps) == 1

        if overrides and isinstance(overrides, dict):
            if single_step:
                trigger_words = mandatory_steps[0]["words"]
                for input_word, output_word in overrides.items():
                    for trigger in trigger_words[:3]:
                        tests.append(
                            [
                                trigger,
                                input_word,
                                f"{trigger} {output_word}",
                                {"rule_id": rid},
                            ]
                        )
            else:
                combos = build_multi_step_combos(mandatory_steps)
                for pre_text in combos[:3]:
                    for input_word, output_word in overrides.items():
                        tests.append(
                            [
                                pre_text,
                                input_word,
                                f"{pre_text} {output_word}",
                                {"rule_id": rid},
                            ]
                        )

        elif inflection:
            rule_type = rule.get("type", "")
            trigger_words_list = mandatory_steps[0]["words"] if single_step else []
            override_words = set()
            for tw in trigger_words_list:
                override_words.update(override_words_by_trigger.get(tw, set()))
            if single_step:
                trigger_words = trigger_words_list
                for word, entry in list(word_entries.items())[:30]:
                    if word in override_words:
                        continue
                    word_types = entry.get("types", [])
                    if rule_type and isinstance(word_types, list):
                        if not word_types or word_types[0] != rule_type:
                            continue
                    infl = entry.get("inflections", {})
                    if not isinstance(infl, dict):
                        continue
                    forms = infl.get(inflection)
                    if forms and isinstance(forms, str):
                        for trigger in trigger_words[:2]:
                            tests.append(
                                [
                                    trigger,
                                    word,
                                    f"{trigger} {forms}",
                                    {"rule_id": rid, "inflection": inflection},
                                ]
                            )
            else:
                combos = build_multi_step_combos(mandatory_steps)
                for pre_text in combos[:3]:
                    for word, entry in list(word_entries.items())[:10]:
                        if word in override_words:
                            continue
                        word_types = entry.get("types", [])
                        if rule_type and isinstance(word_types, list):
                            if not word_types or word_types[0] != rule_type:
                                continue
                        infl = entry.get("inflections", {})
                        if not isinstance(infl, dict):
                            continue
                        forms = infl.get(inflection)
                        if forms and isinstance(forms, str):
                            tests.append(
                                [
                                    pre_text,
                                    word,
                                    f"{pre_text} {forms}",
                                    {"rule_id": rid, "inflection": inflection},
                                ]
                            )

    return tests


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locales",
        default=None,
        help="Comma-separated locales (default: all with rules)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print counts only"
    )
    args = parser.parse_args()

    if args.locales:
        locales = [loc.strip() for loc in args.locales.split(",")]
    else:
        locales = sorted(
            d.name
            for d in INFLECTION_DIR.iterdir()
            if d.is_dir()
            and (d / "rules.json").exists()
            and (d / "words.json").exists()
        )

    total_tests = 0
    total_locales = 0

    for locale in locales:
        rules_path = INFLECTION_DIR / locale / "rules.json"
        rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
        rule_count = len(rules_data.get("rules", []))

        if rule_count == 0:
            continue

        tests = generate_tests_from_rules(locale)
        if not tests:
            continue

        total_tests += len(tests)
        total_locales += 1

        if args.dry_run:
            print(f"  {locale}: {len(tests)} tests from {rule_count} rules")
            continue

        # Build CSV
        import csv
        import io

        csv_header = [
            "rule_id",
            "inflection",
            "pre_words",
            "test_word",
            "updated_words",
        ]
        out = io.StringIO()
        writer = csv.DictWriter(
            out, fieldnames=csv_header, lineterminator="\n"
        )
        writer.writeheader()
        for t in tests:
            checks = t[3] if len(t) > 3 and isinstance(t[3], dict) else {}
            writer.writerow(
                {
                    "rule_id": checks.get("rule_id", ""),
                    "inflection": checks.get("inflection", ""),
                    "pre_words": str(t[0] or ""),
                    "test_word": str(t[1] or ""),
                    "updated_words": str(t[2] or ""),
                }
            )

        csv_path = INFLECTION_DIR / locale / "tests.csv"
        csv_path.write_text(out.getvalue(), encoding="utf-8")

        # Sync into rules.json tests array
        from sync_inflection_tests import sync_locale

        sync_locale(csv_path.parent)

        rule_ids = {r["id"] for r in rules_data["rules"]}
        test_rids = set()
        for t in tests:
            if len(t) > 3 and isinstance(t[3], dict):
                test_rids.add(t[3].get("rule_id", ""))
        overlap = len(test_rids & rule_ids)

        print(
            f"  {locale}: {len(tests)} tests, "
            f"{overlap}/{len(rule_ids)} rules covered"
        )

    print(
        f"\nTotal: {total_tests} tests across {total_locales} locales"
    )


if __name__ == "__main__":
    main()
