#!/usr/bin/env python
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ALPHABET_DIR = DATA_DIR / "alphabets"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
LAYOUT_DIR = DATA_DIR / "layouts"
OUT_DIR = ROOT / "c" / "generated"

# Reuse keyboard mappings from the runtime to avoid divergence.
import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from worldalphabets.keyboards.loader import (  # type: ignore  # noqa: E402
    CODE_TO_HID,
    DEFAULT_LAYERS,
    SCANCODE_TO_CODE,
    VK_TO_CODE,
)


def escape(value: str | None) -> str:
    text = value or ""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_string_array(name: str, values: Iterable[str], exported: bool = False) -> str:
    prefix = "const" if exported else "static const"
    lines = [f"{prefix} char *{name}[] = {{"]
    for val in values:
        lines.append(f'  "{escape(val)}",')
    lines.append("};")
    return "\n".join(lines)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_scripts(index_data: List[dict]) -> Dict[str, List[str]]:
    scripts: Dict[str, List[str]] = {}
    for entry in index_data:
        lang = entry["language"]
        scripts.setdefault(lang, [])
        candidates = []
        if entry.get("script"):
            candidates.append(entry["script"])
        if entry.get("scripts"):
            candidates.extend(entry["scripts"])
        for s in candidates:
            if s not in scripts[lang]:
                scripts[lang].append(s)
    for lang in scripts:
        scripts[lang].sort()
    return scripts


def build_alphabets() -> List[dict]:
    entries: List[dict] = []
    for file in sorted(ALPHABET_DIR.glob("*.json")):
        data = load_json(file)
        parts = file.stem.split("-", 1)
        lang = parts[0]
        script = parts[1] if len(parts) > 1 else data.get("script", "")
        entries.append(
            {
                "language": lang,
                "script": script,
                "uppercase": data.get("uppercase", []),
                "lowercase": data.get("lowercase", []),
                "digits": data.get("digits", []),
                "frequency": data.get("frequency", {}),
            }
        )
    return entries


def build_frequency_lists() -> List[dict]:
    lists: List[dict] = []
    for file in sorted(FREQ_DIR.glob("*.txt")):
        code = file.stem
        mode = "word"
        tokens: List[str] = []
        for line in file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if not tokens and stripped.startswith("#"):
                if "bigram" in stripped.lower():
                    mode = "bigram"
                continue
            tokens.append(stripped)
        lists.append({"language": code, "mode": mode, "tokens": tokens})
    return lists


def resolve_dom_code(key: dict) -> str | None:
    if key.get("pos"):
        return key["pos"]
    if key.get("vk") and key["vk"] in VK_TO_CODE:
        return VK_TO_CODE[key["vk"]]
    if key.get("sc"):
        sc = key["sc"].upper()
        if sc in SCANCODE_TO_CODE:
            return SCANCODE_TO_CODE[sc]
    return None


def build_keyboard_layers(layout: dict) -> List[dict]:
    layers: List[dict] = []
    for layer in DEFAULT_LAYERS:
        entries: List[Tuple[int, str]] = []
        for key in layout.get("keys", []):
            legends = key.get("legends") or {}
            legend = legends.get(layer)
            if not legend:
                continue
            dom_code = resolve_dom_code(key)
            if dom_code is None:
                continue
            hid = CODE_TO_HID.get(dom_code)
            if hid is None:
                continue
            entries.append((hid, legend))
        if entries:
            entries.sort(key=lambda item: item[0])
            layers.append(
                {
                    "name": layer,
                    "entries": [{"hid": hid, "value": legend} for hid, legend in entries],
                }
            )
    return layers


def build_keyboard_layouts() -> List[dict]:
    layouts: List[dict] = []
    for file in sorted(LAYOUT_DIR.glob("*.json")):
        data = load_json(file)
        if "id" not in data or "keys" not in data:
            continue
        layouts.append(
            {
                "id": data["id"],
                "name": data.get("name") or data["id"],
                "layers": build_keyboard_layers(data),
            }
        )
    return layouts


def write_data_files() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header_path = OUT_DIR / "worldalphabets_data.h"
    source_path = OUT_DIR / "worldalphabets_data.c"

    index_data = load_json(DATA_DIR / "index.json")
    scripts_by_lang = build_scripts(index_data)
    alphabets = build_alphabets()
    freq_lists = build_frequency_lists()
    layouts = build_keyboard_layouts()
    language_codes = sorted(scripts_by_lang.keys())

    header_lines = [
        "#pragma once",
        '#include "../include/worldalphabets.h"',
        "",
        "extern const char *WA_LANGUAGE_CODES[];",
        "extern const size_t WA_LANGUAGE_CODES_COUNT;",
        "extern const wa_script_entry WA_SCRIPT_ENTRIES[];",
        "extern const size_t WA_SCRIPT_ENTRIES_COUNT;",
        "extern const wa_alphabet WA_ALPHABETS[];",
        "extern const size_t WA_ALPHABETS_COUNT;",
        "extern const wa_frequency_list WA_FREQUENCY_LISTS[];",
        "extern const size_t WA_FREQUENCY_LISTS_COUNT;",
        "extern const wa_keyboard_layout WA_KEYBOARD_LAYOUTS[];",
        "extern const size_t WA_KEYBOARD_LAYOUTS_COUNT;",
        "extern const char *WA_LAYOUT_IDS[];",
    ]
    header_path.write_text("\n".join(header_lines) + "\n", encoding="utf-8")

    src: List[str] = []
    src.append('#include "worldalphabets_data.h"')
    src.append("")
    src.append(format_string_array("WA_LANGUAGE_CODES", language_codes, exported=True))
    src.append(f"const size_t WA_LANGUAGE_CODES_COUNT = {len(language_codes)}u;")
    src.append("")

    script_entries: List[dict] = []
    for lang in language_codes:
        scripts = scripts_by_lang[lang]
        arr_name = f"WA_SCRIPTS_{lang.replace('-', '_')}"
        src.append(format_string_array(arr_name, scripts))
        src.append("")
        script_entries.append(
            {"lang": lang, "arr": arr_name, "count": len(scripts)}
        )
    src.append("const wa_script_entry WA_SCRIPT_ENTRIES[] = {")
    for entry in script_entries:
        src.append(
            f'  {{ "{escape(entry["lang"])}", {entry["arr"]}, {entry["count"]}u }},'
        )
    src.append("};")
    src.append(f"const size_t WA_SCRIPT_ENTRIES_COUNT = {len(script_entries)}u;")
    src.append("")

    upper_names: List[str] = []
    lower_names: List[str] = []
    digit_names: List[str] = []
    freq_names: List[str] = []

    for idx, alpha in enumerate(alphabets):
        base = f"ALPHA_{idx}"
        upper = f"{base}_UPPER"
        lower = f"{base}_LOWER"
        digits = f"{base}_DIGITS"
        freq = f"{base}_FREQ"
        upper_names.append(upper)
        lower_names.append(lower)
        digit_names.append(digits)
        freq_names.append(freq)

        src.append(format_string_array(upper, alpha["uppercase"]))
        src.append(format_string_array(lower, alpha["lowercase"]))
        src.append(format_string_array(digits, alpha["digits"]))
        src.append("static const wa_freq_entry " + freq + "[] = {")
        for ch, val in alpha["frequency"].items():
            src.append(f'  {{ "{escape(ch)}", {float(val):.8f} }},')
        src.append("};")
        src.append("")

    src.append("const wa_alphabet WA_ALPHABETS[] = {")
    for idx, alpha in enumerate(alphabets):
        src.append("  {")
        src.append(f'    "{escape(alpha["language"])}",')
        src.append(f'    "{escape(alpha["script"])}",')
        src.append(f"    {upper_names[idx]}, {len(alpha['uppercase'])}u,")
        src.append(f"    {lower_names[idx]}, {len(alpha['lowercase'])}u,")
        src.append(
            f"    {freq_names[idx]}, {len(alpha['frequency'].keys())}u,"
        )
        src.append(f"    {digit_names[idx]}, {len(alpha['digits'])}u,")
        src.append("  },")
    src.append("};")
    src.append(f"const size_t WA_ALPHABETS_COUNT = {len(alphabets)}u;")
    src.append("")

    for idx, freq in enumerate(freq_lists):
        src.append(format_string_array(f"WA_FREQ_{idx}_TOKENS", freq["tokens"]))
        src.append("")
    src.append("const wa_frequency_list WA_FREQUENCY_LISTS[] = {")
    for idx, freq in enumerate(freq_lists):
        src.append("  {")
        src.append(f'    "{escape(freq["language"])}",')
        src.append(f'    "{escape(freq["mode"])}",')
        src.append(f"    WA_FREQ_{idx}_TOKENS, {len(freq['tokens'])}u,")
        src.append("  },")
    src.append("};")
    src.append(f"const size_t WA_FREQUENCY_LISTS_COUNT = {len(freq_lists)}u;")
    src.append("")

    layout_ids = [layout["id"] for layout in layouts]
    src.append(format_string_array("WA_LAYOUT_IDS", layout_ids, exported=True))
    src.append("")

    for idx, layout in enumerate(layouts):
        layer_entries: List[dict] = []
        for layer_idx, layer in enumerate(layout["layers"]):
            entry_name = f"LAYOUT_{idx}_LAYER_{layer_idx}_ENTRIES"
            src.append(f"static const wa_keyboard_mapping {entry_name}[] = {{")
            for entry in layer["entries"]:
                src.append(
                    f'  {{ 0x{int(entry["hid"]):02X}, "{escape(entry["value"])}" }},'
                )
            src.append("};")
            src.append("")
            layer_entries.append(
                {
                    "name": layer["name"],
                    "entry_name": entry_name,
                    "count": len(layer["entries"]),
                }
            )

        src.append(f"static const wa_keyboard_layer LAYOUT_{idx}_LAYERS[] = {{")
        for layer in layer_entries:
            src.append("  {")
            src.append(f'    "{layer["name"]}",')
            src.append(f"    {layer['entry_name']}, {layer['count']}u,")
            src.append("  },")
        src.append("};")
        src.append("")

    src.append("const wa_keyboard_layout WA_KEYBOARD_LAYOUTS[] = {")
    for idx, layout in enumerate(layouts):
        src.append("  {")
        src.append(f'    "{escape(layout["id"])}",')
        src.append(f'    "{escape(layout["name"])}",')
        src.append(f"    LAYOUT_{idx}_LAYERS, {len(layout['layers'])}u,")
        src.append("  },")
    src.append("};")
    src.append(f"const size_t WA_KEYBOARD_LAYOUTS_COUNT = {len(layouts)}u;")

    source_path.write_text("\n".join(src) + "\n", encoding="utf-8")
    print(f"Wrote {header_path} and {source_path}")


if __name__ == "__main__":
    write_data_files()
