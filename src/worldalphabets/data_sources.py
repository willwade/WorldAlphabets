"""
Data source collectors for WorldAlphabets pipeline.

This module provides unified access to all external data sources used in the
WorldAlphabets data collection pipeline, with proper caching and fallback handling.
"""

import json
import logging
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    """Base exception for data source errors."""

    pass


class CLDRCollector:
    """Collector for Unicode CLDR (Common Locale Data Repository) data."""

    BASE_URL = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json"

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / "cldr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_available_locales(self) -> Set[str]:
        """Get list of available CLDR locales."""
        url = f"{self.BASE_URL}/cldr-core/availableLocales.json"
        cache_file = self.cache_dir / "availableLocales.json"

        try:
            data = self._fetch_cached_json(url, cache_file)
            return set(data["availableLocales"]["full"])
        except Exception as e:
            logger.error(f"Failed to fetch CLDR available locales: {e}")
            return set()

    def get_exemplar_characters(self, locale: str) -> Optional[Dict]:
        """Get exemplar characters for a locale."""
        url = f"{self.BASE_URL}/cldr-misc-full/main/{locale}/characters.json"
        cache_file = self.cache_dir / f"{locale}_characters.json"

        try:
            data = self._fetch_cached_json(url, cache_file)
            return data["main"][locale]["characters"]
        except Exception as e:
            logger.debug(f"No CLDR exemplar data for {locale}: {e}")
            return None

    def _fetch_cached_json(self, url: str, cache_file: Path) -> Dict:
        """Fetch JSON data with caching."""
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning(f"Corrupted cache file: {cache_file}")

        logger.debug(f"Fetching {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        cache_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data


class ISO639Collector:
    """Collector for ISO 639-3 language registry data."""

    ISO639_3_URL = (
        "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab"
    )

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_language_registry(self) -> List[Dict]:
        """Get complete ISO 639-3 language registry."""
        cache_file = self.cache_dir / "iso-639-3.tab"

        if not cache_file.exists():
            logger.info("Downloading ISO 639-3 registry...")
            try:
                with urllib.request.urlopen(self.ISO639_3_URL) as resp:
                    cache_file.write_bytes(resp.read())
            except Exception as e:
                raise DataSourceError(f"Failed to download ISO 639-3 registry: {e}")

        # Parse tab-separated file
        languages = []
        with open(cache_file, "r", encoding="utf-8") as f:
            headers = f.readline().strip().split("\t")
            for line in f:
                if line.strip():
                    values = line.strip().split("\t")
                    lang_data = dict(zip(headers, values))
                    languages.append(lang_data)

        logger.info(f"Loaded {len(languages)} languages from ISO 639-3 registry")
        return languages


class WikidataCollector:
    """Collector for Wikidata language-script mappings."""

    SPARQL_URL = "https://query.wikidata.org/sparql"
    SPARQL_QUERY = """
    SELECT DISTINCT ?iso1 ?iso3 ?scriptCode WHERE {
      ?lang wdt:P31/wdt:P279* wd:Q34770 ;
            wdt:P282 ?script .
      OPTIONAL { ?lang wdt:P218 ?iso1. }
      OPTIONAL { ?lang wdt:P220 ?iso3. }
      OPTIONAL { ?script wdt:P506 ?scriptCode. }
    }
    LIMIT 10000
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_language_script_mappings(self) -> Dict[str, Set[str]]:
        """Get language to script mappings from Wikidata."""
        cache_file = self.cache_dir / "wikidata_language_scripts.json"

        # Use cache if recent (less than 7 days old)
        if cache_file.exists():
            import time

            if time.time() - cache_file.stat().st_mtime < 7 * 24 * 3600:
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    return {k: set(v) for k, v in data.items()}
                except json.JSONDecodeError:
                    logger.warning("Corrupted Wikidata cache, refetching...")

        logger.info("Fetching language-script mappings from Wikidata...")
        try:
            resp = requests.get(
                self.SPARQL_URL,
                params={"query": self.SPARQL_QUERY, "format": "json"},
                headers={"User-Agent": "WorldAlphabets/1.0"},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise DataSourceError(f"Failed to fetch Wikidata mappings: {e}")

        # Process results
        mappings: Dict[str, Set[str]] = {}
        for row in data["results"]["bindings"]:
            code = row.get("iso1", {}).get("value") or row.get("iso3", {}).get("value")
            script = row.get("scriptCode", {}).get("value")
            if code and script:
                mappings.setdefault(code, set()).add(script)

        # Cache results
        cache_data = {k: sorted(v) for k, v in mappings.items()}
        cache_file.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        logger.info(f"Fetched {len(mappings)} language-script mappings from Wikidata")
        return mappings


class FrequencyCollector:
    """Collector for letter frequency data from multiple sources."""

    SIMIA_URL = "http://simia.net/letters/unigrams.zip"

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.unigrams_dir = cache_dir / "unigrams"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.unigrams_dir.mkdir(parents=True, exist_ok=True)

    def download_simia_unigrams(self) -> bool:
        """Download and extract Simia unigrams dataset."""
        zip_file = self.cache_dir / "unigrams.zip"

        if zip_file.exists():
            logger.debug("Simia unigrams already downloaded")
            return True

        try:
            logger.info("Downloading Simia unigrams dataset...")
            with urllib.request.urlopen(self.SIMIA_URL) as resp:
                zip_file.write_bytes(resp.read())

            with zipfile.ZipFile(zip_file) as zf:
                zf.extractall(self.unigrams_dir)

            logger.info("Simia unigrams dataset downloaded and extracted")
            return True
        except Exception as e:
            logger.error(f"Failed to download Simia unigrams: {e}")
            return False

    def get_frequency_data(self, language_code: str) -> Optional[Dict[str, float]]:
        """Get letter frequency data for a language."""
        # Try Simia unigrams first
        unigrams_file = self.unigrams_dir / f"unigrams-{language_code}.txt"
        if unigrams_file.exists():
            return self._parse_simia_frequencies(unigrams_file)

        # TODO: Add OpenSubtitles fallback
        logger.debug(f"No frequency data available for {language_code}")
        return None

    def _parse_simia_frequencies(self, file_path: Path) -> Dict[str, float]:
        """Parse Simia unigrams frequency file."""
        frequencies = {}
        total_count = 0

        try:
            for line in file_path.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines():
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    char = parts[0]
                    count = int(parts[1])
                    frequencies[char] = count
                    total_count += count
        except Exception as e:
            logger.error(f"Error parsing frequency file {file_path}: {e}")
            return {}

        # Normalize to probabilities
        if total_count > 0:
            return {char: count / total_count for char, count in frequencies.items()}
        return {}


class FallbackDataCollector:
    """Collector for manual fallback data."""

    def __init__(self, fallback_file: Path):
        self.fallback_file = fallback_file

    def get_fallback_alphabets(self) -> Dict[str, Dict[str, str]]:
        """Get manual fallback alphabet definitions."""
        if not self.fallback_file.exists():
            return {}

        try:
            return json.loads(self.fallback_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Error loading fallback data: {e}")
            return {}

    def get_manual_language_additions(self) -> List[Dict]:
        """Get manually added languages from fallbacks.json."""
        if not self.fallback_file.exists():
            return []

        try:
            fallback_data = json.loads(self.fallback_file.read_text(encoding="utf-8"))
            return fallback_data.get("manual_languages", [])
        except Exception as e:
            logger.error(f"Error loading manual language additions: {e}")
            # Fallback to hardcoded Maori if file loading fails
            return [
                {
                    "Id": "mi",
                    "Part1": "mi",
                    "Part2B": "mao",
                    "Part2T": "mri",
                    "Ref_Name": "Māori",
                    "Comment": "Manual addition - missing from Wikidata",
                    "scripts": ["Latn"],
                }
            ]
