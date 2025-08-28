#!/usr/bin/env python3
"""Fetch language to script mappings from Wikidata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Set

import requests

SPARQL_URL = "https://query.wikidata.org/sparql"
SPARQL_QUERY = """
SELECT ?iso1 ?iso3 ?scriptCode WHERE {
  ?lang wdt:P282 ?script .
  OPTIONAL { ?lang wdt:P218 ?iso1. }
  OPTIONAL { ?lang wdt:P220 ?iso3. }
  OPTIONAL { ?script wdt:P506 ?scriptCode. }
}
"""


def fetch_mappings() -> Dict[str, Set[str]]:
    """Return mapping of language codes to sets of script codes."""
    resp = requests.get(
        SPARQL_URL,
        params={"query": SPARQL_QUERY, "format": "json"},
        headers={"User-Agent": "WorldAlphabets/0.1"},
        timeout=30,
    )
    resp.raise_for_status()
    mapping: Dict[str, Set[str]] = {}
    for row in resp.json()["results"]["bindings"]:
        code = row.get("iso1", {}).get("value") or row.get("iso3", {}).get("value")
        script = row.get("scriptCode", {}).get("value")
        if not code or not script:
            continue
        mapping.setdefault(code, set()).add(script)
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default="data/language_scripts.json",
        help="path to write mapping JSON",
    )
    args = parser.parse_args()
    mapping = fetch_mappings()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_map = {k: sorted(v) for k, v in sorted(mapping.items())}
    out_path.write_text(
        json.dumps(sorted_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out_path} with {len(sorted_map)} languages")


if __name__ == "__main__":
    main()
