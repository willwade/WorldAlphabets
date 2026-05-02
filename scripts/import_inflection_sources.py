#!/usr/bin/env python3
"""Import deterministic inflection sources into published inflection data."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
DEFAULT_INFLECTION_DIR = DATA_DIR / "inflections"
DEFAULT_NORMALIZED_DIR = DATA_DIR / "sources" / "inflections" / "normalized_sources"
DEFAULT_PROVIDERS_DIR = DATA_DIR / "sources" / "inflections" / "providers"
VERSION = "0.1"


@dataclass(frozen=True)
class SourceForm:
    """One normalized provider form."""

    base: str
    form: str
    inflection: str
    part_of_speech: str
    source: str
    tags: list[str]


def clean_token(value: str) -> str:
    """Normalize whitespace around a token while preserving spelling."""

    return re.sub(r"\s+", " ", value.strip())


def normalize_tag(value: str) -> str:
    """Normalize a provider tag for use in an inflection key."""

    value = value.strip().lower()
    value = re.sub(r"[^0-9a-zA-Z]+", "_", value)
    return value.strip("_")


def normalize_inflection(tags: Iterable[str]) -> str:
    """Build a stable inflection key from provider tags."""

    normalized = [normalize_tag(tag) for tag in tags if normalize_tag(tag)]
    if not normalized:
        return "form"
    return "_".join(normalized)


def split_tags(value: str) -> list[str]:
    """Split semicolon/pipe/comma/space separated tags."""

    return [item for item in re.split(r"[;,|\s]+", value.strip()) if item]


def infer_part_of_speech(tags: Iterable[str], fallback: str = "word") -> str:
    """Infer a broad part of speech from provider tags."""

    upper_tags = {tag.upper() for tag in tags}
    if "V" in upper_tags or "VERB" in upper_tags:
        return "verb"
    if "N" in upper_tags or "NOUN" in upper_tags:
        return "noun"
    if "ADJ" in upper_tags or "ADJECTIVE" in upper_tags:
        return "adjective"
    if "ADV" in upper_tags or "ADVERB" in upper_tags:
        return "adverb"
    if "PRO" in upper_tags or "PRON" in upper_tags or "PRONOUN" in upper_tags:
        return "pronoun"
    return fallback or "word"


def priority_for_rank(rank: int, total: int) -> int:
    """Map a 1-based frequency rank to a 1-10 priority score."""

    if total <= 1:
        return 10
    score = 10 - int(((rank - 1) / total) * 10)
    return max(1, min(10, score))


def load_frequency_priorities(locale: str, limit: int | None) -> dict[str, int]:
    """Load token priorities from top-frequency data."""

    path = FREQ_DIR / f"{locale}.txt"
    if not path.exists() and "-" in locale:
        path = FREQ_DIR / f"{locale.split('-', 1)[0]}.txt"
    if not path.exists():
        return {}

    tokens: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not tokens and stripped.startswith("#"):
            continue
        tokens.append(stripped)
        if limit is not None and len(tokens) >= limit:
            break
    total = len(tokens)
    return {token: priority_for_rank(index, total) for index, token in enumerate(tokens, 1)}


def parse_unimorph(path: Path, source_name: str) -> list[SourceForm]:
    """Parse UniMorph-style TSV: lemma, form, features."""

    forms: list[SourceForm] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        base = clean_token(parts[0])
        form = clean_token(parts[1])
        tags = split_tags(parts[2])
        if not base or not form:
            continue
        forms.append(
            SourceForm(
                base=base,
                form=form,
                inflection=normalize_inflection(tags),
                part_of_speech=infer_part_of_speech(tags),
                source=source_name,
                tags=tags,
            )
        )
    return forms


def parse_hfst_tsv(path: Path, source_name: str) -> list[SourceForm]:
    """Parse normalized HFST TSV: base, form, tags, optional part_of_speech."""

    forms: list[SourceForm] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        base = clean_token(parts[0])
        form = clean_token(parts[1])
        tags = split_tags(parts[2])
        pos = clean_token(parts[3]).lower() if len(parts) > 3 else ""
        if not base or not form:
            continue
        forms.append(
            SourceForm(
                base=base,
                form=form,
                inflection=normalize_inflection(tags),
                part_of_speech=infer_part_of_speech(tags, fallback=pos),
                source=source_name,
                tags=tags,
            )
        )
    return forms


def parse_wiktextract(path: Path, source_name: str) -> list[SourceForm]:
    """Parse Wiktextract JSONL entries with forms arrays."""

    forms: list[SourceForm] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if not isinstance(entry, dict):
            continue
        base = clean_token(str(entry.get("word", "")))
        pos = clean_token(str(entry.get("pos", "word"))).lower() or "word"
        raw_forms = entry.get("forms", [])
        if not base or not isinstance(raw_forms, list):
            continue
        for raw_form in raw_forms:
            if not isinstance(raw_form, dict):
                continue
            form = clean_token(str(raw_form.get("form", "")))
            raw_tags = raw_form.get("tags", [])
            tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
            if not form or not tags or "canonical" in {tag.lower() for tag in tags}:
                continue
            forms.append(
                SourceForm(
                    base=base,
                    form=form,
                    inflection=normalize_inflection(tags),
                    part_of_speech=pos,
                    source=source_name,
                    tags=tags,
                )
            )
    return forms


def parse_normalized_jsonl(path: Path, source_name: str) -> list[SourceForm]:
    """Parse previously normalized SourceForm JSONL rows."""

    forms: list[SourceForm] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            continue
        base = clean_token(str(row.get("base", "")))
        form = clean_token(str(row.get("form", "")))
        tags = row.get("tags", [])
        tag_list = [str(tag) for tag in tags] if isinstance(tags, list) else []
        inflection = str(row.get("inflection") or normalize_inflection(tag_list))
        pos = str(row.get("part_of_speech") or infer_part_of_speech(tag_list))
        if not base or not form:
            continue
        forms.append(
            SourceForm(
                base=base,
                form=form,
                inflection=inflection,
                part_of_speech=pos,
                source=str(row.get("source") or source_name),
                tags=tag_list,
            )
        )
    return forms


def load_forms(path: Path, source_type: str, source_name: str) -> list[SourceForm]:
    """Load source forms for a supported provider type."""

    if source_type == "unimorph":
        return parse_unimorph(path, source_name)
    if source_type == "wiktextract":
        return parse_wiktextract(path, source_name)
    if source_type == "hfst-tsv":
        return parse_hfst_tsv(path, source_name)
    if source_type == "normalized-jsonl":
        return parse_normalized_jsonl(path, source_name)
    raise ValueError(f"Unsupported source type: {source_type}")


def source_form_to_json(form: SourceForm) -> dict[str, Any]:
    """Serialize a SourceForm."""

    return {
        "base": form.base,
        "form": form.form,
        "inflection": form.inflection,
        "part_of_speech": form.part_of_speech,
        "source": form.source,
        "tags": form.tags,
    }


def write_normalized(locale: str, source_name: str, forms: list[SourceForm]) -> Path:
    """Write normalized provider rows for review/reuse."""

    out_dir = DEFAULT_NORMALIZED_DIR / locale
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{source_name}.jsonl"
    out_path.write_text(
        "".join(
            json.dumps(source_form_to_json(form), ensure_ascii=False, sort_keys=True) + "\n"
            for form in forms
        ),
        encoding="utf-8",
    )
    return out_path


def load_words(data_dir: Path, locale: str) -> dict[str, Any]:
    """Load or initialize words.json."""

    path = data_dir / locale / "words.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    return {"_type": "words", "_locale": locale, "_version": VERSION}


def ensure_rules(data_dir: Path, locale: str) -> None:
    """Create a minimal rules.json if none exists."""

    path = data_dir / locale / "rules.json"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "_type": "rules",
        "_locale": locale,
        "_version": VERSION,
        "rules": [],
        "tests": [],
        "substitutions": {},
        "inflection_locations": {},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique_inflection_key(inflections: dict[str, Any], key: str, value: str) -> str:
    """Return a non-conflicting inflection key."""

    if key not in inflections or inflections.get(key) == value:
        return key
    index = 2
    while f"{key}_{index}" in inflections and inflections.get(f"{key}_{index}") != value:
        index += 1
    return f"{key}_{index}"


def ensure_word_entry(
    words: dict[str, Any],
    word: str,
    base: str,
    part_of_speech: str,
    priority: int | None,
) -> dict[str, Any]:
    """Create or update a word entry."""

    entry = words.get(word)
    if not isinstance(entry, dict):
        entry = {"types": [], "base": base, "inflections": {"regulars": []}}
        words[word] = entry
    types = entry.setdefault("types", [])
    if isinstance(types, list) and part_of_speech not in types:
        types.append(part_of_speech)
    entry.setdefault("base", base)
    entry.setdefault("inflections", {"regulars": []})
    if priority is not None:
        current = entry.get("priority")
        if not isinstance(current, int) or priority > current:
            entry["priority"] = priority
    return entry


def merge_forms(
    words: dict[str, Any],
    forms: Iterable[SourceForm],
    priorities: dict[str, int],
    include_surface_entries: bool,
) -> int:
    """Merge source forms into a words object. Return changed form count."""

    changed = 0
    for form in forms:
        priority = priorities.get(form.base) or priorities.get(form.form)
        base_entry = ensure_word_entry(
            words,
            form.base,
            form.base,
            form.part_of_speech,
            priority,
        )
        inflections = base_entry.setdefault("inflections", {"regulars": []})
        if not isinstance(inflections, dict):
            inflections = {"regulars": []}
            base_entry["inflections"] = inflections
        key = unique_inflection_key(inflections, form.inflection, form.form)
        if inflections.get(key) != form.form:
            inflections[key] = form.form
            changed += 1
        sources = base_entry.setdefault("_sources", [])
        if isinstance(sources, list) and form.source not in sources:
            sources.append(form.source)

        if include_surface_entries and form.form != form.base:
            surface_entry = ensure_word_entry(
                words,
                form.form,
                form.base,
                form.part_of_speech,
                priorities.get(form.form) or priority,
            )
            sources = surface_entry.setdefault("_sources", [])
            if isinstance(sources, list) and form.source not in sources:
                sources.append(form.source)
    return changed


def filter_forms(
    forms: list[SourceForm],
    priorities: dict[str, int],
    all_forms: bool,
) -> list[SourceForm]:
    """Filter forms to frequency-list tokens unless all_forms is true."""

    if all_forms or not priorities:
        return forms
    return [form for form in forms if form.base in priorities or form.form in priorities]


def provider_inputs(providers_dir: Path, source_type: str) -> list[tuple[str, Path]]:
    """Return locale/input paths for fetched provider files."""

    filename = {
        "unimorph": "unimorph.tsv",
        "hfst-tsv": "hfst.tsv",
        "wiktextract": "wiktextract.jsonl",
        "normalized-jsonl": "normalized.jsonl",
    }[source_type]
    results = []
    for locale_dir in sorted(path for path in providers_dir.iterdir() if path.is_dir()):
        input_path = locale_dir / filename
        if input_path.exists():
            results.append((locale_dir.name, input_path))
    return results


def save_words(data_dir: Path, locale: str, words: dict[str, Any]) -> None:
    """Write words.json."""

    path = data_dir / locale / "words.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(words, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale")
    parser.add_argument(
        "--all-fetched",
        action="store_true",
        help="Import every matching provider file under --providers-dir",
    )
    parser.add_argument(
        "--source-type",
        required=True,
        choices=["unimorph", "wiktextract", "hfst-tsv", "normalized-jsonl"],
    )
    parser.add_argument("--input", type=Path)
    parser.add_argument("--source-name", help="Source label stored in word entries")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_INFLECTION_DIR)
    parser.add_argument("--providers-dir", type=Path, default=DEFAULT_PROVIDERS_DIR)
    parser.add_argument("--limit-top", type=int, default=1000)
    parser.add_argument("--all-forms", action="store_true")
    parser.add_argument("--no-surface-entries", action="store_true")
    parser.add_argument("--write-normalized", action="store_true")
    parser.add_argument("--skip-without-frequency", action="store_true", default=True)
    parser.add_argument("--limit-locales", type=int)
    return parser.parse_args()


def import_one(args: argparse.Namespace, locale: str, input_path: Path) -> tuple[int, int, int]:
    """Import one locale/provider file and return total/filtered/changed counts."""

    source_name = args.source_name or args.source_type
    forms = load_forms(input_path, args.source_type, source_name)
    priorities = load_frequency_priorities(locale, args.limit_top)
    if args.skip_without_frequency and not priorities and not args.all_forms:
        print(f"Skipping {locale}: no frequency list and --all-forms not set")
        return len(forms), 0, 0
    if args.write_normalized:
        out_path = write_normalized(locale, source_name, forms)
        print(f"Wrote normalized rows to {out_path}")
    filtered = filter_forms(forms, priorities, all_forms=args.all_forms)
    words = load_words(args.data_dir, locale)
    changed = merge_forms(
        words,
        filtered,
        priorities,
        include_surface_entries=not args.no_surface_entries,
    )
    save_words(args.data_dir, locale, words)
    ensure_rules(args.data_dir, locale)
    print(
        f"Imported {len(filtered)} of {len(forms)} forms for {locale}; "
        f"changed {changed} inflection entries"
    )
    return len(forms), len(filtered), changed


def main() -> None:
    """Import source data."""

    args = parse_args()
    if args.all_fetched:
        inputs = provider_inputs(args.providers_dir, args.source_type)
        if args.limit_locales is not None:
            inputs = inputs[: args.limit_locales]
        totals = [import_one(args, locale, input_path) for locale, input_path in inputs]
        print(
            f"Imported {len(totals)} locale provider files; "
            f"changed {sum(item[2] for item in totals)} inflection entries"
        )
        return

    if not args.locale or args.input is None:
        raise SystemExit("--locale and --input are required unless --all-fetched is used")
    import_one(args, args.locale, args.input)


if __name__ == "__main__":
    main()
