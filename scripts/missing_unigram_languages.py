#!/usr/bin/env python3
"""List language codes present in Simia unigrams but missing alphabets."""
from __future__ import annotations

from pathlib import Path
import re
import urllib.request
import zipfile

UNIGRAMS_URL = "http://simia.net/letters/unigrams.zip"
UNIGRAMS_ZIP = Path("external/unigrams/unigrams.zip")
UNIGRAMS_DIR = UNIGRAMS_ZIP.parent


def _download_unigrams() -> None:
    """Download and extract the unigrams dataset if needed."""
    if UNIGRAMS_ZIP.exists():
        return
    UNIGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(UNIGRAMS_URL) as resp:  # nosec B310
        UNIGRAMS_ZIP.write_bytes(resp.read())
    with zipfile.ZipFile(UNIGRAMS_ZIP) as zf:
        zf.extractall(UNIGRAMS_DIR)


def main() -> None:
    """Print codes that lack alphabet JSON files."""
    _download_unigrams()
    codes = []
    for path in UNIGRAMS_DIR.glob("unigrams-*.txt"):
        m = re.match(r"unigrams-(.+)\.txt", path.name)
        if m:
            codes.append(m.group(1))
    alphabet_codes = {p.stem for p in Path("data/alphabets").glob("*.json")}
    missing = sorted(set(codes) - alphabet_codes)
    for code in missing:
        print(code)


if __name__ == "__main__":
    main()
