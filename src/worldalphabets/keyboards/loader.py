import json
from importlib.resources import files, as_file
from typing import Dict, Iterable, List
from pathlib import Path

from ..models.keyboard import KeyboardLayout, KeyEntry

with as_file(files("worldalphabets")) as p:
    _PACKAGE_PATH = Path(p)
DATA_DIR = _PACKAGE_PATH.parent.parent / "data"
LAYOUTS_DIR = DATA_DIR / "layouts"

def get_available_layouts() -> List[str]:
    """
    Returns a list of available keyboard layout IDs.
    """
    if not LAYOUTS_DIR.is_dir():
        return []
    return sorted([p.name.replace(".json","") for p in LAYOUTS_DIR.iterdir() if p.name.endswith(".json")])

def load_keyboard(layout_id: str) -> KeyboardLayout:
    """
    Loads a keyboard layout by its ID.
    """
    layout_path = LAYOUTS_DIR / f"{layout_id}.json"
    try:
        with open(layout_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return KeyboardLayout.model_validate(data)
    except FileNotFoundError:
        raise ValueError(f"Keyboard layout '{layout_id}' not found.")


DEFAULT_LAYERS: tuple[str, ...] = (
    "base",
    "shift",
    "caps",
    "altgr",
    "shift_altgr",
    "ctrl",
    "alt",
)


def extract_layers(
    layout: KeyboardLayout, layers: Iterable[str] | None = None
) -> Dict[str, Dict[str, str]]:
    """Return a mapping of layer name to key legends for the given layout."""

    result: Dict[str, Dict[str, str]] = {}
    target_layers = list(layers) if layers is not None else list(DEFAULT_LAYERS)

    for layer in target_layers:
        layer_values: Dict[str, str] = {}
        for key in layout.keys:
            if key.legends is None:
                continue
            value = getattr(key.legends, layer, None)
            if not value:
                continue
            pos = key.pos or key.vk or key.sc
            if pos:
                layer_values[str(pos)] = value
        if layer_values:
            result[layer] = layer_values

    return result


def _sanitize_identifier(value: str | None) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value or "")
    if not cleaned:
        return "layout"
    if cleaned[0].isdigit():
        return f"layout_{cleaned}"
    return cleaned


def _escape_c_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = (
        escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    )
    return escaped


SCANCODE_TO_CODE: Dict[str, str] = {
    "01": "Escape",
    "02": "Digit1",
    "03": "Digit2",
    "04": "Digit3",
    "05": "Digit4",
    "06": "Digit5",
    "07": "Digit6",
    "08": "Digit7",
    "09": "Digit8",
    "0A": "Digit9",
    "0B": "Digit0",
    "0C": "Minus",
    "0D": "Equal",
    "0E": "Backspace",
    "0F": "Tab",
    "10": "KeyQ",
    "11": "KeyW",
    "12": "KeyE",
    "13": "KeyR",
    "14": "KeyT",
    "15": "KeyY",
    "16": "KeyU",
    "17": "KeyI",
    "18": "KeyO",
    "19": "KeyP",
    "1A": "BracketLeft",
    "1B": "BracketRight",
    "1C": "Enter",
    "1D": "ControlLeft",
    "1E": "KeyA",
    "1F": "KeyS",
    "20": "KeyD",
    "21": "KeyF",
    "22": "KeyG",
    "23": "KeyH",
    "24": "KeyJ",
    "25": "KeyK",
    "26": "KeyL",
    "27": "Semicolon",
    "28": "Quote",
    "29": "Backquote",
    "2A": "ShiftLeft",
    "2B": "Backslash",
    "2C": "KeyZ",
    "2D": "KeyX",
    "2E": "KeyC",
    "2F": "KeyV",
    "30": "KeyB",
    "31": "KeyN",
    "32": "KeyM",
    "33": "Comma",
    "34": "Period",
    "35": "Slash",
    "36": "ShiftRight",
    "37": "NumpadMultiply",
    "38": "AltLeft",
    "39": "Space",
    "3A": "CapsLock",
    "3B": "F1",
    "3C": "F2",
    "3D": "F3",
    "3E": "F4",
    "3F": "F5",
    "40": "F6",
    "41": "F7",
    "42": "F8",
    "43": "F9",
    "44": "F10",
    "45": "NumLock",
    "46": "ScrollLock",
    "47": "Numpad7",
    "48": "Numpad8",
    "49": "Numpad9",
    "4A": "NumpadSubtract",
    "4B": "Numpad4",
    "4C": "Numpad5",
    "4D": "Numpad6",
    "4E": "NumpadAdd",
    "4F": "Numpad1",
    "50": "Numpad2",
    "51": "Numpad3",
    "52": "Numpad0",
    "53": "NumpadDecimal",
    "56": "IntlBackslash",
    "57": "F11",
    "58": "F12",
    "E010": "MediaPreviousTrack",
    "E019": "MediaNextTrack",
    "E01C": "NumpadEnter",
    "E01D": "ControlRight",
    "E020": "VolumeMute",
    "E021": "LaunchApp2",
    "E022": "MediaPlayPause",
    "E024": "MediaStop",
    "E02E": "VolumeDown",
    "E030": "VolumeUp",
    "E032": "BrowserHome",
    "E035": "NumpadDivide",
    "E037": "PrintScreen",
    "E038": "AltRight",
    "E046": "Pause",
    "E047": "Home",
    "E048": "ArrowUp",
    "E049": "PageUp",
    "E04B": "ArrowLeft",
    "E04D": "ArrowRight",
    "E04F": "End",
    "E050": "ArrowDown",
    "E051": "PageDown",
    "E052": "Insert",
    "E053": "Delete",
    "E05B": "MetaLeft",
    "E05C": "MetaRight",
    "E05D": "ContextMenu",
    "E05F": "Sleep",
    "E065": "BrowserSearch",
    "E066": "BrowserFavorites",
    "E067": "BrowserRefresh",
    "E068": "BrowserStop",
    "E069": "BrowserForward",
    "E06A": "BrowserBack",
    "E06B": "LaunchApp1",
    "E06C": "LaunchMail",
    "E06D": "MediaSelect",
    "E11D": "Pause",
}

VK_TO_CODE: Dict[str, str] = {
    "VK_SPACE": "Space",
    "VK_ADD": "NumpadAdd",
    "VK_SUBTRACT": "NumpadSubtract",
    "VK_MULTIPLY": "NumpadMultiply",
    "VK_DIVIDE": "NumpadDivide",
    "VK_ABNT_C1": "IntlBackslash",
    "VK_ABNT_C2": "NumpadDecimal",
    "VK_OEM_1": "Semicolon",
    "VK_OEM_PLUS": "Equal",
    "VK_OEM_COMMA": "Comma",
    "VK_OEM_MINUS": "Minus",
    "VK_OEM_PERIOD": "Period",
    "VK_OEM_2": "Slash",
    "VK_OEM_3": "Backquote",
    "VK_OEM_4": "BracketLeft",
    "VK_OEM_5": "Backslash",
    "VK_OEM_6": "BracketRight",
    "VK_OEM_7": "Quote",
    "VK_OEM_8": "IntlBackslash",
    "VK_OEM_102": "IntlBackslash",
}

CODE_TO_HID: Dict[str, int] = {
    "Escape": 0x29,
    "Backspace": 0x2A,
    "Tab": 0x2B,
    "Space": 0x2C,
    "Minus": 0x2D,
    "Equal": 0x2E,
    "BracketLeft": 0x2F,
    "BracketRight": 0x30,
    "Backslash": 0x31,
    "NonUSHash": 0x32,
    "Semicolon": 0x33,
    "Quote": 0x34,
    "Backquote": 0x35,
    "Comma": 0x36,
    "Period": 0x37,
    "Slash": 0x38,
    "CapsLock": 0x39,
    "Enter": 0x28,
    "IntlBackslash": 0x64,
    "NumpadDivide": 0x54,
    "NumpadMultiply": 0x55,
    "NumpadSubtract": 0x56,
    "NumpadAdd": 0x57,
    "NumpadEnter": 0x58,
    "Numpad1": 0x59,
    "Numpad2": 0x5A,
    "Numpad3": 0x5B,
    "Numpad4": 0x5C,
    "Numpad5": 0x5D,
    "Numpad6": 0x5E,
    "Numpad7": 0x5F,
    "Numpad8": 0x60,
    "Numpad9": 0x61,
    "Numpad0": 0x62,
    "NumpadDecimal": 0x63,
}

for i in range(26):
    CODE_TO_HID[f"Key{chr(65 + i)}"] = 0x04 + i
for i in range(1, 10):
    CODE_TO_HID[f"Digit{i}"] = 0x1D + i
CODE_TO_HID["Digit0"] = 0x27


def _normalize_keycode(keycode: str | int | None) -> int | None:
    if keycode is None:
        return None
    if isinstance(keycode, int):
        return keycode
    raw = keycode.strip()
    if raw.startswith("0x") or raw.startswith("0X"):
        try:
            return int(raw, 16)
        except ValueError:
            return None
    if raw.isdigit():
        return int(raw, 10)
    sc = raw.upper()
    if sc in SCANCODE_TO_CODE:
        dom = SCANCODE_TO_CODE[sc]
        return CODE_TO_HID.get(dom)
    if raw in VK_TO_CODE:
        dom = VK_TO_CODE[raw]
        return CODE_TO_HID.get(dom)
    return CODE_TO_HID.get(raw)


def find_layouts_by_keycode(keycode: str | int, layer: str = "base") -> list[dict]:
    """Return layouts matching a given keycode (DOM code, VK, scan, or HID)."""

    hid = _normalize_keycode(keycode)
    if hid is None:
        return []

    matches: list[dict] = []
    for layout_id in get_available_layouts():
        try:
            kb = load_keyboard(layout_id)
        except ValueError:
            continue
        for key in kb.keys:
            legends = key.legends
            legend = getattr(legends, layer, None)
            if not legend:
                continue
            dom_code = _resolve_dom_code(key)
            if dom_code is None:
                continue
            usage = _code_to_hid_usage(dom_code)
            if usage is None:
                continue
            if usage == hid:
                matches.append(
                    {"id": kb.id, "name": kb.name, "legend": legend, "layer": layer}
                )
                break
    return matches


def _resolve_dom_code(key: KeyEntry) -> str | None:
    if key.pos:
        return key.pos
    if key.vk and key.vk in VK_TO_CODE:
        return VK_TO_CODE[key.vk]
    if key.sc:
        sc_key = key.sc.upper()
        return SCANCODE_TO_CODE.get(sc_key)
    return None


def _code_to_hid_usage(code: str | None) -> int | None:
    if code is None:
        return None
    return CODE_TO_HID.get(code)


def _build_layer_entries(
    layout: KeyboardLayout, layers: Iterable[str]
) -> list[tuple[str, list[tuple[int, str]]]]:
    built: list[tuple[str, list[tuple[int, str]]]] = []
    for layer in layers:
        entries: Dict[int, str] = {}
        for key in layout.keys:
            if key.legends is None:
                continue
            legend = getattr(key.legends, layer, None)
            if not legend:
                continue
            dom_code = _resolve_dom_code(key)
            if dom_code is None:
                raise ValueError(
                    f"Unable to resolve key code for layer '{layer}' in layout '{layout.id}'."
                )
            usage = _code_to_hid_usage(dom_code)
            if usage is None:
                raise ValueError(
                    f"Unsupported key code '{dom_code}' in layout '{layout.id}'."
                )
            entries[usage] = legend
        if entries:
            ordered = sorted(entries.items())
            built.append((layer, ordered))
    return built


def generate_c_header(
    layout_id: str,
    layers: Iterable[str] | None = None,
    guard: bool = True,
    symbol_name: str | None = None,
) -> str:
    """Return a C header representation of a keyboard layout."""

    layout = load_keyboard(layout_id)
    target_layers = list(layers) if layers is not None else list(DEFAULT_LAYERS)
    layer_entries = _build_layer_entries(layout, target_layers)
    if not layer_entries:
        raise ValueError(f"No legends found for layout '{layout.id}'.")

    symbol_base = _sanitize_identifier(symbol_name or f"layout_{layout.id}")
    guard_name = f"{symbol_base.upper()}_H"

    lines: List[str] = []
    if guard:
        lines.extend([f"#ifndef {guard_name}", f"#define {guard_name}", ""])

    lines.extend(
        [
            "#include <stddef.h>",
            "#include <stdint.h>",
            "",
            "typedef struct {",
            "  uint16_t keycode;",
            "  const char *value;",
            "} keyboard_mapping_t;",
            "",
            "typedef struct {",
            "  const char *name;",
            "  const keyboard_mapping_t *entries;",
            "  size_t entry_count;",
            "} keyboard_layer_t;",
            "",
            "typedef struct {",
            "  const char *name;",
            "  const char *display_name;",
            "  const keyboard_layer_t *layers;",
            "  size_t layer_count;",
            "} keyboard_layout_t;",
            "",
        ]
    )

    for layer_name, entries in layer_entries:
        entry_name = f"{symbol_base}_{layer_name}_entries"
        lines.append(f"static const keyboard_mapping_t {entry_name}[] = {{")
        for usage, value in entries:
            lines.append(f'  {{ 0x{usage:02X}, "{_escape_c_string(value)}" }},')
        lines.append("};")
        lines.append("")
        lines.append(f"static const keyboard_layer_t {symbol_base}_{layer_name} = {{")
        lines.append(f'  .name = "{layer_name}",')
        lines.append(f"  .entries = {entry_name},")
        lines.append(f"  .entry_count = {len(entries)}u,")
        lines.append("};")
        lines.append("")

    lines.append(f"static const keyboard_layer_t {symbol_base}_layers[] = {{")
    for layer_name, _ in layer_entries:
        lines.append(f"  {symbol_base}_{layer_name},")
    lines.append("};")
    lines.append("")
    lines.append(f"static const keyboard_layout_t {symbol_base} = {{")
    lines.append(f'  .name = "{_escape_c_string(layout.id)}",')
    display_name = layout.name or layout.id
    lines.append(f'  .display_name = "{_escape_c_string(display_name)}",')
    lines.append(f"  .layers = {symbol_base}_layers,")
    lines.append(f"  .layer_count = {len(layer_entries)}u,")
    lines.append("};")
    if guard:
        lines.append("")
        lines.append(f"#endif /* {guard_name} */")

    return "\n".join(lines)
