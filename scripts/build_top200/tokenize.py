"""Tokenisation helpers."""
from __future__ import annotations

from typing import List

import regex as re

WORD_RE = re.compile(r"\p{L}+", re.UNICODE)
LETTER_RE = re.compile(r"\p{L}", re.UNICODE)


def word_tokens(text: str) -> List[str]:
    """Return all word tokens from *text*."""
    return WORD_RE.findall(text)


def char_bigrams(text: str) -> List[str]:
    """Return character bigrams derived from *text*.

    Only Unicode letters are considered for the bigram sequence.
    """

    letters = LETTER_RE.findall(text)
    return [a + b for a, b in zip(letters, letters[1:])]
