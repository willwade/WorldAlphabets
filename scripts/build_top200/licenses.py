"""License and provenance helpers for sources."""
from __future__ import annotations

from typing import Dict

LICENSES: Dict[str, Dict[str, str]] = {
    "leipzig": {
        "name": "Leipzig Corpora Collection",
        "license": "CC-BY 4.0",
        "url": "https://wortschatz.uni-leipzig.de/en/download",
    },
    "hermitdave": {
        "name": "HermitDave Frequency Words",
        "license": "CC-BY",
        "url": "https://github.com/hermitdave/FrequencyWords",
    },
    "tatoeba": {
        "name": "Tatoeba",
        "license": "CC-BY 2.0 FR",
        "url": "https://tatoeba.org/",
    },
    "stopwords": {
        "name": "Stopwords ISO",
        "license": "MIT",
        "url": "https://github.com/stopwords-iso/",
    },
}


def render_sources_md(report: Dict[str, Dict]) -> str:
    """Render a SOURCES.md document from *report* metadata."""

    lines = ["# Frequency Sources", ""]
    for lang, info in sorted(report.items()):
        lines.append(f"## {lang} — {info['name']}")
        for source, count in info["source_counts"].items():
            meta = LICENSES.get(source, {})
            url = meta.get("url", "")
            lic = meta.get("license", "")
            lines.append(f"- {source}: {count} entries — {lic} {url}")
        notes = info.get("notes")
        if notes:
            lines.append(f"Notes: {notes}")
        lines.append("")
    return "\n".join(lines)
