#!/usr/bin/env python3
"""Fetch external inflection source files for deterministic imports."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_INDEX = ROOT / "data" / "index.json"
DEFAULT_OUT_DIR = ROOT / "data" / "sources" / "inflections" / "providers"
USER_AGENT = "WorldAlphabets/1.0 (https://github.com/willwade/WorldAlphabets)"

UNIMORPH_OVERRIDES = {
    # Regional and macrolanguage defaults where the repo name is not obvious
    # from the WorldAlphabets locale alone.
    "ar": "ara",
    "ca": "cat",
    "fr": "fra",
    "fr-CA": "fra",
    "no": "nob",
    "nb": "nob",
    "nn": "nno",
    "pt": "por",
    "pt-BR": "por",
    "zh": "zho",
}


@dataclass(frozen=True)
class LocaleCandidate:
    """A locale and possible UniMorph repository codes."""

    locale: str
    name: str | None
    candidates: list[str]


@dataclass(frozen=True)
class FetchResult:
    """Result of a single locale fetch attempt."""

    locale: str
    status: str
    code: str | None
    path: str | None
    error: str | None = None


def fetch_url(url: str) -> bytes:
    """Fetch bytes from a URL."""

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def read_json(path: Path) -> Any:
    """Read JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def unique(values: list[str]) -> list[str]:
    """Return values without duplicates, preserving order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def load_locale_candidates(locales: list[str] | None = None) -> list[LocaleCandidate]:
    """Load UniMorph candidate codes from WorldAlphabets index metadata."""

    wanted = set(locales) if locales else None
    index = read_json(DATA_INDEX)
    if not isinstance(index, list):
        raise ValueError(f"{DATA_INDEX} must contain a list")

    by_locale: dict[str, dict[str, Any]] = {}
    for entry in index:
        if not isinstance(entry, dict):
            continue
        locale = entry.get("language")
        if not isinstance(locale, str):
            continue
        if wanted is not None and locale not in wanted:
            continue
        by_locale.setdefault(locale, entry)

    if wanted is not None:
        for locale in wanted - set(by_locale):
            by_locale[locale] = {"language": locale, "name": None}

    candidates: list[LocaleCandidate] = []
    for locale, entry in sorted(by_locale.items()):
        base_locale = locale.split("-", 1)[0]
        possible = [
            UNIMORPH_OVERRIDES.get(locale, ""),
            UNIMORPH_OVERRIDES.get(base_locale, ""),
        ]
        iso3 = entry.get("iso639_3")
        iso1 = entry.get("iso639_1")
        if isinstance(iso3, str):
            possible.append(iso3.lower())
        if isinstance(iso1, str):
            possible.append(UNIMORPH_OVERRIDES.get(iso1.lower(), ""))
            possible.append(iso1.lower())
        possible.extend([base_locale.lower(), locale.lower()])
        candidates.append(
            LocaleCandidate(
                locale=locale,
                name=entry.get("name") if isinstance(entry.get("name"), str) else None,
                candidates=unique(possible),
            )
        )
    return candidates


def write_manifest(
    locale: str,
    code: str,
    url: str,
    out_path: Path,
    byte_count: int,
) -> None:
    """Write source metadata for a fetched provider file."""

    manifest_path = out_path.parent / "unimorph.source.json"
    manifest = {
        "source": "unimorph",
        "locale": locale,
        "code": code,
        "url": url,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "bytes": byte_count,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_unimorph_candidate(
    candidate: LocaleCandidate,
    out_dir: Path,
    skip_existing: bool,
) -> FetchResult:
    """Fetch the first available UniMorph table for a locale candidate."""

    locale_dir = out_dir / candidate.locale
    out_path = locale_dir / "unimorph.tsv"
    if skip_existing and out_path.exists():
        return FetchResult(
            locale=candidate.locale,
            status="skipped_existing",
            code=None,
            path=str(out_path),
        )

    errors: list[str] = []
    for code in candidate.candidates:
        url = f"https://raw.githubusercontent.com/unimorph/{code}/master/{code}"
        try:
            data = fetch_url(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                errors.append(f"{code}:404")
                continue
            errors.append(f"{code}:HTTP {exc.code}")
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{code}:{exc}")
            continue

        locale_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        write_manifest(candidate.locale, code, url, out_path, len(data))
        return FetchResult(
            locale=candidate.locale,
            status="fetched",
            code=code,
            path=str(out_path),
        )

    return FetchResult(
        locale=candidate.locale,
        status="not_found",
        code=None,
        path=None,
        error="; ".join(errors[:8]),
    )


def write_report(results: list[FetchResult], out_dir: Path) -> Path:
    """Write a JSON fetch report."""

    report_path = out_dir / "unimorph_fetch_report.json"
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
    payload = {
        "_type": "unimorph_fetch_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_counts": status_counts,
        "results": [result.__dict__ for result in results],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report_path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=["unimorph"],
        default="unimorph",
        help="Source provider to fetch",
    )
    parser.add_argument(
        "--locales",
        help="Comma-separated locales to fetch",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch UniMorph data for every locale in data/index.json",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--limit", type=int, help="Limit number of locales to attempt")
    return parser.parse_args()


def main() -> None:
    """Fetch requested source files."""

    args = parse_args()
    if not args.all and not args.locales:
        print("error: provide --locales or --all", file=sys.stderr)
        sys.exit(2)
    locales = (
        [locale.strip() for locale in args.locales.split(",") if locale.strip()]
        if args.locales
        else None
    )
    candidates = load_locale_candidates(locales)
    if args.limit is not None:
        candidates = candidates[: args.limit]

    results: list[FetchResult] = []
    for idx, candidate in enumerate(candidates, start=1):
        if args.source == "unimorph":
            result = fetch_unimorph_candidate(candidate, args.out_dir, args.skip_existing)
            results.append(result)
            detail = f" via {result.code}" if result.code else ""
            print(f"[{idx}/{len(candidates)}] {candidate.locale}: {result.status}{detail}")

    report_path = write_report(results, args.out_dir)
    print(f"Wrote fetch report to {report_path}")


if __name__ == "__main__":
    main()
