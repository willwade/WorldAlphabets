#!/usr/bin/env python3
"""Build per-language text corpora from REAL sentences (Tatoeba exports).

Produces `data/corpora/<lang>.txt` — natural sentences, one per line,
~400KB per language — plus `data/corpora/SOURCES.json` with per-corpus
provenance and licensing. Generic language asset, like data/freq and
data/audio: consumers format it however they need.

Sources, in priority order (per language, ISO 639-3 code):
  1. Tatoeba CC0 subset   (`<iso3>_sentences_CC0.tsv.bz2`)   — public domain
  2. Tatoeba base export  (`<iso3>_sentences.tsv.bz2`)       — CC-BY 2.0 FR,
     shipped with attribution (https://tatoeba.org)

Downloads are cached under .cache/tatoeba/ (gitignored). Languages with
no Tatoeba coverage are SKIPPED and reported — a missing corpus is honest;
a synthetic one is not. (A Zipf-synthesised fallback from the frequency
lists existed briefly and was removed: it produced word salad with
plausible character statistics, which is exactly the wrong trade for a
text-entry corpus. Do not reintroduce it for shipped data.)

Usage:
  python3 scripts/build_text_corpora.py                 # all languages with freq data
  python3 scripts/build_text_corpora.py --langs hu,da   # subset
  python3 scripts/build_text_corpora.py --list          # what's available
  python3 scripts/build_text_corpora.py --refresh       # re-download exports
"""

import argparse
import bz2
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

REPO = Path(__file__).resolve().parent.parent
FREQ_DIR = REPO / "data" / "freq" / "top1000"
REGISTRY = REPO / "data" / "language_registry.json"
OUT_DIR = REPO / "data" / "corpora"
CACHE = REPO / ".cache" / "tatoeba"

TARGET_BYTES = 400_000
BASE_URL = "https://downloads.tatoeba.org/exports/per_language/{iso3}/{iso3}_{kind}.tsv.bz2"
ATTRIBUTION = "https://tatoeba.org (sentences export)"


def available_languages() -> list[str]:
    return sorted(p.stem for p in FREQ_DIR.glob("*.txt"))


def iso3_map() -> dict[str, str]:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    m: dict[str, str] = {}
    for code, info in reg.items():
        iso1 = info.get("iso639_1") or ""
        if iso1:
            m[iso1] = code
        m.setdefault(code, code)  # already-639-3 codes pass through
    return m


def fetch_export(iso3: str, kind: str, refresh: bool) -> Path | None:
    """Download+cache a Tatoeba per-language export. Returns path or None (404)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / f"{iso3}_{kind}.tsv.bz2"
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        return dest
    url = BASE_URL.format(iso3=iso3, kind=kind)
    try:
        with urlopen(url, timeout=60) as resp:
            data = resp.read()
    except Exception:
        return None
    dest.write_bytes(data)
    return dest


def load_sentences(path: Path) -> list[str]:
    """Parse a sentences TSV: id<TAB>lang<TAB>text[<TAB>created]."""
    out: list[str] = []
    with bz2.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[2].strip():
                out.append(parts[2].strip())
    return out


def build_corpus(sentences: list[str], target_bytes: int) -> str:
    seen: set[str] = set()
    lines: list[str] = []
    total = 0
    for s in sentences:
        if s in seen:
            continue
        seen.add(s)
        lines.append(s)
        total += len(s.encode("utf-8")) + 1
        if total >= target_bytes:
            break
    return "\n".join(lines) + "\n"


def provenance(code: str, mode: str, n_sentences: int) -> dict:
    return {
        "lang": code,
        "generator": "build_text_corpora.py",
        "mode": mode,
        "source": "Tatoeba per-language exports",
        "attribution": ATTRIBUTION,
        "sentences_available": n_sentences,
        "generated": datetime.now(UTC).isoformat(),
        "license_note": (
            "Tatoeba sentences are CC-BY 2.0 FR (attribution: https://tatoeba.org); "
            "the CC0 subset is used where the language has substantive coverage. "
            "Retain this attribution when redistributing."
        )
        if mode.endswith("cc0")
        else (
            "Tatoeba sentences, CC-BY 2.0 FR — attribution required: "
            "https://tatoeba.org. Retain this attribution when redistributing."
        ),
        "verify": False,  # Tatoeba exports are licensing-clean with attribution
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--langs", help="comma-separated language codes (default: all with freq data)")
    ap.add_argument("--list", action="store_true", help="list available languages and exit")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--target-bytes", type=int, default=TARGET_BYTES)
    ap.add_argument("--refresh", action="store_true", help="re-download Tatoeba exports")
    ap.add_argument("--min-cc0", type=int, default=500,
                    help="use the CC0 subset when it has at least this many sentences")
    args = ap.parse_args()

    if args.list:
        print(" ".join(available_languages()))
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sources_path = out / "SOURCES.json"
    sources: dict = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}

    to3 = iso3_map()
    langs = [l.strip() for l in args.langs.split(",")] if args.langs else available_languages()

    ok: list[str] = []
    skipped: list[str] = []
    for code in langs:
        iso3 = to3.get(code)
        if not iso3:
            skipped.append(f"{code}(no-iso3)")
            continue
        # Prefer CC0 when substantive; fall back to the full CC-BY export.
        sentences: list[str] = []
        mode = None
        cc0 = fetch_export(iso3, "sentences_CC0", args.refresh)
        if cc0 is not None:
            s_cc0 = load_sentences(cc0)
            if len(s_cc0) >= args.min_cc0:
                sentences, mode = s_cc0, "tatoeba-sentences-cc0"
        if not sentences:
            base = fetch_export(iso3, "sentences", args.refresh)
            if base is None:
                skipped.append(f"{code}(no-tatoeba)")
                continue
            sentences = load_sentences(base)
            mode = "tatoeba-sentences"
        if not sentences:
            skipped.append(f"{code}(empty)")
            continue
        name = f"{code}.txt"
        (out / name).write_text(build_corpus(sentences, args.target_bytes), encoding="utf-8")
        sources[name] = provenance(code, mode, len(sentences))
        ok.append(code)

    sources_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Drop corpora for languages we no longer produce (previous synthetic set)
    current = {f"{c}.txt" for c in ok}
    for stale in set(sources) - current:
        (out / stale).unlink(missing_ok=True)
        del sources[stale]
    sources_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Browser/ESM manifest bundle (manifest only — text too large to embed).
    dist = REPO / "dist"
    dist.mkdir(exist_ok=True)
    manifest = [
        {"lang": sources[n]["lang"], "mode": sources[n]["mode"], "verify": sources[n]["verify"], "bytes": (out / n).stat().st_size}
        for n in sorted(sources)
    ]
    (dist / "browser-corpora.mjs").write_text(
        "// GENERATED by scripts/build_text_corpora.py — do not edit.\n"
        "// Manifest only (text corpora are too large to embed); see data/corpora/.\n"
        f"export const CORPORA_MANIFEST = {json.dumps(manifest, ensure_ascii=False, indent=1)};\n",
        encoding="utf-8",
    )

    print(f"built {len(ok)} corpora from real Tatoeba sentences ({len(sources)} in SOURCES.json)")
    if skipped:
        print(f"skipped (no Tatoeba coverage): {' '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
