#!/usr/bin/env python3
"""Fetch alphabets from the kalenchukov/Alphabet Java repository."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
import urllib.request
from pathlib import Path
from typing import Dict, List

import langcodes

REPO_URL = "https://github.com/kalenchukov/Alphabet.git"
REPO_PATH = Path("external/Alphabet")
JAVA_SRC = REPO_PATH / "src/main/java/dev/kalenchukov/alphabet"

SAMPLE_TEXT_URLS: Dict[str, str] = {
    "en": "https://en.wikipedia.org/wiki/English_language?action=render",
    "ru": (
        "https://ru.wikipedia.org/wiki/"
        "%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9_%D1%8F%D0%B7%D1%8B%D0%BA"
        "?action=render"
    ),
    "el": (
        "https://el.wikipedia.org/wiki/"
        "%CE%95%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA%CE%AE_%CE%B3%CE%BB%CF%8E%CF%83%CF%83%CE%B1"
        "?action=render"
    ),
    "fr": (
        "https://fr.wikipedia.org/wiki/"
        "Langue_fran%C3%A7aise?action=render"
    ),
    "de": (
        "https://de.wikipedia.org/wiki/"
        "Deutsche_Sprache?action=render"
    ),
}


def clone_repo() -> None:
    """Clone the external Java repository if needed."""
    if REPO_PATH.exists():
        return
    REPO_PATH.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "git",
        "clone",
        "--depth",
        "1",
        REPO_URL,
        str(REPO_PATH),
    ], check=True)


def _strip_diacritics(text: str) -> str:
    """Return ``text`` without combining marks."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _fetch_text(url: str) -> str:
    with urllib.request.urlopen(url) as response:  # nosec B310
        html = response.read().decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", "", html)
    return _strip_diacritics(text).lower()


def _letter_frequency(text: str, letters: List[str]) -> Dict[str, float]:
    counts = {ch: 0 for ch in letters}
    total = 0
    for ch in text:
        if ch in counts:
            counts[ch] += 1
            total += 1
    if total == 0:
        return {ch: 0.0 for ch in letters}
    return {ch: round(counts[ch] / total, 4) for ch in letters}


def parse_letter_groups(java_file: Path) -> Dict[str, List[str]]:
    """Extract alphabetical, upper, and lower case letters from ``java_file``."""
    text = java_file.read_text(encoding="utf-8")

    def extract(pattern: str) -> List[str] | None:
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return None
        codes = re.findall(r"'\\u([0-9A-Fa-f]{4})'", match.group(1))
        return [chr(int(code, 16)) for code in codes]

    alphabetical = extract(r"LETTERS\s*=\s*List\.of\((.*?)\);")
    if alphabetical is None:
        raise ValueError(
            f"Could not find pattern in {java_file}: LETTERS list not found",
        )
    uppercase = extract(r"UpperCase.*?LETTERS\s*=\s*List\.of\((.*?)\);")
    lowercase = extract(r"LowerCase.*?LETTERS\s*=\s*List\.of\((.*?)\);")
    if uppercase is None or lowercase is None:
        uppercase = lowercase = alphabetical
    return {"alphabetical": alphabetical, "uppercase": uppercase, "lowercase": lowercase}


def main() -> None:
    clone_repo()
    output_dir = Path("data/alphabets")
    output_dir.mkdir(parents=True, exist_ok=True)
    todo: List[Dict[str, str]] = []
    for file in JAVA_SRC.glob("*Alphabet.java"):
        name = file.stem.replace("Alphabet", "")
        try:
            code = langcodes.find(name).language or ""
        except LookupError:
            code = ""
        if not code:
            todo.append({"language": name, "code": "", "reason": "unknown language"})
            continue
        try:
            groups = parse_letter_groups(file)
        except ValueError as exc:  # missing case information
            todo.append({"language": name, "code": code, "reason": str(exc)})
            continue
        url = SAMPLE_TEXT_URLS.get(code)
        if url is None:
            todo.append(
                {
                    "language": name,
                    "code": code,
                    "reason": "missing sample text",
                }
            )
            freq = {ch: 0.0 for ch in groups["lowercase"]}
        else:
            sample = _fetch_text(url)
            freq = _letter_frequency(sample, groups["lowercase"])
        output_path = output_dir / f"{code}.json"
        output_path.write_text(
            json.dumps({**groups, "frequency": freq}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"Wrote {name} ({code}) alphabet ({len(groups['alphabetical'])} letters) "
            f"to {output_path}."
        )
    todo_path = Path("data/todo_languages.csv")
    with todo_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["language", "code", "reason"])
        writer.writeheader()
        writer.writerows(todo)
    print(f"Recorded {len(todo)} missing languages to {todo_path}.")


if __name__ == "__main__":
    main()
