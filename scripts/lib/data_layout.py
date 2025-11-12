from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utcnow() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class RepoDataLayout:
    """Helper for working with the per-language data layout under ``data/``."""

    root: Path = Path("data")
    _registry_cache: Optional[Dict[str, Dict[str, Any]]] = None
    _iso1_to_code: Optional[Dict[str, str]] = None
    _iso3_to_code: Optional[Dict[str, str]] = None

    def canonical_code(self, lang: str) -> str:
        code = (lang or "").lower()
        if not code:
            return code
        registry = self._language_registry()
        if code in registry:
            return code
        if self._iso1_to_code and code in self._iso1_to_code:
            return self._iso1_to_code[code]
        if self._iso3_to_code and code in self._iso3_to_code:
            return self._iso3_to_code[code]
        return code

    def lang_dir(self, lang: str) -> Path:
        return self.root / self.canonical_code(lang)

    def alphabet_dir(self, lang: str) -> Path:
        return self.lang_dir(lang) / "alphabet"

    def alphabet_path(self, lang: str, script: str) -> Path:
        return self.alphabet_dir(lang) / f"{lang}-{script}.json"

    def legacy_alphabet_dir(self) -> Path:
        return self.root / "alphabets"

    def frequency_dir(self, lang: str) -> Path:
        return self.lang_dir(lang) / "frequency"

    def frequency_path(self, lang: str, filename: str = "top1000.txt") -> Path:
        return self.frequency_dir(lang) / filename

    def legacy_frequency_dir(self) -> Path:
        return self.root / "freq" / "top1000"

    def layouts_dir(self, lang: str) -> Path:
        return self.lang_dir(lang) / "layouts"

    def layouts_index_path(self) -> Path:
        return self.root / "layouts" / "index.json"

    def layout_path(self, lang: str, layout_id: str) -> Path:
        return self.layouts_dir(lang) / f"{layout_id}.json"

    def legacy_layouts_dir(self) -> Path:
        return self.root / "layouts"

    def audio_dir(self, lang: str) -> Path:
        return self.lang_dir(lang) / "audio"

    def audio_index_path(self) -> Path:
        return self.root / "audio" / "index.json"

    def audio_path(self, lang: str, filename: str) -> Path:
        return self.audio_dir(lang) / filename

    def legacy_audio_dir(self) -> Path:
        return self.root / "audio"

    def metadata_path(self, lang: str) -> Path:
        return self.lang_dir(lang) / "metadata.json"

    def source_log_path(self, lang: str) -> Path:
        return self.lang_dir(lang) / "SOURCE.txt"

    # ------------------------------------------------------------------ helpers
    def _language_registry(self) -> Dict[str, Dict[str, Any]]:
        if self._registry_cache is None:
            registry_path = self.root / "language_registry.json"
            if registry_path.exists():
                data = json.loads(registry_path.read_text(encoding="utf-8"))
            else:
                data = {}
            self._registry_cache = data
            iso1_map: Dict[str, str] = {}
            iso3_map: Dict[str, str] = {}
            for code, info in data.items():
                iso1 = (info.get("iso639_1") or "").lower()
                iso3 = (info.get("iso639_3") or "").lower()
                if iso1:
                    iso1_map[iso1] = code
                if iso3:
                    iso3_map[iso3] = code
                iso3_map[code] = code
            self._iso1_to_code = iso1_map
            self._iso3_to_code = iso3_map
        return self._registry_cache

    def get_language_info(self, lang: str) -> Dict[str, Any]:
        registry = self._language_registry()
        canonical = self.canonical_code(lang)
        info = registry.get(canonical)
        if not info:
            return {"code": canonical, "iso639_3": canonical}
        return info

    def ensure_language_root(self, lang: str) -> None:
        """Ensure the main language directory exists."""
        self.lang_dir(lang).mkdir(parents=True, exist_ok=True)

    def ensure_section(self, lang: str, section: str) -> Path:
        """Ensure a subsection (alphabet/frequency/etc.) exists and return it."""
        section_dir_map = {
            "alphabet": self.alphabet_dir,
            "frequency": self.frequency_dir,
            "layouts": self.layouts_dir,
            "audio": self.audio_dir,
        }
        if section not in section_dir_map:
            raise ValueError(f"Unknown section '{section}'")
        folder = section_dir_map[section](lang)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def update_metadata(
        self,
        lang: str,
        section: str,
        payload: Dict[str, Any],
        *,
        language_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update metadata.json for ``lang`` with information about ``section``."""

        canonical = self.canonical_code(lang)
        path = self.metadata_path(canonical)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {"language": canonical, "sections": {}}

        payload = dict(payload)
        payload.setdefault("updated", _utcnow())
        data["sections"][section] = payload

        info = language_info or self.get_language_info(canonical)
        if info:
            data["language"] = info.get("code", canonical)
            data["language_name"] = info.get("name") or info.get("language", "")
            iso1 = info.get("iso639_1")
            if iso1:
                data["iso639_1"] = iso1
            if info.get("iso639_3"):
                data["iso639_3"] = info["iso639_3"]

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_source_entry(
        self,
        lang: str,
        section: str,
        description: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a human-readable source entry under SOURCE.txt."""

        path = self.source_log_path(lang)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"[{section}] {_utcnow()}",
            description.strip(),
        ]
        if extra:
            for key, value in extra.items():
                if isinstance(value, (list, set, tuple)):
                    value = ", ".join(str(v) for v in value)
                lines.append(f"{key}: {value}")
        lines.append("")  # blank line between entries
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def record_missing_script(self, lang: str, script: str, reason: str) -> None:
        """Record that a specific script could not be generated."""

        canonical = self.canonical_code(lang)
        path = self.metadata_path(canonical)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {"language": canonical, "sections": {}}

        missing = data.setdefault("missing_scripts", [])
        entry = {
            "script": script,
            "reason": reason,
            "timestamp": _utcnow(),
        }
        if not any(item.get("script") == script for item in missing):
            missing.append(entry)
        else:
            for item in missing:
                if item.get("script") == script:
                    item.update(entry)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
