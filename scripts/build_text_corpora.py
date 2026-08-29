#!/usr/bin/env python3
"""Build per-language text corpora from WorldAlphabets pipeline data.

Produces `data/corpora/<lang>.txt` — natural text, one sentence per line,
~400KB per language — plus `data/corpora/SOURCES.json` recording how each
corpus was produced and its licensing status. This is a generic language
asset (like data/freq, data/audio): consumers downstream (keyboard
prediction, language models, text-entry projects) format it however they
need; nothing consumer-specific lives here.

Today the builder runs in synthetic mode from the ranked word lists in
data/freq/top1000: words are Zipf-weighted by rank and sampled into short
sentences, which preserves the character- and word-shape statistics of the
source corpus. When sentence sources land (CommonVoice CC-0 transcripts
and Tatoeba CC-BY sentences are the priority inputs), they take
precedence and the synthetic mode becomes the fallback.

Licensing: every corpus carries `verify: true` in SOURCES.json until the
per-language source chain is confirmed clean (the freq pipeline mixes
Leipzig — research-use terms — with clean sources; Tatoeba and
CommonVoice are clean).

Usage:
  python3 scripts/build_text_corpora.py                 # all languages with freq data
  python3 scripts/build_text_corpora.py --langs az,hu   # subset
  python3 scripts/build_text_corpora.py --list          # what's available
"""

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FREQ_DIR = REPO / "data" / "freq" / "top1000"
OUT_DIR = REPO / "data" / "corpora"

TARGET_BYTES = 400_000
RANDOM_SEED = 1234
PIPELINE = "Unified 6-Priority (Leipzig + HermitDave + CommonVoice + Tatoeba + Alphabet + Simia)"


def available_languages() -> list[str]:
    return sorted(p.stem for p in FREQ_DIR.glob("*.txt"))


def load_freq_words(code: str) -> list[str] | None:
    path = FREQ_DIR / f"{code}.txt"
    if not path.exists():
        return None
    words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("Σ")]
    return words or None


def zipf_weights(n: int) -> list[float]:
    # Ranked list, no counts: classic Zipf ~ 1/rank is a decent prior for
    # word frequencies in the source corpus.
    return [1.0 / (i + 1) for i in range(n)]


def synth_text(words: list[str], target_bytes: int, rng: random.Random) -> str:
    weights = zipf_weights(len(words))
    lines: list[str] = []
    total = 0
    while total < target_bytes:
        n_words = rng.randint(4, 12)
        sent = [words[rng.choices(range(len(words)), weights=weights, k=1)[0]] for _ in range(n_words)]
        line = " ".join(sent)
        line = line[0].upper() + line[1:] + rng.choice([".", ".", ".", "?", "!"])
        lines.append(line)
        total += len(line.encode("utf-8")) + 1
    return "\n".join(lines) + "\n"


def provenance(code: str) -> dict:
    return {
        "lang": code,
        "generator": "build_text_corpora.py",
        "mode": "synthetic-from-freq-top1000",
        "pipeline": PIPELINE,
        "generated": datetime.now(UTC).isoformat(),
        "license_note": (
            "Derived from WorldAlphabets freq pipeline output. Review the source "
            "chain per language before redistribution: CommonVoice (CC-0) and "
            "Tatoeba (CC-BY 2.0 FR) are clean; Leipzig-sourced lists are "
            "research-use — verify or re-derive before shipping."
        ),
        "verify": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--langs", help="comma-separated language codes (default: all with freq data)")
    ap.add_argument("--list", action="store_true", help="list available languages and exit")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--target-bytes", type=int, default=TARGET_BYTES)
    args = ap.parse_args()

    if args.list:
        print(" ".join(available_languages()))
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sources_path = out / "SOURCES.json"
    sources: dict = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}

    langs = [l.strip() for l in args.langs.split(",")] if args.langs else available_languages()
    rng = random.Random(RANDOM_SEED)
    ok: list[str] = []
    skipped: list[str] = []
    for code in langs:
        words = load_freq_words(code)
        if words is None:
            skipped.append(code)
            continue
        name = f"{code}.txt"
        (out / name).write_text(synth_text(words, args.target_bytes, rng), encoding="utf-8")
        sources[name] = provenance(code)
        ok.append(code)

    sources_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"built {len(ok)} corpora in {out} ({len(sources)} in SOURCES.json)")
    if skipped:
        print(f"skipped (no freq data): {' '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
