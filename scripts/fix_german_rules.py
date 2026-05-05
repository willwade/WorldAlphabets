#!/usr/bin/env python3
"""Fix German inflection rules to work with the first-match rule engine.

Problems fixed:
1. Override rules: Multiple rules with identical overrides + overlapping
   lookback triggers. Merged into single rules with combined lookbacks.
2. Verb rules: Multiple rules per pronoun trigger (present/past/imperative/
   subjunctive) - only first match fires. Keep present tense as default,
   remove unreachable duplicates.
3. Adjective rules: Same as override - merge duplicates with same outputs.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DE_RULES = ROOT / "data" / "inflections" / "de" / "rules.json"


def merge_override_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge override rules that produce identical output transformations."""
    override_rules = [r for r in rules if r.get("type") == "override"]
    other_rules = [r for r in rules if r.get("type") != "override"]

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in override_rules:
        key = json.dumps(r.get("overrides", {}), sort_keys=True)
        groups[key].append(r)

    merged = []
    for overrides_key, group in groups.items():
        combined_words: set[str] = set()
        representative = group[0]
        for r in group:
            for lb in r.get("lookback", []):
                if isinstance(lb, dict) and "words" in lb:
                    combined_words.update(lb["words"])

        merged_rule = dict(representative)
        merged_rule["lookback"] = [{"words": sorted(combined_words)}]
        merged_rule["id"] = min(r["id"] for r in group)
        merged.append(merged_rule)

    return other_rules + merged


def dedup_verb_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only one verb rule per unique lookback trigger.

    The engine only fires the first matching rule per type, so duplicates
    with the same trigger are unreachable. Keep present tense (prs) as
    the default since it's most common.
    """
    verb_rules = [r for r in rules if r.get("type") == "verb"]
    other_rules = [r for r in rules if r.get("type") != "verb"]

    by_trigger: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in verb_rules:
        trigger_words: list[str] = []
        for lb in r.get("lookback", []):
            if isinstance(lb, dict) and "words" in lb:
                trigger_words.extend(lb["words"])
        by_trigger[tuple(sorted(trigger_words))].append(r)

    kept = []
    for trigger, group in by_trigger.items():
        prs_rules = [
            r for r in group if "_prs_" in r.get("id", "") or "_prs" in r.get("inflection", "")
        ]
        if prs_rules:
            kept.append(prs_rules[0])
        else:
            kept.append(group[0])

    return other_rules + kept


def remove_adj_trigger_overlaps(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping trigger words from later adjective rules.

    The engine fires the first matching adjective rule per word, so later
    rules can never trigger on words already claimed by earlier rules.
    Remove those words to make rules explicit and tests correct.
    """
    adj_rules = [r for r in rules if r.get("type") == "adjective"]
    other_rules = [r for r in rules if r.get("type") != "adjective"]

    claimed: set[str] = set()
    result = []
    for r in adj_rules:
        new_words = []
        for lb in r.get("lookback", []):
            if isinstance(lb, dict) and "words" in lb:
                for w in lb["words"]:
                    if w not in claimed:
                        new_words.append(w)
        if new_words:
            new_rule = dict(r)
            new_rule["lookback"] = [{"words": sorted(new_words)}]
            result.append(new_rule)
            claimed.update(new_words)
        else:
            print(f"    DROPPED {r['id']} (all triggers claimed)")

    return other_rules + result


def main() -> None:
    data = json.loads(DE_RULES.read_text(encoding="utf-8"))
    original_count = len(data["rules"])
    print(f"Original: {original_count} rules")

    rules = data["rules"]

    print("\n--- Override rules (before) ---")
    for r in rules:
        if r.get("type") == "override":
            lb_words = [lb.get("words", []) for lb in r.get("lookback", []) if isinstance(lb, dict)]
            print(f"  {r['id']}: {lb_words} → {r.get('overrides', {})}")

    rules = merge_override_rules(rules)
    print(f"\n--- Override rules (after merge: {sum(1 for r in rules if r.get('type') == 'override')}) ---")
    for r in rules:
        if r.get("type") == "override":
            lb_words = [lb.get("words", []) for lb in r.get("lookback", []) if isinstance(lb, dict)]
            print(f"  {r['id']}: {lb_words} → {r.get('overrides', {})}")

    print(f"\n--- Verb rules (before: {sum(1 for r in rules if r.get('type') == 'verb')}) ---")
    verb_by_trigger: dict[tuple, list] = defaultdict(list)
    for r in rules:
        if r.get("type") == "verb":
            tw = tuple(sorted(w for lb in r.get("lookback", []) if isinstance(lb, dict) for w in lb.get("words", [])))
            verb_by_trigger[tw].append(r)
    for trigger, group in verb_by_trigger.items():
        print(f"  {trigger}: {[r['id'] for r in group]}")

    rules = dedup_verb_rules(rules)
    print(f"\n--- Verb rules (after dedup: {sum(1 for r in rules if r.get('type') == 'verb')}) ---")
    for r in rules:
        if r.get("type") == "verb":
            print(f"  {r['id']}: inflection={r.get('inflection', '?')}")

    print(f"\n--- Adjective rules (before: {sum(1 for r in rules if r.get('type') == 'adjective')}) ---")
    for r in rules:
        if r.get("type") == "adjective":
            lb_words = [lb.get("words", []) for lb in r.get("lookback", []) if isinstance(lb, dict)]
            print(f"  {r['id']}: {lb_words} → inflection={r.get('inflection', '?')}")

    rules = remove_adj_trigger_overlaps(rules)
    print(f"\n--- Adjective rules (after overlap removal: {sum(1 for r in rules if r.get('type') == 'adjective')}) ---")
    for r in rules:
        if r.get("type") == "adjective":
            lb_words = [lb.get("words", []) for lb in r.get("lookback", []) if isinstance(lb, dict)]
            print(f"  {r['id']}: {lb_words} → inflection={r.get('inflection', '?')}")

    data["rules"] = rules
    print(f"\nFinal: {len(rules)} rules (was {original_count})")

    DE_RULES.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written to {DE_RULES}")


if __name__ == "__main__":
    main()
