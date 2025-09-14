"""Source file readers for the top200 builder."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, List

from .tokenize import char_bigrams, word_tokens


def read_lines(path: str | Path) -> Iterable[str]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            yield line.rstrip("\n")


def load_leipzig(path: str | Path) -> List[str]:
    """Parse a Leipzig/Wortschatz file (rank\tword\tfreq)."""

    tokens: List[str] = []
    for line in read_lines(path):
        parts = line.split("\t")
        if len(parts) >= 2:
            tokens.append(parts[1])
    return tokens


def load_hermitdave(path: str | Path) -> List[str]:
    """Parse a HermitDave frequency file (word freq)."""

    tokens: List[str] = []
    for line in read_lines(path):
        parts = line.split()
        if parts:
            tokens.append(parts[0])
    return tokens


def load_stopwords(path: str | Path) -> List[str]:
    """Read a stopwords list (one token per line)."""

    return [line for line in read_lines(path) if line]


def load_tatoeba(path: str | Path, mode: str) -> List[str]:
    """Parse a Tatoeba sentences file using *mode* tokenisation."""

    tokens: List[str] = []
    tokenizer: Callable[[str], List[str]] = word_tokens if mode == "word" else char_bigrams
    for line in read_lines(path):
        tokens.extend(tokenizer(line))
    return tokens
