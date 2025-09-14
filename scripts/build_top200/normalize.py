"""Token normalization helpers for top200 builder."""
from __future__ import annotations

from typing import Dict, Optional, Set
import unicodedata

import regex as re

# Match a sequence of letters only
LETTER_RE = re.compile(r"^\p{L}+$", re.UNICODE)


def normalize_token(token: str, lang: str, allowlists: Dict[str, Set[str]]) -> Optional[str]:
    """Normalize a single token.

    The token is NFKC-normalised, lowercased and stripped of apostrophes.
    Tokens containing digits or punctuation are rejected. One letter words are
    allowed only when present in the allowlist for the given language or the
    global ``default`` allowlist.
    """

    norm = unicodedata.normalize("NFKC", token).lower().strip()
    norm = norm.replace("'", "")
    if not norm:
        return None
    if any(ch.isdigit() for ch in norm):
        return None
    if not LETTER_RE.fullmatch(norm):
        return None
    if len(norm) == 1 and norm not in _allowed(lang, allowlists):
        return None
    return norm


def _allowed(lang: str, allowlists: Dict[str, Set[str]]) -> Set[str]:
    """Return the allowlist for a language including defaults."""

    allowed: Set[str] = set(allowlists.get("default", set()))
    allowed.update(allowlists.get(lang, set()))
    return allowed
