"""Merge tokens from multiple sources and write outputs."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class LangResult:
    tokens: List[str]
    source_counts: Dict[str, int]
    mode: str
    partial: bool
    sha256: Dict[str, str]


def merge_sources(sources: List[Tuple[str, List[str]]], limit: int) -> Tuple[List[str], Dict[str, int]]:
    """Merge *sources* according to precedence returning tokens and counts."""

    merged: List[str] = []
    seen: set[str] = set()
    counts: Dict[str, int] = {}
    for name, items in sources:
        for token in items:
            if token in seen:
                continue
            merged.append(token)
            seen.add(token)
            counts[name] = counts.get(name, 0) + 1
            if len(merged) >= limit:
                break
        if len(merged) >= limit:
            break
    return merged, counts


def write_tokens(path: Path, tokens: List[str], mode: str) -> None:
    """Write *tokens* to *path* respecting *mode*."""

    lines = tokens[:]
    if mode == "bigram":
        lines.insert(0, "# type=bigram")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    h = sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
