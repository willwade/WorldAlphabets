#!/usr/bin/env python3
"""Run inflection batch jobs using llm (provider-agnostic).

Supports any llm-backed model (Mistral Small, GPT-4o-mini, etc.)
and compares results across providers.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"
BATCH_DIR = ROOT / "data" / "sources" / "inflections" / "batches"
RESULTS_DIR = ROOT / "data" / "sources" / "inflections" / "llm_results"

DEFAULT_TESTS_MODEL = "mistral/mistral-small-latest"
DEFAULT_RULES_MODEL = "mistral/mistral-small-latest"


TESTS_SYSTEM_PROMPT = (
    "You generate inflection-rule test suites. "
    "Return only valid compact JSON. Do not include markdown. "
    "The output must be a JSON object with a tests array. "
    "Do not return CSV text."
)

RULES_SYSTEM_PROMPT = (
    "You generate executable inflection rules. "
    "Return only valid JSON. No markdown. No explanation. "
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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summarize_locale(locale: str, sample_size: int) -> Dict[str, Any]:
    words_data = _load_json(INFLECTION_DIR / locale / "words.json")
    sample_words = []
    for word, entry in words_data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        forms = entry.get("inflections", {})
        sample_words.append(
            {
                "word": word,
                "types": entry.get("types", []),
                "base": entry.get("base", word),
                "inflection_keys": (
                    list(forms.keys())[:8] if isinstance(forms, dict) else []
                ),
            }
        )
        if len(sample_words) >= sample_size:
            break

    return {"locale": locale, "sample_words": sample_words}


def _en_test_examples(limit: int) -> List[List[Any]]:
    path = INFLECTION_DIR / "en" / "tests.csv"
    if not path.exists():
        return []
    import csv

    rows: List[List[Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            test: List[Any] = [
                row.get("pre_words", ""),
                row.get("test_word", ""),
                row.get("updated_words", ""),
            ]
            checks: Dict[str, str] = {}
            if row.get("rule_id"):
                checks["rule_id"] = row["rule_id"]
            if row.get("inflection"):
                checks["inflection"] = row["inflection"]
            if checks:
                test.append(checks)
            rows.append(test)
            if len(rows) >= limit:
                break
    return rows


def build_tests_prompt(locale: str, row_count: int, sample_size: int) -> str:
    from collections import Counter

    rules_data = _load_json(INFLECTION_DIR / locale / "rules.json")
    rule_list = rules_data.get("rules", [])
    rule_ids = sorted(
        {
            r["id"]
            for r in rule_list
            if isinstance(r, dict) and "id" in r
        }
    )

    infl_by_type: Dict[str, set[str]] = {}
    for r in rule_list:
        if not isinstance(r, dict):
            continue
        infl = r.get("inflection", "")
        if infl:
            rtype = r.get("type", "unknown")
            infl_by_type.setdefault(rtype, set()).add(infl)

    infl_summary = {
        t: sorted(keys) for t, keys in infl_by_type.items()
    }

    payload = {
        "task": "Generate a comprehensive inflection test suite.",
        "locale": locale,
        "target_row_count": row_count,
        "locale_summary": _summarize_locale(locale, sample_size),
        "english_pattern_examples": _en_test_examples(80),
        "existing_rules": {
            "rule_ids": rule_ids,
            "inflections_by_type": infl_summary,
        },
        "requirements": [
            'Return JSON only: {"tests": [[pre_words, test_word, updated_words, checks], ...]}.',
            "Each test must be an array with 3 or 4 items.",
            "At least 70% of rows should expect an actual rule_id, not no_rule.",
            "Use words and inflection keys that exist in locale_summary.",
            "The updated_words value should be the expected full phrase.",
            "IMPORTANT: Use rule_id values from existing_rules.rule_ids where possible.",
            "Each rule_id should reference an actual rule that would produce the expected output.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_rules_prompt(locale: str, sample_size: int, max_rules: int) -> str:
    from collections import Counter, defaultdict

    words_data = _load_json(INFLECTION_DIR / locale / "words.json")
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
    inflection_counts: Dict[str, Counter] = defaultdict(Counter)
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
                inflection_counts[part][key] += 1
        if len(samples) < sample_size:
            samples.append(
                {
                    "word": word,
                    "types": type_list,
                    "inflection_keys": keys[:12],
                }
            )

    summary = {
        "locale": locale,
        "word_count": len(entries),
        "type_counts": dict(type_counts.most_common(20)),
        "inflection_keys_by_type": {
            part: dict(counter.most_common(20))
            for part, counter in inflection_counts.items()
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
                "lookback": (
                    "array of {words: [...]} or "
                    "{optional:true, type:'adverb'}"
                ),
                "overrides": (
                    "dict mapping input_word -> output_word"
                ),
            },
            "inflection_rule": {
                "id": "string",
                "type": "verb|noun|pronoun|adjective",
                "inflection": (
                    "key name from word_summary inflection_keys "
                    "(e.g. 'plural', 'past_participle')"
                ),
                "location": (
                    "'n' for noun/pronoun position, "
                    "'sw' for suffix/verb position"
                ),
                "lookback": (
                    "array of {words: [...]} or "
                    "{optional:true, type:'adverb'}"
                ),
            },
        },
        "working_examples_from_english": EXAMPLE_RULES,
        "requirements": [
            "lookback MUST be an array of objects.",
            "Each object has 'words' array or "
            "{optional:true, type:'adverb'}.",
            "EVERY rule MUST have either 'overrides' dict "
            "OR 'inflection'+'location' strings.",
            "Rules with only id+type+lookback are INVALID.",
            "Use inflection keys from "
            "word_summary.inflection_keys_by_type.",
            "Do NOT add 'description' fields.",
        ],
        "response_shape": {
            "rules": {
                "_type": "rules",
                "_locale": locale,
                "_version": "0.1",
                "rules": [],
                "tests": [],
                "substitutions": {},
                "inflection_locations": {},
            }
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_single(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    import llm

    model = llm.get_model(model_id)
    response = model.prompt(
        user_prompt,
        system=system_prompt,
    )
    text = response.text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import json_repair
            repaired = json_repair.loads(text)
            return repaired
        except Exception:
            return {"_raw": text, "_parse_error": True}


def normalize_tests(result: Dict[str, Any]) -> List[List[Any]]:
    raw_tests = result.get("tests", [])
    normalized = []
    for t in raw_tests:
        if not isinstance(t, list):
            continue
        if len(t) == 0:
            continue
        flat = []
        for item in t:
            if isinstance(item, list):
                for sub in item:
                    if isinstance(sub, str):
                        flat.append(sub)
                    elif isinstance(sub, dict):
                        flat.append(sub)
            else:
                flat.append(item)
        if len(flat) >= 3:
            if isinstance(flat[0], str) and isinstance(flat[1], str):
                expected = flat[2]
                if isinstance(expected, list):
                    expected = " ".join(str(x) for x in expected)
                if not isinstance(expected, str):
                    continue
                checks = flat[3] if len(flat) > 3 and isinstance(flat[3], dict) else {}
                if "rule_id" not in checks:
                    non_reg = [
                        k for k in checks if k != "regulars"
                    ]
                    if non_reg:
                        checks["rule_id"] = non_reg[0]
                normalized.append([flat[0], flat[1], expected, checks])
    return normalized


def run_tests_batch(
    locales: List[str],
    model_id: str,
    row_count: int = 150,
    sample_size: int = 80,
    delay: float = 0.5,
    dry_run: bool = False,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for locale in locales:
        print(f"\n=== Generating tests for {locale} via {model_id} ===")
        user_prompt = build_tests_prompt(locale, row_count, sample_size)

        if dry_run:
            print(f"  [DRY RUN] Would send prompt ({len(user_prompt)} chars)")
            continue

        t0 = time.time()
        result = run_single(model_id, TESTS_SYSTEM_PROMPT, user_prompt)
        elapsed = time.time() - t0

        if isinstance(result, list):
            result = {"tests": result}
        if not isinstance(result, dict):
            result = {"_raw": str(result), "_parse_error": True}

        if result.get("_parse_error"):
            print(f"  PARSE ERROR ({elapsed:.1f}s)")
        else:
            tests = normalize_tests(result)
            result["tests"] = tests
            print(f"  OK: {len(tests)} tests in {elapsed:.1f}s")

        out_path = RESULTS_DIR / f"tests_{locale}_{model_id.replace('/', '_')}.json"
        out_path.write_text(
            json.dumps(
                {
                    "locale": locale,
                    "model": model_id,
                    "elapsed_seconds": round(elapsed, 1),
                    "result": result,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        if delay > 0:
            time.sleep(delay)


def run_rules_batch(
    locales: List[str],
    model_id: str,
    sample_size: int = 40,
    max_rules: int = 8,
    delay: float = 0.5,
    dry_run: bool = False,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for locale in locales:
        print(f"\n=== Generating rules for {locale} via {model_id} ===")
        user_prompt = build_rules_prompt(locale, sample_size, max_rules)

        if dry_run:
            print(f"  [DRY RUN] Would send prompt ({len(user_prompt)} chars)")
            continue

        t0 = time.time()
        result = run_single(model_id, RULES_SYSTEM_PROMPT, user_prompt)
        elapsed = time.time() - t0

        out_path = RESULTS_DIR / f"rules_{locale}_{model_id.replace('/', '_')}.json"
        out_path.write_text(
            json.dumps(
                {
                    "locale": locale,
                    "model": model_id,
                    "elapsed_seconds": round(elapsed, 1),
                    "result": result,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        if isinstance(result, list):
            result = {"rules": result}
        if not isinstance(result, dict):
            result = {"_raw": str(result), "_parse_error": True}

        if result.get("_parse_error"):
            print(f"  PARSE ERROR ({elapsed:.1f}s)")
        else:
            rules_obj = result.get("rules", {})
            if isinstance(rules_obj, list):
                rules_list = rules_obj
            elif isinstance(rules_obj, dict):
                rules_list = rules_obj.get("rules", [])
            else:
                rules_list = []
            print(f"  OK: {len(rules_list)} rules in {elapsed:.1f}s")

        if delay > 0:
            time.sleep(delay)


def compare_results(locale: str, model_a: str, model_b: str) -> None:
    path_a = RESULTS_DIR / f"tests_{locale}_{model_a.replace('/', '_')}.json"
    path_b = RESULTS_DIR / f"tests_{locale}_{model_b.replace('/', '_')}.json"

    if not path_a.exists():
        print(f"No results for {locale} from {model_a}")
        return
    if not path_b.exists():
        print(f"No results for {locale} from {model_b}")
        return

    a = _load_json(path_a)
    b = _load_json(path_b)

    tests_a = a.get("result", {}).get("tests", [])
    tests_b = b.get("result", {}).get("tests", [])

    print(f"\n=== Comparison for {locale} ===")
    print(f"  {model_a}: {len(tests_a)} tests, {a.get('elapsed_seconds', '?')}s")
    print(f"  {model_b}: {len(tests_b)} tests, {b.get('elapsed_seconds', '?')}s")

    no_rule_a = sum(
        1
        for t in tests_a
        if isinstance(t, list) and len(t) > 3 and t[3].get("rule_id") == "no_rule"
    )
    no_rule_b = sum(
        1
        for t in tests_b
        if isinstance(t, list) and len(t) > 3 and t[3].get("rule_id") == "no_rule"
    )
    print(f"  no_rule ratio: {model_a}={no_rule_a}/{len(tests_a)}, {model_b}={no_rule_b}/{len(tests_b)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    tests_p = sub.add_parser("tests", help="Generate inflection tests")
    tests_p.add_argument("--locales", required=True, help="Comma-separated locales")
    tests_p.add_argument("--model", default=DEFAULT_TESTS_MODEL)
    tests_p.add_argument("--row-count", type=int, default=150)
    tests_p.add_argument("--sample-size", type=int, default=80)
    tests_p.add_argument("--delay", type=float, default=0.5)
    tests_p.add_argument("--dry-run", action="store_true")

    rules_p = sub.add_parser("rules", help="Generate inflection rules")
    rules_p.add_argument("--locales", required=True, help="Comma-separated locales")
    rules_p.add_argument("--model", default=DEFAULT_RULES_MODEL)
    rules_p.add_argument("--sample-size", type=int, default=40)
    rules_p.add_argument("--max-rules", type=int, default=8)
    rules_p.add_argument("--delay", type=float, default=0.5)
    rules_p.add_argument("--dry-run", action="store_true")

    cmp_p = sub.add_parser("compare", help="Compare results from two models")
    cmp_p.add_argument("--locale", required=True)
    cmp_p.add_argument("--model-a", default="gpt-4o-mini")
    cmp_p.add_argument("--model-b", default="mistral/mistral-small-latest")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "tests":
        locales = [loc.strip() for loc in args.locales.split(",")]
        run_tests_batch(
            locales,
            args.model,
            args.row_count,
            args.sample_size,
            args.delay,
            args.dry_run,
        )
    elif args.command == "rules":
        locales = [loc.strip() for loc in args.locales.split(",")]
        run_rules_batch(
            locales,
            args.model,
            sample_size=args.sample_size,
            max_rules=args.max_rules,
            delay=args.delay,
            dry_run=args.dry_run,
        )
    elif args.command == "compare":
        compare_results(args.locale, args.model_a, args.model_b)


if __name__ == "__main__":
    main()
