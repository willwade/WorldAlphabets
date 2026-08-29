#!/usr/bin/env python3
"""Export Dasher training corpora from WorldAlphabets data.

Answers the DasherCore corpus gap (dasher-project/DasherCore#70 follow-ups):
148 shipped alphabets declare training files that don't exist, and 289 WA
alphabets declare none. This exporter generates licensing-traceable
training text for them from data already in this repo, into the format
DasherCore consumes (training_wa_<lang>_<Script>.txt, natural text, one
sentence per line).

WHY HERE: the corpora are generated from WorldAlphabets' own pipeline
outputs, under this repo's licensing control — nothing is taken from the
GPL-licensed upstream Dasher repo (that route is closed: GPL→MIT
relicensing needs author agreements we don't have).

Sources, in priority order:
  1. CommonVoice transcripts (CC-0)          — clean, ship freely
  2. Tatoeba sentences (CC-BY 2.0 FR)        — clean, attribute Tatoeba
  3. Freq lists (data/freq/top1000)          — derived pipeline output;
     the pipeline mixes Leipzig + HermitDave + CommonVoice + Tatoeba.
     Leipzig's own terms are research-use, so languages whose list may
     derive from Leipzig are emitted with "verify": true in SOURCES.json
     — review before shipping to DasherCore.

Output format:
  data/dasher/training_wa_<code>_<Script>.txt   — one sentence per line.
  NOTE: no comment headers inside the corpus files — Dasher's trainer
  streams every byte through the alphabet map, so provenance lives in
  SOURCES.json instead.
  data/dasher/SOURCES.json                       — per-language provenance
  + license note + verify flag.

Synthetic-text mode (default): the freq lists are ranked words without
counts, so words are sampled by Zipf rank (weight ~ 1/rank) and emitted
as short sentences. Character-level PPM (Dasher's LM) learns unigram/
bigram statistics from this; word-order nuance is lost, and the user's
own typing continues training adaptively.

Usage:
  python3 scripts/export_dasher_training.py --langs az,hi,gu
  python3 scripts/export_dasher_training.py --missing-from /path/to/DasherCore
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FREQ_DIR = REPO / "data" / "freq" / "top1000"
REGISTRY = REPO / "data" / "language_registry.json"
OUT_DIR = REPO / "data" / "dasher"

# Rough minimum Dasher guidance: "300K or more" of natural text.
TARGET_BYTES = 400_000
RANDOM_SEED = 1234


def load_registry():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_iso1 = {}
    for code, info in reg.items():
        iso1 = info.get("iso639_1") or ""
        if iso1:
            by_iso1[iso1] = code  # 639-1 -> 639-3
    return by_iso1


def load_scripts():
    # language_scripts.json: 639-3 -> ["Latn", ...] (curated; carries the
    # script info the raw registry lacks for most languages)
    return json.loads((REPO / "data" / "language_scripts.json").read_text(encoding="utf-8"))


def script_for(by_iso1, scripts_by_code, code):
    iso3 = by_iso1.get(code)
    if not iso3:
        return None
    for s in scripts_by_code.get(iso3, []):
        if len(s) == 4:
            return s
    return None


def load_freq_words(code):
    path = FREQ_DIR / f"{code}.txt"
    if not path.exists():
        return None
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        w = line.strip()
        if w and not w.startswith("Σ"):
            words.append(w)
    return words or None


def zipf_weights(n):
    # Ranked list, no counts: classic Zipf ~ 1/rank is a decent prior for
    # word frequencies in the source corpus.
    return [1.0 / (i + 1) for i in range(n)]


def synth_text(words, target_bytes, rng):
    weights = zipf_weights(len(words))
    lines = []
    total = 0
    while total < target_bytes:
        n_words = rng.randint(4, 12)
        sent = []
        for _ in range(n_words):
            # Zipf-weighted pick: common (low-rank) words dominate, matching
            # the frequency profile of the source corpus.
            idx = rng.choices(range(len(words)), weights=weights, k=1)[0]
            sent.append(words[idx])
        line = " ".join(sent)
        line = line[0].upper() + line[1:] + rng.choice([".", ".", ".", "?", "!"])
        lines.append(line)
        total += len(line.encode("utf-8")) + 1
    return "\n".join(lines) + "\n"


def provenance(code, script):
    # TODO(licensing): refine per-language source attribution once the freq
    # pipeline records it. Until then every freq-derived corpus is flagged
    # for review; CommonVoice (CC-0) / Tatoeba (CC-BY 2.0 FR) sentence
    # sources can be wired in as priority inputs later — both clean.
    return {
        "lang": code,
        "script": script,
        "generator": "WorldAlphabets export_dasher_training.py",
        "mode": "synthetic-from-freq-top1000",
        "pipeline": "Unified 6-Priority (Leipzig + HermitDave + CommonVoice + Tatoeba + Alphabet + Simia)",
        "generated": datetime.now(timezone.utc).isoformat(),
        "license_note": "Derived from WorldAlphabets freq pipeline output. Review source "
                        "attribution per language before redistribution: Tatoeba (CC-BY 2.0 FR) "
                        "and CommonVoice (CC-0) are clean; Leipzig-sourced lists are "
                        "research-use — verify or re-derive before shipping.",
        "verify": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", help="comma-separated ISO 639-1 codes")
    ap.add_argument("--missing-from", help="path to a DasherCore checkout; exports every missing-corpus language with freq data")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--target-bytes", type=int, default=TARGET_BYTES)
    args = ap.parse_args()

    if not args.langs and not args.missing_from:
        ap.error("need --langs or --missing-from")

    by_iso1 = load_registry()
    scripts_by_code = load_scripts()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    langs = []
    missing_alphabets = None  # [(lang, script), ...] when driven by --missing-from
    if args.langs:
        langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    else:
        index = Path(args.missing_from) / "Data" / "alphabets" / "alphabet_index.json"
        d = json.loads(index.read_text(encoding="utf-8"))
        import os
        have = set(os.listdir(Path(args.missing_from) / "Data" / "training"))
        missing_alphabets = []
        for a in d["alphabets"]:
            if not (a.get("training") and a["training"] not in have and a["training"] != ""):
                continue
            if not a.get("lang"):
                continue
            lang = a["lang"].split("-")[0]
            script = a.get("script")
            if lang and script:
                missing_alphabets.append((lang, script))

    sources_path = out / "SOURCES.json"
    sources = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}

    rng = random.Random(RANDOM_SEED)
    ok, skipped = [], []
    targets = missing_alphabets if missing_alphabets is not None else None

    if targets is not None:
        # --missing-from: one corpus per (lang, script) that a corpus-less
        # alphabet actually declares; never overwrite corpora DasherCore
        # already ships (real sentences beat synthetic text).
        seen = set()
        for code, script in sorted(set(targets)):
            name = f"training_wa_{code}_{script}.txt"
            if name in seen:
                continue
            seen.add(name)
            words = load_freq_words(code)
            if not words:
                skipped.append(code)
                continue
            if name in have or (out / name).exists():
                ok.append(name + " (kept existing)")
                continue
            text = synth_text(words, args.target_bytes, rng)
            (out / name).write_text(text, encoding="utf-8")
            sources[name] = provenance(code, script)
            ok.append(name)
    else:
        for code in langs:
            script = script_for(by_iso1, scripts_by_code, code)
            words = load_freq_words(code)
            if not script or not words:
                skipped.append(code)
                continue
            name = f"training_wa_{code}_{script}.txt"
            if (out / name).exists():
                ok.append(name + " (kept existing)")
                continue
            text = synth_text(words, args.target_bytes, rng)
            (out / name).write_text(text, encoding="utf-8")
            sources[name] = provenance(code, script)
            ok.append(name)

    sources_path.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"exported {len(ok)} corpora to {out}")
    for n in ok[:10]:
        print("  ", n)
    if len(ok) > 10:
        print(f"   ... and {len(ok) - 10} more")
    if skipped:
        print(f"skipped (no freq data or script): {' '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
