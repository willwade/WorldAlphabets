import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import langcodes
import requests
from bs4 import BeautifulSoup

# Manual mapping for language names that don't match directly
LANGUAGE_NAME_MAPPING = {
    "US": "English",
    "United Kingdom": "English",
    "United States-Dvorak": "English",
    "United States-International": "English",
    "Canadian French": "French",
    "Swiss French": "French",
    "Belgian French": "French",
    "Latin American": "Spanish",
    "Swiss German": "German",
    "Bangla": "Bengali",
    "Faeroese": "Faroese",
    "Norwegian with Sami": "Norwegian",
    "Swedish with Sami": "Swedish",
    "Sami Extended Norway": "Northern Sami",
    "Sami Extended Finland-Sweden": "Northern Sami",
    "Cherokee Nation": "Cherokee",
    "Cherokee Phonetic": "Cherokee",
}

STOPWORDS: set[str] = {
    "keyboard",
    "layout",
    "standard",
    "legacy",
    "extended",
    "phonetic",
    "nation",
    "basic",
    "variant",
    "modern",
    "traditional",
    "enhanced",
    "typewriter",
    "programmers",
    "international",
    "classic",
    "alternate",
    "alt",
    "pc",
    "enhanced",
    "romanized",
    "romanised",
    "compact",
    "unicode",
    "script",
    "legacy",
    "with",
    "and",
    "the",
    "regional",
    "extended",
    "symbol",
    "symbols",
    "101",
    "102",
    "103",
    "104",
    "105",
    "106",
}


def strip_diacritics(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch)
    )


def normalize_language_name(value: str) -> str:
    if not value:
        return ""
    normalized = strip_diacritics(value)
    normalized = re.sub(r"\(.*?\)", " ", normalized)
    normalized = re.sub(r"[^A-Za-z0-9]+", " ", normalized)
    tokens = []
    for token in normalized.lower().split():
        if not token or token in STOPWORDS or token.isdigit():
            continue
        tokens.append(token)
    return " ".join(tokens)


def dedupe_entries(entries: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    result: List[Dict[str, Any]] = []
    for entry in entries:
        key = (
            entry.get("language"),
            entry.get("script"),
            entry.get("file"),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def resolve_candidates(
    lang_name: str,
    norm_lookup: Dict[str, List[Dict[str, Any]]],
    iso_lookup: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    normalized = normalize_language_name(lang_name)
    if normalized:
        direct_matches = norm_lookup.get(normalized)
        if direct_matches:
            return dedupe_entries(direct_matches)

        # Try progressively shortening the name (dropping trailing tokens)
        parts = normalized.split()
        while len(parts) > 1:
            parts.pop()
            key = " ".join(parts)
            if key in norm_lookup:
                return dedupe_entries(norm_lookup[key])

    codes: set[str] = set()
    try:
        tag_obj = langcodes.find(lang_name)
        if tag_obj:
            tag = tag_obj if isinstance(tag_obj, str) else tag_obj.to_tag()
            if tag:
                codes.add(tag.lower())
                primary = tag.split("-")[0].lower()
                codes.add(primary)
                language = langcodes.get(tag)
                lang_code = language.language or ""
                if lang_code:
                    codes.add(lang_code.lower())
                try:
                    alpha3 = language.to_alpha3()
                    if alpha3:
                        codes.add(alpha3.lower())
                except LookupError:
                    pass
    except LookupError:
        pass

    matched_entries: List[Dict[str, Any]] = []
    for code in codes:
        matches = iso_lookup.get(code)
        if matches:
            matched_entries.extend(matches)

    return dedupe_entries(matched_entries)


def get_driver_name(session: requests.Session, url: str) -> str | None:
    """Fetches the driver name from a kbdlayout.info page."""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the "Layout File" table row
        layout_file_header = soup.find("th", string=re.compile(r"Layout File"))
        if layout_file_header:
            layout_file_cell = layout_file_header.find_next_sibling("td")
            if layout_file_cell:
                # Driver name is like KBDGR.DLL, we want KBDGR
                driver_name = layout_file_cell.text.strip()
                if driver_name.upper().endswith(".DLL"):
                    return driver_name[:-4]
                return driver_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None


def main() -> None:
    """
    Populates index.json with keyboard layouts and generates a driver mapping.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate index.json with keyboard layouts and generate driver mapping"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip languages that already have keyboard layouts"
    )
    args = parser.parse_args()
    data_root = Path("data")
    index_path = data_root / "index.json"
    kbdlayouts_path = data_root / "kbdlayouts.json"
    driver_mapping_path = data_root / "mappings" / "layout_to_driver.json"

    with open(index_path, "r", encoding="utf-8") as f:
        index_data: List[Dict[str, Any]] = json.load(f)

    with open(kbdlayouts_path, "r", encoding="utf-8") as f:
        kbdlayouts_data: Dict[str, Any] = json.load(f)

    # Clear existing keyboard lists (unless skipping existing)
    if not args.skip_existing:
        for entry in index_data:
            if "keyboards" in entry:
                entry["keyboards"] = []
    else:
        # Initialize empty keyboards lists for entries that don't have them
        for entry in index_data:
            if "keyboards" not in entry:
                entry["keyboards"] = []

    norm_name_to_entries: Dict[str, List[Dict[str, Any]]] = {}
    iso_to_entries: Dict[str, List[Dict[str, Any]]] = {}
    for entry in index_data:
        norm_name = normalize_language_name(entry["name"])
        if norm_name:
            norm_name_to_entries.setdefault(norm_name, []).append(entry)
        codes = (
            entry.get("language"),
            entry.get("iso639_1"),
            entry.get("iso639_3"),
        )
        for code in codes:
            if code:
                iso_to_entries.setdefault(code.lower(), []).append(entry)

    layout_to_driver: Dict[str, str] = {}

    session = requests.Session()

    for layout_id, layout_info in kbdlayouts_data.items():
        lang_name = layout_info.get("language")
        if not lang_name:
            continue

        # Handle special cases
        lang_name = LANGUAGE_NAME_MAPPING.get(lang_name, lang_name)

        candidates = resolve_candidates(lang_name, norm_name_to_entries, iso_to_entries)

        if candidates:
            for lang_entry in candidates:
                if "keyboards" not in lang_entry:
                    lang_entry["keyboards"] = []

                # Skip if already has keyboards and skip_existing is True
                if args.skip_existing and lang_entry["keyboards"]:
                    continue

                if layout_id not in lang_entry["keyboards"]:
                    lang_entry["keyboards"].append(layout_id)

            # Get the driver name
            href = layout_info.get("href")
            if href:
                url = f"http://kbdlayout.info{href}"
                driver_name = get_driver_name(session, url)
                if driver_name:
                    layout_to_driver[layout_id] = driver_name
                    print(f"Mapped {layout_id} ({lang_name}) to {driver_name}")
                else:
                    print(f"Could not find driver for {layout_id} ({lang_name})")
        else:
            print(f"Warning: No language match found for layout {layout_id} ({lang_name})")

    # Write updated index.json
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Updated {index_path}")

    # Write layout_to_driver.json
    driver_mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with open(driver_mapping_path, "w", encoding="utf-8") as f:
        json.dump(layout_to_driver, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote driver mapping to {driver_mapping_path}")


if __name__ == "__main__":
    main()
