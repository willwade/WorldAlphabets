#!/usr/bin/env python3
"""Quick test script to iterate on rules prompt for one locale."""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"

RULES_SYSTEM_PROMPT = (
    "You generate executable inflection rules. "
    "Return only valid JSON. No markdown. No explanation. "
    "The output must be exactly: "
    '{"rules": {"_type": "rules", "_locale": "LOCALE", '
    '"_version": "0.1", "rules": [...], "tests": [], '
    '"substitutions": {}, "inflection_locations": {}}}\n\n'
    "CRITICAL: Every rule MUST have either 'overrides' (dict) or "
    "'inflection' (string) + 'location' (string). "
    "Rules without these are INVALID."
)

EXAMPLE_RULES = [
    {
        "id": "i_am",
        "type": "override",
        "lookback": [{"words": ["I"]}, {"optional": True, "type": "adverb"}],
        "overrides": {"are": "am", "is": "am", "were": "was"},
    },
    {
        "id": "with_her",
        "type": "pronoun",
        "inflection": "objective",
        "location": "n",
        "lookback": [{"words": ["at", "for", "with"]}],
    },
    {
        "id": "these_dogs",
        "type": "noun",
        "inflection": "plural",
        "location": "n",
        "lookback": [{"words": ["those", "these", "some", "many"]}],
    },
    {
        "id": "has_she_looked",
        "type": "verb",
        "inflection": "past_participle",
        "location": "sw",
        "lookback": [
            {"words": ["has", "have", "had"]},
            {"words": ["you", "I", "he", "she", "it", "they"]},
        ],
    },
]


def build_prompt(locale: str, sample_size: int = 30, max_rules: int = 10):
    from collections import Counter, defaultdict

    words_data = json.loads(
        (INFLECTION_DIR / locale / "words.json").read_text(encoding="utf-8")
    )
    entries = []
    for word, entry in words_data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        entries.append((word, entry))

    entries.sort(
        key=lambda x: (
            -int(x[1].get("priority", 0))
            if isinstance(x[1].get("priority"), int)
            else 0,
            x[0],
        )
    )

    type_counts: Counter = Counter()
    infl_counts: dict[str, Counter] = defaultdict(Counter)
    samples = []
    for word, entry in entries:
        types = entry.get("types", [])
        type_list = types if isinstance(types, list) else ["word"]
        for part in type_list:
            type_counts[part] += 1
        forms = entry.get("inflections", {})
        keys = [k for k in forms if k != "regulars"] if isinstance(forms, dict) else []
        for part in type_list:
            for key in keys:
                infl_counts[part][key] += 1
        if len(samples) < sample_size:
            samples.append({"word": word, "types": type_list, "inflection_keys": keys[:12]})

    summary = {
        "locale": locale,
        "word_count": len(entries),
        "type_counts": dict(type_counts.most_common(20)),
        "inflection_keys_by_type": {
            part: dict(counter.most_common(20))
            for part, counter in infl_counts.items()
        },
        "sample_words": samples,
    }

    payload = {
        "task": (
            f"Generate at most {max_rules} executable inflection rules for "
            f"{locale}. Rules transform words based on preceding context."
        ),
        "locale": locale,
        "word_summary": summary,
        "schema": {
            "override_rule": {
                "id": "string",
                "type": "override",
                "lookback": "array of {words: [...]} or {optional:true, type:'adverb'}",
                "overrides": "dict mapping input_word -> output_word",
            },
            "inflection_rule": {
                "id": "string",
                "type": "verb|noun|pronoun|adjective",
                "inflection": "key name from word_summary inflection_keys (e.g. 'plural', 'past_participle')",
                "location": "'n' for noun/pronoun position, 'sw' for suffix/verb position",
                "lookback": "array of {words: [...]} or {optional:true, type:'adverb'}",
            },
        },
        "working_examples_from_english": EXAMPLE_RULES,
        "requirements": [
            "lookback MUST be an array of objects, each with 'words' array or {optional:true, type:'adverb'}.",
            "EVERY rule MUST have either 'overrides' dict OR 'inflection'+'location' strings.",
            "Rules with only id+type+lookback are INVALID.",
            "Use inflection keys that exist in word_summary.inflection_keys_by_type.",
            "Do NOT add 'description' fields.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def validate_rules(rules_list):
    errors = []
    valid = 0
    for i, r in enumerate(rules_list):
        if not isinstance(r, dict):
            errors.append(f"rule[{i}]: not a dict")
            continue
        rid = r.get("id", f"rule[{i}]")
        if not isinstance(r.get("lookback"), list):
            errors.append(f"{rid}: lookback must be array")
            continue
        has_overrides = isinstance(r.get("overrides"), dict) and r["overrides"]
        has_inflection = isinstance(r.get("inflection"), str) and r["inflection"]
        has_location = isinstance(r.get("location"), str) and r["location"]
        if not has_overrides and not (has_inflection and has_location):
            errors.append(f"{rid}: needs overrides dict OR inflection+location strings")
            continue
        if has_inflection and not has_location:
            errors.append(f"{rid}: has inflection but missing location")
            continue
        valid += 1
    return valid, errors


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--locale", default="de")
    parser.add_argument("--max-rules", type=int, default=10)
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--model", default="mistral/mistral-small-latest")
    args = parser.parse_args()

    prompt = build_prompt(args.locale, args.sample_size, args.max_rules)
    print(f"Model: {args.model}")
    print(f"Prompt size: {len(prompt)} chars")
    print(f"Generating rules for {args.locale}...")

    import llm

    model = llm.get_model(args.model)
    t0 = time.time()
    response = model.prompt(prompt, system=RULES_SYSTEM_PROMPT)
    text = response.text()
    elapsed = time.time() - t0
    print(f"Response in {elapsed:.1f}s ({len(text)} chars)")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        import json_repair
        parsed = json_repair.loads(text)
        print("(repaired JSON)")

    rules_obj = parsed.get("rules", parsed)
    rules_list = rules_obj.get("rules", [])

    print(f"\nGenerated {len(rules_list)} rules:")
    valid, errors = validate_rules(rules_list)
    for r in rules_list:
        if not isinstance(r, dict):
            print(f"  SKIP: {r}")
            continue
        rid = r.get("id", "?")
        rtype = r.get("type", "?")
        has_o = bool(r.get("overrides"))
        has_i = bool(r.get("inflection"))
        lb = len(r.get("lookback", []))
        status = "OK" if (has_o or has_i) else "INVALID"
        print(f"  [{status}] {rid} type={rtype} lookback={lb} overrides={has_o} inflection={has_i}")
        if has_i:
            print(f"         inflection={r.get('inflection')} location={r.get('location')}")
        if has_o:
            items = list(r["overrides"].items())[:3]
            print(f"         overrides={items}...")

    print(f"\nValid: {valid}/{len(rules_list)}")
    if errors:
        print("Errors:")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
