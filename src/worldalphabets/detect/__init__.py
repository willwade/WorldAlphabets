"""Language detection using script priors and Top-200 token overlap."""
from __future__ import annotations

import math
import os
import unicodedata
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

__all__ = ["detect_languages", "PRIOR_WEIGHT", "FREQ_WEIGHT"]

DEFAULT_FREQ_DIR = files("worldalphabets") / "data" / "freq" / "top200"
PRIOR_WEIGHT = float(os.environ.get("WA_FREQ_PRIOR_WEIGHT", 0.65))
FREQ_WEIGHT = float(os.environ.get("WA_FREQ_OVERLAP_WEIGHT", 0.35))


def _tokenize_words(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return set(
        __import__("re").findall(
            r"[^\W\d_]+", normalized, flags=__import__("re").UNICODE
        )
    )


def _tokenize_bigrams(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    letters = [ch for ch in normalized if ch.isalpha()]
    return {"".join(letters[i : i + 2]) for i in range(len(letters) - 1)}


@dataclass
class RankData:
    mode: str
    ranks: Dict[str, int]


def _load_rank_data(lang: str, freq_dir: Path) -> RankData:
    path = freq_dir / f"{lang}.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return RankData("word", {})
    mode = "word"
    if lines and lines[0].startswith("#"):
        header = lines.pop(0)
        if "bigram" in header:
            mode = "bigram"
    ranks: Dict[str, int] = {}
    for idx, token in enumerate(lines, start=1):
        if token and token not in ranks:
            ranks[token] = idx
    return RankData(mode, ranks)


def _overlap(tokens: Iterable[str], ranks: Dict[str, int]) -> float:
    score = 0.0
    for token in tokens:
        rank = ranks.get(token)
        if rank:
            score += 1 / math.log2(rank + 1.5)
    if score == 0:
        return 0.0
    return score


def detect_languages(
    text: str,
    *,
    candidate_langs: List[str],
    priors: Dict[str, float] | None = None,
    topk: int = 3,
) -> List[Tuple[str, float]]:
    """Return top language guesses for ``text``.

    Combines provided ``priors`` with token overlap from Top-200 lists.
    """

    priors = priors or {}
    env_dir = os.environ.get("WORLDALPHABETS_FREQ_DIR")
    freq_dir = Path(env_dir) if env_dir else Path(str(DEFAULT_FREQ_DIR))

    word_tokens = _tokenize_words(text)
    bigram_tokens = _tokenize_bigrams(text)

    results: List[Tuple[str, float]] = []
    for lang in candidate_langs:
        data = _load_rank_data(lang, freq_dir)
        tokens = word_tokens if data.mode == "word" else bigram_tokens
        overlap = 0.0
        if data.ranks and tokens:
            overlap = _overlap(tokens, data.ranks)
            overlap /= math.sqrt(len(tokens) + 3)
        final = PRIOR_WEIGHT * priors.get(lang, 0.0) + FREQ_WEIGHT * overlap
        if final > 0.05:
            results.append((lang, final))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:topk]
