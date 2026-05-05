#!/usr/bin/env python3
"""Fix inflection rules for any locale to work with the first-match rule engine.

Three transformations:
1. Merge override rules with identical output maps (combine triggers)
2. Dedup non-override rules per type+trigger (keep first match only)
3. Remove overlapping trigger words from later rules of the same type

Then regenerate tests and verify.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"


def get_trigger_words(rule: dict[str, Any]) -> list[str]:
    words: list[str] = []
    for lb in rule.get("lookback", []):
        if isinstance(lb, dict) and "words" in lb:
            words.extend(lb["words"])
    return words


def merge_override_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge override rules that share trigger words AND produce same output."""
    override_rules = [r for r in rules if r.get("type") == "override"]
    other_rules = [r for r in rules if r.get("type") != "override"]

    by_overrides: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in override_rules:
        key = json.dumps(r.get("overrides", {}), sort_keys=True)
        by_overrides[key].append(r)

    merged = []
    for overrides_key, group in by_overrides.items():
        if len(group) <= 1:
            merged.extend(group)
            continue

        tw_sets = [set(get_trigger_words(r)) for r in group]
        has_overlap = any(
            tw_sets[i] & tw_sets[j]
            for i in range(len(tw_sets))
            for j in range(i + 1, len(tw_sets))
        )
        if has_overlap:
            combined_words: set[str] = set()
            for r in group:
                combined_words.update(get_trigger_words(r))
            merged_rule = dict(group[0])
            merged_rule["lookback"] = [{"words": sorted(combined_words)}]
            merged_rule["id"] = min(r["id"] for r in group)
            merged.append(merged_rule)
        else:
            merged.extend(group)

    return other_rules + merged


def dedup_rules_by_trigger(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only one rule per (type, trigger) combination."""
    non_override = [r for r in rules if r.get("type") != "override"]
    override_rules = [r for r in rules if r.get("type") == "override"]

    by_key: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    for r in non_override:
        tw = tuple(sorted(get_trigger_words(r)))
        by_key[(r.get("type", ""), tw)].append(r)

    kept = []
    for key, group in by_key.items():
        prs_rules = [r for r in group if "_prs_" in r.get("id", "")]
        kept.append(prs_rules[0] if prs_rules else group[0])

    return override_rules + kept


def remove_trigger_overlaps(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping trigger words from later rules of the same type.

    The engine fires the first matching rule per type, so later rules
    can never trigger on words already claimed by earlier rules.
    """
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rules:
        by_type[r.get("type", "")].append(r)

    result_by_type: dict[str, list[dict[str, Any]]] = {}
    for rtype, type_rules in by_type.items():
        claimed: set[str] = set()
        kept = []
        for r in type_rules:
            new_words = [w for w in get_trigger_words(r) if w not in claimed]
            if new_words:
                new_rule = dict(r)
                new_rule["lookback"] = [{"words": sorted(new_words)}]
                kept.append(new_rule)
                claimed.update(new_words)
        result_by_type[rtype] = kept

    all_rules = []
    seen_ids: set[str] = set()
    for r in rules:
        rtype = r.get("type", "")
        fixed = next(
            (fr for fr in result_by_type.get(rtype, []) if fr.get("id") == r.get("id")),
            None,
        )
        rid = r.get("id", "")
        if fixed and rid not in seen_ids:
            all_rules.append(fixed)
            seen_ids.add(rid)

    return all_rules


def remove_dead_overrides(rules: list[dict[str, Any]], words_data: dict) -> list[dict[str, Any]]:
    """Remove override entries whose input words aren't in words.json
    or whose output is empty (engine can't express deletion)."""
    word_set = {w for w in words_data if not w.startswith("_")}
    cleaned = []
    for r in rules:
        if r.get("type") == "override" and isinstance(r.get("overrides"), dict):
            valid = {
                k: v
                for k, v in r["overrides"].items()
                if k in word_set and v
            }
            if valid:
                r = dict(r)
                r["overrides"] = valid
                cleaned.append(r)
        else:
            cleaned.append(r)
    return cleaned


def fix_override_types(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fix rules that have overrides dict but non-override type.

    Also lowercase all trigger words since the engine lowercases lookup.
    """
    fixed = []
    for r in rules:
        r = dict(r)
        if isinstance(r.get("overrides"), dict) and r.get("type") != "override":
            r["type"] = "override"
        new_lookback = []
        for lb in r.get("lookback", []):
            if isinstance(lb, dict) and "words" in lb:
                lb = dict(lb)
                lb["words"] = sorted(set(w.lower() for w in lb["words"]))
                new_lookback.append(lb)
            else:
                new_lookback.append(lb)
        r["lookback"] = new_lookback
        fixed.append(r)
    return fixed


def fix_multi_word_triggers(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split multi-word trigger entries into separate rules."""
    expanded = []
    for r in rules:
        multi_phrases: list[str] = []
        single_words: list[str] = []
        for lb in r.get("lookback", []):
            if isinstance(lb, dict) and "words" in lb:
                for w in lb["words"]:
                    if " " in w:
                        multi_phrases.append(w.strip())
                    else:
                        single_words.append(w)
        if not multi_phrases:
            expanded.append(r)
            continue

        if single_words:
            r = dict(r)
            r["lookback"] = [{"words": sorted(single_words)}]
            expanded.append(r)

        for phrase in multi_phrases:
            parts = phrase.split()
            if len(parts) == 2:
                new_rule = dict(r)
                new_rule["lookback"] = [
                    {"words": [parts[0]]},
                    {"words": [parts[1]]},
                ]
                if "id" in new_rule:
                    new_rule["id"] = f"{new_rule['id']}_{parts[0]}_{parts[1]}"
                expanded.append(new_rule)

    return expanded


def fix_locale(locale: str, *, dry_run: bool = False) -> tuple[int, int]:
    rules_path = INFLECTION_DIR / locale / "rules.json"
    words_path = INFLECTION_DIR / locale / "words.json"
    if not rules_path.exists() or not words_path.exists():
        return 0, 0

    data = json.loads(rules_path.read_text(encoding="utf-8"))
    words_data = json.loads(words_path.read_text(encoding="utf-8"))
    original = len(data.get("rules", []))
    if original == 0:
        return 0, 0

    rules = data["rules"]
    rules = merge_override_rules(rules)
    rules = fix_override_types(rules)
    rules = dedup_rules_by_trigger(rules)
    rules = remove_trigger_overlaps(rules)
    rules = remove_dead_overrides(rules, words_data)
    rules = fix_multi_word_triggers(rules)
    data["rules"] = rules

    if dry_run:
        return original, len(rules)

    rules_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return original, len(rules)


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

    total_before = 0
    total_after = 0
    for locale in locales:
        before, after = fix_locale(locale, dry_run=args.dry_run)
        if before > 0:
            total_before += before
            total_after += after
            print(f"  {locale}: {before} → {after} rules")

    print(f"\nTotal: {total_before} → {total_after} rules")


if __name__ == "__main__":
    main()
