#!/usr/bin/env python3
import os
import json
import time
import html
from typing import Dict, Any, Iterable, List, Optional, Set
import requests
from pathlib import Path

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
REQUEST_TIMEOUT = 15
RETRY_BACKOFFS = [1, 2, 4, 8]

ALPHABETS_DIR = Path("data/alphabets")
INDEX_PATH = Path("data/index.json")
FIELD_NAME = "hello_how_are_you"
SOURCE_TEXT = "Hello how are you?"

# Known alias/canonicalization candidates -> try in order
ALIASES: Dict[str, List[str]] = {
    # Chinese family & legacy quirks
    "zh": ["zh-CN"],
    "zh-hans": ["zh-CN"],
    "zh-cn": ["zh-CN"],
    "zh_hans": ["zh-CN"],
    "zh-hant": ["zh-TW"],
    "zh-tw": ["zh-TW"],
    "zh_hant": ["zh-TW"],
    "zh-yue": ["yue"],  # Cantonese
    "yue": ["yue"],  # explicit
    "zh-min-nan": ["nan"],  # Hokkien/Min Nan (if supported)
    # Historical or dataset quirks
    "jw": ["jv"],  # Javanese
    "he": ["he", "iw"],  # Google used to accept 'iw'
    "tl": ["tl", "fil"],  # Tagalog/Filipino sometimes interchangeable
    "nb": ["nb", "no"],  # Bokmål vs Norwegian
    # fallbacks where API prefers 2-letter
    "id": ["id"],  # Indonesian (not 'in')
}


def backoff_delays() -> Iterable[int]:
    yield 0
    for d in RETRY_BACKOFFS:
        yield d


def http_get(url: str, *, params: Dict[str, Any]) -> requests.Response:
    for delay in backoff_delays():
        if delay:
            time.sleep(delay)
        try:
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code in {429, 500, 502, 503, 504}:
                continue
            r.raise_for_status()
            return r
        except requests.RequestException:
            # Retry on transient network issues
            continue
    # Final attempt (to raise helpful error)
    r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r


def get_supported_languages(api_key: str) -> Set[str]:
    """
    Fetch the set of supported target language codes from Google.
    Returns codes like 'en', 'fr', 'zh-CN', 'yue', etc.
    """
    params = {"key": api_key, "target": "en"}  # 'target' just localizes names
    resp = http_get(f"{TRANSLATE_URL}/languages", params=params)
    data = resp.json()
    langs = {entry["language"] for entry in data.get("data", {}).get("languages", [])}
    return langs


def candidate_codes(code: str) -> List[str]:
    """
    Generate a list of candidate codes to try for a given dataset code.
    """
    c = code.strip()
    lower = c.lower()

    # Preserve original casing variant for things like 'zh-CN'
    # Try exact first, then alias list (which may include canonical casing)
    tried: List[str] = [c]

    # Normalized alias list
    if lower in ALIASES:
        for a in ALIASES[lower]:
            if a not in tried:
                tried.append(a)

    # Common Chinese normalizations if not already included
    if lower == "zh" and "zh-CN" not in tried:
        tried.append("zh-CN")

    return tried


def find_supported_code(raw_code: str, supported: Set[str]) -> Optional[str]:
    for cand in candidate_codes(raw_code):
        if cand in supported:
            return cand
    return None


def translate_once(api_key: str, text: str, target: str) -> str:
    params = {"q": text, "target": target, "key": api_key, "format": "text"}
    resp = http_get(TRANSLATE_URL, params=params)
    data: Dict[str, Any] = resp.json()
    return html.unescape(data["data"]["translations"][0]["translatedText"])


def generate_translations() -> None:
    api_key = os.environ.get("GOOGLE_TRANS_KEY")
    if not api_key:
        print("Error: GOOGLE_TRANS_KEY environment variable not set.")
        return

    # Load index
    try:
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            languages = json.load(f)
    except Exception as e:
        print(f"Error reading {INDEX_PATH}: {e}")
        return

    if not isinstance(languages, list):
        print("Error: data/index.json should be an array of language entries.")
        return

    # Fetch supported languages once
    try:
        supported = get_supported_languages(api_key)
    except Exception as e:
        print(f"Error fetching supported languages: {e}")
        return

    print(f"Loaded {len(supported)} supported Google Translate codes.\n")

    # Ensure output directory
    ALPHABETS_DIR.mkdir(parents=True, exist_ok=True)

    unsupported: List[Dict[str, str]] = []

    for item in languages:
        try:
            lang_code = item["language"]
            lang_name = item.get("language-name", lang_code)
        except (KeyError, TypeError):
            print(f"Skipping malformed entry: {item!r}")
            continue

        target = find_supported_code(lang_code, supported)
        file_path = ALPHABETS_DIR / f"{lang_code}.json"

        if not target:
            print(f"- {lang_name} ({lang_code}) -> unsupported by Google; skipping")
            unsupported.append({"language": lang_code, "name": lang_name})
            continue

        print(
            f"- {lang_name} ({lang_code}) -> using target '{target}' -> {file_path} ... ",
            end="",
            flush=True,
        )

        # Load or create base file
        if file_path.exists():
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    base_obj = json.load(f)
                if not isinstance(base_obj, dict):
                    raise ValueError("Top-level JSON must be an object")
            except Exception as e:
                print(f"failed to read: {e}")
                continue
        else:
            base_obj = {
                "alphabetical": [],
                "uppercase": [],
                "lowercase": [],
                "frequency": {},
            }

        try:
            translated = translate_once(api_key, SOURCE_TEXT, target)
            base_obj[FIELD_NAME] = translated
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(base_obj, f, ensure_ascii=False, indent=2)
            print("ok")
        except requests.HTTPError as e:
            # Avoid logging full URL (which includes your key)
            status = e.response.status_code if e.response is not None else "?"
            try:
                err_json = e.response.json()
                msg = err_json.get("error", {}).get("message", "")
            except Exception:
                msg = str(e)
            print(f"failed: HTTP {status} {msg}")
        except Exception as e:
            print(f"failed: {e}")

    # Optional: write a small report of unsupported languages for follow-up
    if unsupported:
        report_path = Path("data/unsupported_translations.json")
        try:
            with report_path.open("w", encoding="utf-8") as f:
                json.dump(unsupported, f, ensure_ascii=False, indent=2)
            print(f"\nWrote unsupported list to {report_path}")
        except Exception as e:
            print(f"\nFailed to write unsupported list: {e}")


if __name__ == "__main__":
    generate_translations()
