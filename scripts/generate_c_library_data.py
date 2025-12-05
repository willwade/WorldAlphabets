#!/usr/bin/env python
"""Generate C library data files from JSON data.

Usage:
    python generate_c_library_data.py [OPTIONS]

Options:
    --max-tokens=N       Maximum frequency tokens per language (default: unlimited)
                         Lower values reduce binary size. 100-200 is usually sufficient
                         for language detection.

    --include-langs=xx,yy  Only include specified language codes (comma-separated).
                           Supports 2-letter (en) and 3-letter (eng) codes.
                           Default: include all languages.

    --packed-strings     Use packed string storage (single blob + offsets) instead of
                         pointer arrays. Reduces binary size by ~30-40%.

    --help               Show this help message.

Examples:
    # Full build (all languages, all tokens)
    python generate_c_library_data.py

    # Minimal build for Western European languages
    python generate_c_library_data.py --max-tokens=200 --include-langs=en,fr,de,es,pt,it

    # Compact build with packed strings
    python generate_c_library_data.py --max-tokens=200 --packed-strings
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ALPHABET_DIR = DATA_DIR / "alphabets"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
LAYOUT_DIR = DATA_DIR / "layouts"
OUT_DIR = ROOT / "c" / "generated"

# Import keyboard mappings from the runtime to avoid duplication.
sys.path.insert(0, str(ROOT / "src"))
from worldalphabets.keyboards.loader import (  # noqa: E402
    CODE_TO_HID,
    DEFAULT_LAYERS,
    SCANCODE_TO_CODE,
    VK_TO_CODE,
)


@dataclass
class GeneratorConfig:
    """Configuration for C data generation."""

    max_tokens: Optional[int] = None  # None = unlimited
    include_langs: Optional[Set[str]] = None  # None = all languages
    packed_strings: bool = False


def escape(value: str | None) -> str:
    text = value or ""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_string_array(
    name: str, values: Iterable[str], exported: bool = False
) -> str:
    """Format as traditional array of string pointers."""
    prefix = "const" if exported else "static const"
    lines = [f"{prefix} char *{name}[] = {{"]
    for val in values:
        lines.append(f'  "{escape(val)}",')
    lines.append("};")
    return "\n".join(lines)


def format_packed_strings(
    name: str, values: List[str], exported: bool = False
) -> List[str]:
    """Format as packed string blob with offset table.

    Instead of:
        const char *TOKENS[] = {"hello", "world"};

    Generates:
        static const char TOKENS_DATA[] = "hello\\0world\\0";
        static const uint16_t TOKENS_OFFSETS[] = {0, 6};
        #define TOKENS_COUNT 2
        #define TOKENS_GET(i) (&TOKENS_DATA[TOKENS_OFFSETS[i]])

    This saves ~4-8 bytes per string (pointer overhead) at the cost of
    slightly more complex access.
    """
    prefix = "const" if exported else "static const"
    lines: List[str] = []

    # Build packed data blob
    blob_parts: List[str] = []
    offsets: List[int] = []
    current_offset = 0
    for val in values:
        offsets.append(current_offset)
        escaped = escape(val)
        blob_parts.append(escaped)
        # +1 for null terminator
        current_offset += len(val.encode("utf-8")) + 1

    # Generate blob as string literal with embedded nulls
    blob_str = "\\0".join(blob_parts) + "\\0" if blob_parts else ""
    lines.append(f'{prefix} char {name}_DATA[] = "{blob_str}";')

    # Use uint16_t for offsets if possible (saves space), else uint32_t
    offset_type = "uint16_t" if current_offset < 65536 else "uint32_t"
    offset_vals = ", ".join(str(o) for o in offsets)
    lines.append(f"{prefix} {offset_type} {name}_OFFSETS[] = {{{offset_vals}}};")

    # Add convenience macros
    lines.append(f"#define {name}_COUNT {len(values)}u")
    lines.append(f"#define {name}_GET(i) (&{name}_DATA[{name}_OFFSETS[i]])")

    return lines


def lang_matches_filter(lang: str, include_langs: Optional[Set[str]]) -> bool:
    """Check if language code matches the filter set."""
    if include_langs is None:
        return True
    # Direct match
    if lang in include_langs:
        return True
    # Match base language (e.g., "en-US" matches "en")
    if "-" in lang and lang.split("-")[0] in include_langs:
        return True
    return False


def load_json_dict(path: Path) -> Dict:
    """Load JSON file that must contain a dict/object."""
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} should contain a JSON object"
    return data


def load_json_list(path: Path) -> List[Dict]:
    """Load JSON file that must contain a list of objects."""
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), f"{path} should contain a JSON array"
    return data


def build_scripts(index_data: List[dict], cfg: GeneratorConfig) -> Dict[str, List[str]]:
    scripts: Dict[str, List[str]] = {}
    for entry in index_data:
        lang = entry["language"]
        if not lang_matches_filter(lang, cfg.include_langs):
            continue
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


def build_alphabets(cfg: GeneratorConfig) -> List[dict]:
    entries: List[dict] = []
    for file in sorted(ALPHABET_DIR.glob("*.json")):
        data = load_json_dict(file)
        parts = file.stem.split("-", 1)
        lang = parts[0]
        if not lang_matches_filter(lang, cfg.include_langs):
            continue
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


def build_frequency_lists(cfg: GeneratorConfig) -> List[dict]:
    lists: List[dict] = []
    for file in sorted(FREQ_DIR.glob("*.txt")):
        code = file.stem
        if not lang_matches_filter(code, cfg.include_langs):
            continue
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
            # Apply max_tokens limit
            if cfg.max_tokens and len(tokens) >= cfg.max_tokens:
                break
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
                    "entries": [
                        {"hid": hid, "value": legend} for hid, legend in entries
                    ],
                }
            )
    return layers


def build_keyboard_layouts(cfg: GeneratorConfig) -> List[dict]:
    layouts: List[dict] = []
    for file in sorted(LAYOUT_DIR.glob("*.json")):
        data = load_json_dict(file)
        if "id" not in data or "keys" not in data:
            continue
        # Filter by language prefix in layout id (e.g., "en-us-qwerty" -> "en")
        layout_id = data["id"]
        lang_prefix = layout_id.split("-")[0] if "-" in layout_id else layout_id
        if not lang_matches_filter(lang_prefix, cfg.include_langs):
            continue
        layouts.append(
            {
                "id": layout_id,
                "name": data.get("name") or layout_id,
                "layers": build_keyboard_layers(data),
            }
        )
    return layouts


def write_data_files(cfg: GeneratorConfig) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header_path = OUT_DIR / "worldalphabets_data.h"

    index_data = load_json_list(DATA_DIR / "index.json")
    scripts_by_lang = build_scripts(index_data, cfg)
    alphabets = build_alphabets(cfg)
    freq_lists = build_frequency_lists(cfg)
    layouts = build_keyboard_layouts(cfg)
    language_codes = sorted(scripts_by_lang.keys())

    # Use #define for counts to ensure compile-time constants (required for MSVC)
    header_lines = [
        "#pragma once",
        '#include "../include/worldalphabets.h"',
        "",
        f"#define WA_LANGUAGE_CODES_COUNT {len(language_codes)}u",
        f"#define WA_SCRIPT_ENTRIES_COUNT {len(scripts_by_lang)}u",
        f"#define WA_ALPHABETS_COUNT {len(alphabets)}u",
        f"#define WA_FREQUENCY_LISTS_COUNT {len(freq_lists)}u",
        f"#define WA_KEYBOARD_LAYOUTS_COUNT {len(layouts)}u",
        "",
        "extern const char *WA_LANGUAGE_CODES[];",
        "extern const wa_script_entry WA_SCRIPT_ENTRIES[];",
        "extern const wa_alphabet WA_ALPHABETS[];",
        "extern const wa_frequency_list WA_FREQUENCY_LISTS[];",
        "extern const wa_keyboard_layout WA_KEYBOARD_LAYOUTS[];",
        "extern const char *WA_LAYOUT_IDS[];",
    ]
    header_path.write_text("\n".join(header_lines) + "\n", encoding="utf-8")

    # Split data across multiple source files to avoid MSVC internal compiler errors
    # with very large translation units

    # File 1: Languages and scripts (small)
    src1: List[str] = ['#include "worldalphabets_data.h"', ""]
    src1.append(format_string_array("WA_LANGUAGE_CODES", language_codes, exported=True))
    src1.append("")
    script_entries: List[dict] = []
    for lang in language_codes:
        scripts = scripts_by_lang[lang]
        arr_name = f"WA_SCRIPTS_{lang.replace('-', '_')}"
        src1.append(format_string_array(arr_name, scripts))
        src1.append("")
        script_entries.append({"lang": lang, "arr": arr_name, "count": len(scripts)})
    src1.append("const wa_script_entry WA_SCRIPT_ENTRIES[] = {")
    for entry in script_entries:
        src1.append(
            f'  {{ "{escape(entry["lang"])}", {entry["arr"]}, {entry["count"]}u }},'
        )
    src1.append("};")
    src1.append("")
    (OUT_DIR / "wa_data_langs.c").write_text("\n".join(src1) + "\n", encoding="utf-8")

    # File 2: Alphabets (each alphabet in its own file to avoid MSVC ICE)
    # Some alphabets (Korean, Japanese, Chinese) have >10K characters each
    for idx, alpha in enumerate(alphabets):
        src2: List[str] = ['#include "worldalphabets_data.h"', ""]
        base = f"ALPHA_{idx}"
        upper = f"{base}_UPPER"
        lower = f"{base}_LOWER"
        digits = f"{base}_DIGITS"
        freq = f"{base}_FREQ"
        src2.append(format_string_array(upper, alpha["uppercase"], exported=True))
        src2.append(format_string_array(lower, alpha["lowercase"], exported=True))
        src2.append(format_string_array(digits, alpha["digits"], exported=True))
        src2.append("const wa_freq_entry " + freq + "[] = {")
        for ch, val in alpha["frequency"].items():
            src2.append(f'  {{ "{escape(ch)}", {float(val):.8f} }},')
        src2.append("};")
        src2.append("")
        (OUT_DIR / f"wa_data_alpha_{idx}.c").write_text(
            "\n".join(src2) + "\n", encoding="utf-8"
        )

    # Alphabet table file (references the data from chunk files)
    src2_table: List[str] = ['#include "worldalphabets_data.h"', ""]
    for idx, alpha in enumerate(alphabets):
        base = f"ALPHA_{idx}"
        src2_table.append(f"extern const char *{base}_UPPER[];")
        src2_table.append(f"extern const char *{base}_LOWER[];")
        src2_table.append(f"extern const char *{base}_DIGITS[];")
        src2_table.append(f"extern const wa_freq_entry {base}_FREQ[];")
    src2_table.append("")
    src2_table.append("const wa_alphabet WA_ALPHABETS[] = {")
    for idx, alpha in enumerate(alphabets):
        base = f"ALPHA_{idx}"
        src2_table.append("  {")
        src2_table.append(f'    "{escape(alpha["language"])}",')
        src2_table.append(f'    "{escape(alpha["script"])}",')
        src2_table.append(f"    {base}_UPPER, {len(alpha['uppercase'])}u,")
        src2_table.append(f"    {base}_LOWER, {len(alpha['lowercase'])}u,")
        src2_table.append(f"    {base}_FREQ, {len(alpha['frequency'].keys())}u,")
        src2_table.append(f"    {base}_DIGITS, {len(alpha['digits'])}u,")
        src2_table.append("  },")
    src2_table.append("};")
    src2_table.append("")
    (OUT_DIR / "wa_data_alphabets_table.c").write_text(
        "\n".join(src2_table) + "\n", encoding="utf-8"
    )

    # File 3: Frequency lists (large - split into chunks)
    # Use exported=True so symbols are visible across translation units
    FREQ_CHUNK_SIZE = 15  # Smaller chunks to avoid MSVC ICE
    if cfg.packed_strings:
        # Packed strings mode: store data in blob + generate pointer array
        # This maintains API compatibility while reducing relocations
        src3: List[str] = [
            '#include "worldalphabets_data.h"',
            "#include <stdint.h>",
            "",
        ]
        for idx, freq_entry in enumerate(freq_lists):
            tokens = freq_entry["tokens"]
            name = f"WA_FREQ_{idx}_TOKENS"

            # Build packed data blob
            blob_parts: List[str] = []
            offsets: List[int] = []
            current_offset = 0
            for val in tokens:
                offsets.append(current_offset)
                blob_parts.append(escape(val))
                current_offset += len(val.encode("utf-8")) + 1

            # Generate blob
            blob_str = "\\0".join(blob_parts) + "\\0" if blob_parts else ""
            src3.append(f'static const char {name}_DATA[] = "{blob_str}";')

            # Generate pointer array pointing into blob (API compatible)
            src3.append(f"const char *{name}[] = {{")
            for off in offsets:
                src3.append(f"  {name}_DATA + {off},")
            src3.append("};")
            src3.append("")

        (OUT_DIR / "wa_data_freq_0.c").write_text(
            "\n".join(src3) + "\n", encoding="utf-8"
        )
    else:
        # Traditional mode: array of pointers, split across files
        for chunk_idx in range(0, len(freq_lists), FREQ_CHUNK_SIZE):
            chunk_end = min(chunk_idx + FREQ_CHUNK_SIZE, len(freq_lists))
            src3 = ['#include "worldalphabets_data.h"', ""]
            for idx in range(chunk_idx, chunk_end):
                freq_entry = freq_lists[idx]
                src3.append(
                    format_string_array(
                        f"WA_FREQ_{idx}_TOKENS", freq_entry["tokens"], exported=True
                    )
                )
                src3.append("")
            chunk_num = chunk_idx // FREQ_CHUNK_SIZE
            (OUT_DIR / f"wa_data_freq_{chunk_num}.c").write_text(
                "\n".join(src3) + "\n", encoding="utf-8"
            )

    # File 4: Frequency list table (references the tokens from the chunk files)
    src4: List[str] = ['#include "worldalphabets_data.h"', ""]
    for idx, freq_entry in enumerate(freq_lists):
        src4.append(f"extern const char *WA_FREQ_{idx}_TOKENS[];")
    src4.append("")
    src4.append("const wa_frequency_list WA_FREQUENCY_LISTS[] = {")
    for idx, freq_entry in enumerate(freq_lists):
        src4.append("  {")
        src4.append(f'    "{escape(freq_entry["language"])}",')
        src4.append(f'    "{escape(freq_entry["mode"])}",')
        src4.append(f"    WA_FREQ_{idx}_TOKENS, {len(freq_entry['tokens'])}u,")
        src4.append("  },")
    src4.append("};")
    src4.append("")
    (OUT_DIR / "wa_data_freq_table.c").write_text(
        "\n".join(src4) + "\n", encoding="utf-8"
    )

    # File 5: Keyboard layouts (split into chunks)
    KEYBOARD_CHUNK_SIZE = 40  # ~40 layouts per file
    for chunk_idx in range(0, len(layouts), KEYBOARD_CHUNK_SIZE):
        chunk_end = min(chunk_idx + KEYBOARD_CHUNK_SIZE, len(layouts))
        src5: List[str] = ['#include "worldalphabets_data.h"', ""]

        for idx in range(chunk_idx, chunk_end):
            layout = layouts[idx]
            layer_entries: List[dict] = []
            for layer_idx, layer in enumerate(layout["layers"]):
                entry_name = f"LAYOUT_{idx}_LAYER_{layer_idx}_ENTRIES"
                src5.append(f"const wa_keyboard_mapping {entry_name}[] = {{")
                for entry in layer["entries"]:
                    hid = int(entry["hid"])
                    val = escape(entry["value"])
                    src5.append(f'  {{ 0x{hid:02X}, "{val}" }},')
                src5.append("};")
                src5.append("")
                layer_entries.append(
                    {
                        "name": layer["name"],
                        "entry_name": entry_name,
                        "count": len(layer["entries"]),
                    }
                )
            src5.append(f"const wa_keyboard_layer LAYOUT_{idx}_LAYERS[] = {{")
            for layer in layer_entries:
                src5.append("  {")
                src5.append(f'    "{layer["name"]}",')
                src5.append(f"    {layer['entry_name']}, {layer['count']}u,")
                src5.append("  },")
            src5.append("};")
            src5.append("")

        chunk_num = chunk_idx // KEYBOARD_CHUNK_SIZE
        (OUT_DIR / f"wa_data_keyboards_{chunk_num}.c").write_text(
            "\n".join(src5) + "\n", encoding="utf-8"
        )

    # Keyboard table file
    src5_table: List[str] = ['#include "worldalphabets_data.h"', ""]
    layout_ids = [layout["id"] for layout in layouts]
    src5_table.append(format_string_array("WA_LAYOUT_IDS", layout_ids, exported=True))
    src5_table.append("")
    for idx, _layout in enumerate(layouts):
        src5_table.append(f"extern const wa_keyboard_layer LAYOUT_{idx}_LAYERS[];")
    src5_table.append("")
    src5_table.append("const wa_keyboard_layout WA_KEYBOARD_LAYOUTS[] = {")
    for idx, layout in enumerate(layouts):
        src5_table.append("  {")
        src5_table.append(f'    "{escape(layout["id"])}",')
        src5_table.append(f'    "{escape(layout["name"])}",')
        src5_table.append(f"    LAYOUT_{idx}_LAYERS, {len(layout['layers'])}u,")
        src5_table.append("  },")
    src5_table.append("};")
    src5_table.append("")
    (OUT_DIR / "wa_data_keyboards_table.c").write_text(
        "\n".join(src5_table) + "\n", encoding="utf-8"
    )

    # Count generated files
    alpha_file_count = len(alphabets)  # Each alphabet in its own file
    kbd_file_count = (len(layouts) + KEYBOARD_CHUNK_SIZE - 1) // KEYBOARD_CHUNK_SIZE
    if cfg.packed_strings:
        freq_file_count = 1  # All packed into one file
    else:
        freq_file_count = (len(freq_lists) + FREQ_CHUNK_SIZE - 1) // FREQ_CHUNK_SIZE
    file_count = (
        1  # header
        + 1  # langs
        + alpha_file_count
        + 1  # alphabet table
        + freq_file_count
        + 1  # freq table
        + kbd_file_count
        + 1  # keyboard table
    )

    # Print summary
    print(f"Generated {file_count} files to {OUT_DIR}")
    print(f"  Languages: {len(language_codes)}")
    print(f"  Alphabets: {len(alphabets)}")
    print(f"  Frequency lists: {len(freq_lists)}")
    print(f"  Keyboard layouts: {len(layouts)}")
    if cfg.max_tokens:
        print(f"  Max tokens per language: {cfg.max_tokens}")
    if cfg.include_langs:
        print(f"  Filtered to languages: {', '.join(sorted(cfg.include_langs))}")
    if cfg.packed_strings:
        print("  Using packed string storage")


def parse_args() -> GeneratorConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        metavar="N",
        help="Maximum frequency tokens per language (default: unlimited)",
    )
    parser.add_argument(
        "--include-langs",
        type=str,
        default=None,
        metavar="CODES",
        help="Comma-separated language codes to include (default: all)",
    )
    parser.add_argument(
        "--packed-strings",
        action="store_true",
        help="Use packed string storage for smaller binaries",
    )
    args = parser.parse_args()

    include_langs: Optional[Set[str]] = None
    if args.include_langs:
        include_langs = set(code.strip() for code in args.include_langs.split(","))

    return GeneratorConfig(
        max_tokens=args.max_tokens,
        include_langs=include_langs,
        packed_strings=args.packed_strings,
    )


if __name__ == "__main__":
    config = parse_args()
    write_data_files(config)
