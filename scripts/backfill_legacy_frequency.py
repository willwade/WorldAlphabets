from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import langcodes


LEGACY_FREQ_DIR = Path("dontcommit/originaldata/freq/top1000")
DATA_ROOT = Path("data")
TOP_LEVEL_FREQ_TARGETS: tuple[Path, ...] = (
    Path("data/freq/top1000"),
    Path("src/worldalphabets/data/freq/top1000"),
)
FREQUENCY_SECTION = "frequency_top1000"
FREQUENCY_FILENAME = "top1000.txt"
LEGACY_SOURCE_LABEL = "historic_legacy (Leipzig)"


def _iter_legacy_files() -> Iterable[Path]:
    if not LEGACY_FREQ_DIR.is_dir():
        return []
    return sorted(
        p
        for p in LEGACY_FREQ_DIR.glob("*.txt")
        if p.name.lower() != "build_report_unified.json"
    )


def _iso_codes(tag: str) -> tuple[str, str | None]:
    tag = tag.strip()
    if not tag:
        return "", None
    try:
        lang = langcodes.Language.get(tag)
    except (LookupError, ValueError):
        return tag.lower(), None
    iso3 = (lang.to_alpha3() or tag).lower()
    primary = langcodes.standardize_tag(tag).split("-")[0].lower()
    iso1 = primary if len(primary) == 2 else None
    return iso3, iso1


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _count_tokens(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _ensure_top_level_copy(source: Path, filename: str) -> None:
    for target_root in TOP_LEVEL_FREQ_TARGETS:
        target_root.mkdir(parents=True, exist_ok=True)
        target_file = target_root / f"{filename}.txt"
        if target_file.exists():
            continue
        shutil.copyfile(source, target_file)


def backfill() -> None:
    processed = 0
    copied = 0
    skipped_no_dir: list[str] = []
    skipped_existing: list[str] = []

    for legacy_file in _iter_legacy_files():
        processed += 1
        legacy_code = legacy_file.stem.lower()
        iso3, iso1 = _iso_codes(legacy_code)
        if not iso3:
            skipped_no_dir.append(legacy_code)
            continue

        lang_dir = DATA_ROOT / iso3
        metadata_path = lang_dir / "metadata.json"
        if not metadata_path.exists():
            skipped_no_dir.append(legacy_code)
            continue

        dest_freq_dir = lang_dir / "frequency"
        dest_freq_file = dest_freq_dir / FREQUENCY_FILENAME
        if dest_freq_file.exists():
            skipped_existing.append(legacy_code)
            continue

        dest_freq_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(legacy_file, dest_freq_file)
        _ensure_top_level_copy(legacy_file, iso1 or iso3)

        token_count = _count_tokens(legacy_file)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        sections = metadata.setdefault("sections", {})
        sections[FREQUENCY_SECTION] = {
            "file": f"{iso3}/frequency/{FREQUENCY_FILENAME}",
            "token_count": token_count,
            "mode": "word",
            "source": LEGACY_SOURCE_LABEL,
            "updated": _timestamp(),
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        copied += 1
        print(f"Backfilled legacy frequency for {iso3} ({legacy_code}).")

    print(f"\nProcessed: {processed}")
    print(f"Backfilled: {copied}")
    if skipped_existing:
        print(f"Skipped (already present): {', '.join(sorted(skipped_existing))}")
    if skipped_no_dir:
        print(f"Skipped (missing metadata): {', '.join(sorted(skipped_no_dir))}")


if __name__ == "__main__":
    backfill()
