"""CLI entry point for building top-200 token lists."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import yaml

from .assemble import LangResult, file_sha256, merge_sources, write_tokens
from .normalize import normalize_token
from .sources import load_hermitdave, load_leipzig, load_stopwords, load_tatoeba
from .licenses import render_sources_md


DEFAULT_LANGMAP = Path(__file__).with_name("langmap.yaml")
DEFAULT_SETTINGS = Path(__file__).with_name("settings.yaml")


def load_yaml(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_language(
    lang: str, cfg: Dict, settings: Dict, freq_dir: Path, dry_run: bool
) -> LangResult:
    mode = cfg.get("type", "word")
    allowlists = settings.get("allowlist", {})
    limit = int(settings.get("max_tokens", 200))

    sources_data: List[tuple[str, List[str]]] = []
    shas: Dict[str, str] = {}
    for name in ["leipzig", "hermitdave", "tatoeba", "stopwords"]:
        path = cfg.get("sources", {}).get(name)
        if not path:
            continue
        p = Path(path)
        shas[name] = file_sha256(p)
        if name == "leipzig":
            raw = load_leipzig(p)
        elif name == "hermitdave":
            raw = load_hermitdave(p)
        elif name == "tatoeba":
            raw = load_tatoeba(p, mode)
        else:
            raw = load_stopwords(p)
        tokens = []
        for token in raw:
            norm = normalize_token(token, lang, allowlists)
            if norm:
                tokens.append(norm)
        sources_data.append((name, tokens))

    merged, counts = merge_sources(sources_data, limit)
    partial = len(merged) < limit
    if not dry_run:
        out_path = freq_dir / f"{lang}.txt"
        write_tokens(out_path, merged, mode)
    return LangResult(
        tokens=merged, source_counts=counts, mode=mode, partial=partial, sha256=shas
    )


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--langs", default="all")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--freq-dir", default="data/freq/top200")
    parser.add_argument("--langmap", default=str(DEFAULT_LANGMAP))
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS))
    parser.add_argument("--report", default=None)
    parser.add_argument("--update-sources-md", action="store_true")
    args = parser.parse_args(argv)

    langmap = load_yaml(Path(args.langmap))
    settings = load_yaml(Path(args.settings))

    if args.langs == "all":
        langs = list(langmap.keys())
    else:
        langs = [code.strip() for code in args.langs.split(",") if code.strip()]

    freq_dir = Path(args.freq_dir)
    report: Dict[str, Dict] = {}

    for lang in langs:
        cfg = langmap[lang]
        result = build_language(lang, cfg, settings, freq_dir, args.dry_run)
        report[lang] = {
            "name": cfg.get("name", lang),
            "token_count": len(result.tokens),
            "mode": result.mode,
            "source_counts": result.source_counts,
            "partial": result.partial,
            "sha256": result.sha256,
        }

    # Write reports
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    build_report = {"generated_at": generated_at, "languages": report}

    if args.report:
        report_path = Path(args.report)
        report_path.write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        freq_dir.mkdir(parents=True, exist_ok=True)
        (freq_dir / "BUILD_REPORT.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        sources_md = render_sources_md(report)
        (freq_dir / "SOURCES.md").write_text(sources_md, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
