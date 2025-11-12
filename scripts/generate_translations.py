#!/usr/bin/env python3
import argparse
import html
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import requests

try:
    from scripts.lib.data_layout import RepoDataLayout
except ModuleNotFoundError:  # pragma: no cover
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.lib.data_layout import RepoDataLayout

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
REQUEST_TIMEOUT = 15
RETRY_BACKOFFS = [1, 2, 4, 8]

ALPHABETS_DIR = Path("data/alphabets")
INDEX_PATH = Path("data/index.json")
FIELD_NAME = "hello_how_are_you"
SOURCE_TEXT = "Hello how are you?"
CACHE_DIR = Path(".cache/translations")
DATA_LAYOUT = RepoDataLayout()

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


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


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


def cache_file_path(lang_code: str, script: str) -> Path:
    canonical = DATA_LAYOUT.canonical_code(lang_code)
    return CACHE_DIR / canonical / f"{canonical}-{script}.json"


def load_cached_translation(
    lang_code: str, script: str, target: str
) -> Optional[Dict[str, Any]]:
    path = cache_file_path(lang_code, script)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    entries = cached.get("entries") or {}
    entry = entries.get(target)
    if entry and entry.get("text"):
        return entry
    return None


def save_cached_translation(
    lang_code: str, script: str, target: str, text: str
) -> None:
    path = cache_file_path(lang_code, script)
    if path.exists():
        try:
            cache_obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            cache_obj = {}
    else:
        cache_obj = {}
    entries = cache_obj.setdefault("entries", {})
    entries[target] = {
        "text": text,
        "timestamp": _utcnow(),
        "source": "google_translate",
    }
    cache_obj["language"] = DATA_LAYOUT.canonical_code(lang_code)
    cache_obj["script"] = script
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache_obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_alphabet_record(canonical_path: Path, legacy_path: Path) -> Dict[str, Any]:
    for path in (canonical_path, legacy_path):
        if path.exists():
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
    return {
        "alphabetical": [],
        "uppercase": [],
        "lowercase": [],
        "frequency": {},
    }


def write_alphabet_records(lang_code: str, script: str, data: Dict[str, Any]) -> None:
    canonical_path = DATA_LAYOUT.alphabet_path(lang_code, script)
    DATA_LAYOUT.ensure_section(lang_code, "alphabet")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    canonical_path.write_text(payload, encoding="utf-8")

    legacy_path = ALPHABETS_DIR / f"{lang_code}-{script}.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(payload, encoding="utf-8")


def generate_translations(skip_existing: bool = False) -> None:
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
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    unsupported: List[Dict[str, str]] = []

    for item in languages:
        try:
            lang_code = item["language"]
            lang_name = item.get("name", lang_code)
            script = item["script"]
            # Prefer iso639_1 (2-letter) for Google Translate API
            iso639_1 = item.get("iso639_1")
        except (KeyError, TypeError):
            print(f"Skipping malformed entry: {item!r}")
            continue

        # Try to find a supported Google Translate code
        # Priority: iso639_1-script, iso639_1, lang_code-script, lang_code
        target = None
        script_specific = False
        display_code = f"{lang_code}-{script}"

        if iso639_1:
            # Try 2-letter code with script first (e.g., zh-CN)
            code_with_script = f"{iso639_1}-{script}"
            target = find_supported_code(code_with_script, supported)
            if target:
                script_specific = True
            else:
                # Try plain 2-letter code
                target = find_supported_code(iso639_1, supported)

        if not target:
            # Fallback to 3-letter code
            code_with_script = f"{lang_code}-{script}"
            target = find_supported_code(code_with_script, supported)
            if target:
                script_specific = True
            else:
                target = find_supported_code(lang_code, supported)

        if not target:
            print(
                f"- {lang_name} ({display_code}) -> " f"unsupported by Google; skipping"
            )
            unsupported.append(
                {"language": lang_code, "script": script, "name": lang_name}
            )
            continue

        canonical_lang = DATA_LAYOUT.canonical_code(lang_code)
        legacy_path = ALPHABETS_DIR / f"{lang_code}-{script}.json"
        canonical_path = DATA_LAYOUT.alphabet_path(lang_code, script)
        base_obj = load_alphabet_record(canonical_path, legacy_path)

        if skip_existing and FIELD_NAME in base_obj:
            print(f"- {lang_name} ({display_code}) -> " f"skipped (already translated)")
            continue

        cache_hit = load_cached_translation(canonical_lang, script, target)
        output_label = f"{legacy_path}"
        match_type = "script-match" if script_specific else "fallback"
        print(
            f"- {lang_name} ({display_code}) -> target '{target}' "
            f"({match_type}) -> {output_label} ... ",
            end="",
            flush=True,
        )

        if cache_hit:
            base_obj[FIELD_NAME] = cache_hit["text"]
            write_alphabet_records(lang_code, script, base_obj)
            DATA_LAYOUT.update_metadata(
                canonical_lang,
                f"translation_{script}",
                {
                    "script": script,
                    "source": "google_translate (cache)",
                    "target": target,
                    "cached": True,
                },
            )
            DATA_LAYOUT.append_source_entry(
                canonical_lang,
                "translation",
                "Translation applied from cache",
                {"script": script, "target": target},
            )
            print("cached")
            continue

        try:
            translated = translate_once(api_key, SOURCE_TEXT, target)
            base_obj[FIELD_NAME] = translated
            write_alphabet_records(lang_code, script, base_obj)
            save_cached_translation(canonical_lang, script, target, translated)
            DATA_LAYOUT.update_metadata(
                canonical_lang,
                f"translation_{script}",
                {
                    "script": script,
                    "source": "google_translate",
                    "target": target,
                    "cached": False,
                },
            )
            DATA_LAYOUT.append_source_entry(
                canonical_lang,
                "translation",
                "Translation updated via Google Translate",
                {"script": script, "target": target},
            )
            print("ok")
        except requests.HTTPError as e:
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
    parser = argparse.ArgumentParser(
        description="Generate translations for alphabet files using Google Translate API"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip languages that already have translations",
    )
    args = parser.parse_args()

    generate_translations(skip_existing=args.skip_existing)
