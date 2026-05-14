"""Backfill USB HID keycode into existing keyboard layout JSON files.

Usage:
    uv run python scripts/add_hid_to_layouts.py
    uv run python scripts/add_hid_to_layouts.py --dry-run
"""

import json
import sys
from pathlib import Path

LAYOUTS_DIR = Path(__file__).resolve().parent.parent / "data" / "layouts"

SCANCODE_TO_CODE: dict[str, str] = {
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

VK_TO_CODE: dict[str, str] = {
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

CODE_TO_HID: dict[str, str] = {
    "Escape": "0x29",
    "Backspace": "0x2A",
    "Tab": "0x2B",
    "Space": "0x2C",
    "Minus": "0x2D",
    "Equal": "0x2E",
    "BracketLeft": "0x2F",
    "BracketRight": "0x30",
    "Backslash": "0x31",
    "NonUSHash": "0x32",
    "Semicolon": "0x33",
    "Quote": "0x34",
    "Backquote": "0x35",
    "Comma": "0x36",
    "Period": "0x37",
    "Slash": "0x38",
    "CapsLock": "0x39",
    "Enter": "0x28",
    "IntlBackslash": "0x64",
    "NumpadDivide": "0x54",
    "NumpadMultiply": "0x55",
    "NumpadSubtract": "0x56",
    "NumpadAdd": "0x57",
    "NumpadEnter": "0x58",
    "Numpad1": "0x59",
    "Numpad2": "0x5A",
    "Numpad3": "0x5B",
    "Numpad4": "0x5C",
    "Numpad5": "0x5D",
    "Numpad6": "0x5E",
    "Numpad7": "0x5F",
    "Numpad8": "0x60",
    "Numpad9": "0x61",
    "Numpad0": "0x62",
    "NumpadDecimal": "0x63",
    "F1": "0x3A",
    "F2": "0x3B",
    "F3": "0x3C",
    "F4": "0x3D",
    "F5": "0x3E",
    "F6": "0x3F",
    "F7": "0x40",
    "F8": "0x41",
    "F9": "0x42",
    "F10": "0x43",
    "F11": "0x44",
    "F12": "0x45",
    "PrintScreen": "0x46",
    "ScrollLock": "0x47",
    "Pause": "0x48",
    "Insert": "0x49",
    "Home": "0x4A",
    "PageUp": "0x4B",
    "Delete": "0x4C",
    "End": "0x4D",
    "PageDown": "0x4E",
    "ArrowRight": "0x4F",
    "ArrowLeft": "0x50",
    "ArrowDown": "0x51",
    "ArrowUp": "0x52",
    "NumLock": "0x53",
    "ControlLeft": "0xE0",
    "ShiftLeft": "0xE1",
    "AltLeft": "0xE2",
    "MetaLeft": "0xE3",
    "ControlRight": "0xE4",
    "ShiftRight": "0xE5",
    "AltRight": "0xE6",
    "MetaRight": "0xE7",
}

for _i in range(26):
    CODE_TO_HID[f"Key{chr(65 + _i)}"] = f"0x{0x04 + _i:02X}"
for _i in range(1, 10):
    CODE_TO_HID[f"Digit{_i}"] = f"0x{0x1D + _i:02X}"
CODE_TO_HID["Digit0"] = "0x27"


def resolve_hid(pos: str | None, vk: str | None, sc: str | None) -> str | None:
    if pos:
        return CODE_TO_HID.get(pos)
    if vk and vk in VK_TO_CODE:
        return CODE_TO_HID.get(VK_TO_CODE[vk])
    if sc:
        dom = SCANCODE_TO_CODE.get(sc.upper())
        if dom:
            return CODE_TO_HID.get(dom)
    return None


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    files = sorted(LAYOUTS_DIR.glob("*.json"))
    updated = 0
    skipped = 0

    for fpath in files:
        if fpath.name == "index.json":
            continue
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        keys_with_hid = 0
        keys_total = 0
        for key in data.get("keys", []):
            keys_total += 1
            hid = resolve_hid(key.get("pos"), key.get("vk"), key.get("sc"))
            if hid is not None:
                key["hid"] = hid
                keys_with_hid += 1
                changed = True
            else:
                key.pop("hid", None)

        if changed:
            updated += 1
            if not dry_run:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write("\n")
            print(
                f"  {'[DRY] ' if dry_run else ''}{fpath.name}: "
                f"{keys_with_hid}/{keys_total} keys got hid"
            )
        else:
            skipped += 1

    print(f"\n{'Would update' if dry_run else 'Updated'}: {updated}, skipped: {skipped}")


if __name__ == "__main__":
    main()
