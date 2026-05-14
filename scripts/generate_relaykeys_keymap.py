"""
Generate RelayKeys keymap JSON files from WorldAlphabets keyboard layouts.

Usage:
    uv run python generate_keymap.py                    # Generate all
    uv run python generate_keymap.py en-us              # Generate one
    uv run python generate_keymap.py en-us de-DE-qwertz fr-fr-azerty

Output goes to ../../keymaps/ in RelayKeys-compatible format:
    { "a": ["A", []], "@": ["2", ["LSHIFT"]], ... }

This is a dev tool — the generated JSON files are embedded in the Go binary
at build time. No runtime dependency on WorldAlphabets.
"""

import json
import os
import sys

LAYOUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "layouts")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "RelayKeys", "keymaps")

VK_TO_HID = {
    "VK_1": "1", "VK_2": "2", "VK_3": "3", "VK_4": "4", "VK_5": "5",
    "VK_6": "6", "VK_7": "7", "VK_8": "8", "VK_9": "9", "VK_0": "0",
    "VK_Q": "Q", "VK_W": "W", "VK_E": "E", "VK_R": "R", "VK_T": "T",
    "VK_Y": "Y", "VK_U": "U", "VK_I": "I", "VK_O": "O", "VK_P": "P",
    "VK_A": "A", "VK_S": "S", "VK_D": "D", "VK_F": "F", "VK_G": "G",
    "VK_H": "H", "VK_J": "J", "VK_K": "K", "VK_L": "L",
    "VK_Z": "Z", "VK_X": "X", "VK_C": "C", "VK_V": "V",
    "VK_B": "B", "VK_N": "N", "VK_M": "M",
    "VK_OEM_MINUS": "MINUS", "VK_OEM_PLUS": "EQUALS",
    "VK_OEM_4": "LEFTBRACKET", "VK_OEM_6": "RIGHTBRACKET",
    "VK_OEM_5": "BACKSLASH", "VK_OEM_1": "SEMICOLON",
    "VK_OEM_7": "QUOTE", "VK_OEM_3": "BACKQUOTE",
    "VK_OEM_COMMA": "COMMA", "VK_OEM_PERIOD": "PERIOD",
    "VK_OEM_2": "SLASH",
    "VK_OEM_102": "NON-US-BACKSLASH",
    "VK_SPACE": "SPACE", "VK_RETURN": "ENTER",
    "VK_TAB": "TAB", "VK_BACK": "BACKSPACE",
    "VK_DELETE": "DELETE", "VK_ESCAPE": "ESCAPE",
    "VK_INSERT": "INSERT", "VK_HOME": "HOME",
    "VK_END": "END", "VK_PRIOR": "PAGEUP",
    "VK_NEXT": "PAGEDOWN",
    "VK_UP": "UP", "VK_DOWN": "DOWN",
    "VK_LEFT": "LEFT", "VK_RIGHT": "RIGHT",
    "VK_F1": "F1", "VK_F2": "F2", "VK_F3": "F3", "VK_F4": "F4",
    "VK_F5": "F5", "VK_F6": "F6", "VK_F7": "F7", "VK_F8": "F8",
    "VK_F9": "F9", "VK_F10": "F10", "VK_F11": "F11", "VK_F12": "F12",
    "VK_NUMPAD0": "KP0", "VK_NUMPAD1": "KP1", "VK_NUMPAD2": "KP2",
    "VK_NUMPAD3": "KP3", "VK_NUMPAD4": "KP4", "VK_NUMPAD5": "KP5",
    "VK_NUMPAD6": "KP6", "VK_NUMPAD7": "KP7", "VK_NUMPAD8": "KP8",
    "VK_NUMPAD9": "KP9",
    "VK_MULTIPLY": "KP_MULTIPLY", "VK_ADD": "KP_PLUS",
    "VK_SUBTRACT": "KP_MINUS", "VK_DIVIDE": "KP_DIVIDE",
    "VK_DECIMAL": "KP_PERIOD",
    "VK_CAPITAL": "CAPSLOCK", "VK_NUMLOCK": "NUMLOCK",
    "VK_SCROLL": "SCROLLOCK",
    "VK_SNAPSHOT": "PRINTSCREEN", "VK_PAUSE": "PAUSE",
    "VK_APPS": "APP",
}

NUMPAD_VKS = {
    "VK_NUMPAD0", "VK_NUMPAD1", "VK_NUMPAD2", "VK_NUMPAD3", "VK_NUMPAD4",
    "VK_NUMPAD5", "VK_NUMPAD6", "VK_NUMPAD7", "VK_NUMPAD8", "VK_NUMPAD9",
    "VK_MULTIPLY", "VK_ADD", "VK_SUBTRACT", "VK_DIVIDE", "VK_DECIMAL",
    "VK_CLEAR",
}

LAYER_MODS = {
    "base": [],
    "shift": ["LSHIFT"],
    "caps": ["CAPSLOCK"],
    "altgr": ["RALT"],
    "shift_altgr": ["LSHIFT", "RALT"],
}

# Friendly names for output files
FRIENDLY_NAMES = {
    "en-us": "us_keymap.json",
    "en-gb": "uk_keymap.json",
    "en-GB-qwerty": "uk_keymap.json",
    "de-DE-qwertz": "de_keymap.json",
    "fr-french-standard-azerty": "fr_azerty_keymap.json",
    "es-spanish": "es_qwerty_keymap.json",
    "it-italian": "it_qwerty_keymap.json",
    "de-swiss-german": "ch_german_keymap.json",
    "fr-belgian-french": "be_french_keymap.json",
    "es-latin-american": "es_latin_keymap.json",
    "pt-brazilian-abnt2": "pt_br_keymap.json",
    "pl-polish-214": "pl_keymap.json",
    "nl-dutch": "nl_keymap.json",
    "sv-swedish": "sv_keymap.json",
    "nb-norwegian": "nb_keymap.json",
    "da-danish": "da_keymap.json",
    "fi-finnish": "fi_keymap.json",
    "cs-czech": "cs_keymap.json",
    "hu-hungarian": "hu_keymap.json",
    "tr-turkish-q": "tr_keymap.json",
    "ru-russian": "ru_keymap.json",
    "ar-arabic-101": "ar_keymap.json",
    "el-greek": "el_keymap.json",
    "he-hebrew": "he_keymap.json",
    "ja-japanese": "ja_keymap.json",
    "ko-korean": "ko_keymap.json",
    "zh-chinese-simplified": "zh_cn_keymap.json",
}


def load_layout(layout_id):
    path = os.path.join(LAYOUTS_DIR, f"{layout_id}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def layout_to_keymap(layout):
    keymap = {}
    numpad_keymap = {}

    for key in layout["keys"]:
        vk = key.get("vk", "")
        hid_name = VK_TO_HID.get(vk)
        if hid_name is None:
            continue

        is_numpad = vk in NUMPAD_VKS
        target = numpad_keymap if is_numpad else keymap

        legends = key.get("legends", {})

        for layer, mods in LAYER_MODS.items():
            char = legends.get(layer)
            if char is None or char == "":
                continue
            if isinstance(char, str) and len(char) != 1:
                continue

            if char in target:
                continue

            target[char] = [hid_name, mods]

    for char, entry in numpad_keymap.items():
        if char not in keymap:
            keymap[char] = entry

    keymap["\t"] = ["TAB", []]
    keymap["\n"] = ["ENTER", []]
    keymap["\r"] = [None, None]

    return {k: v for k, v in keymap.items() if v[0] is not None}


def find_layout_file(query):
    if os.path.exists(os.path.join(LAYOUTS_DIR, f"{query}.json")):
        return query

    matches = []
    for f in os.listdir(LAYOUTS_DIR):
        if f.endswith(".json"):
            lid = f[:-5]
            if lid.startswith(query) or query in lid:
                matches.append(lid)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        for m in matches:
            if m == query:
                return m
        print(f"Ambiguous '{query}', matches: {matches[:5]}")
        return None
    return None


def get_output_name(layout_id):
    if layout_id in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[layout_id]
    return f"{layout_id}_keymap.json"


def generate_one(layout_id):
    actual_id = find_layout_file(layout_id)
    if actual_id is None:
        print(f"  SKIP: layout '{layout_id}' not found")
        return None

    layout = load_layout(actual_id)
    keymap = layout_to_keymap(layout)

    if not keymap:
        print(f"  SKIP: {actual_id} — no character mappings")
        return None

    out_name = get_output_name(actual_id)
    out_path = os.path.join(OUTPUT_DIR, out_name)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sorted_map = dict(sorted(keymap.items(), key=lambda x: x[0]))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sorted_map, f, ensure_ascii=False, indent=2)

    print(f"  OK: {actual_id} -> {out_name} ({len(sorted_map)} chars)")
    return out_path


def generate_all():
    print("Generating keymaps from WorldAlphabets layouts...")
    print()

    priority = ["en-us", "en-GB-qwerty", "de-DE-qwertz", "fr-french-standard-azerty",
                "es-spanish", "it-italian"]

    all_ids = []
    for f in sorted(os.listdir(LAYOUTS_DIR)):
        if f.endswith(".json"):
            lid = f[:-5]
            if lid not in priority:
                all_ids.append(lid)

    ordered = priority + all_ids

    count = 0
    for lid in ordered:
        result = generate_one(lid)
        if result:
            count += 1

    print(f"\nGenerated {count} keymap files in {OUTPUT_DIR}/")


def list_available():
    layouts = sorted(f[:-5] for f in os.listdir(LAYOUTS_DIR) if f.endswith(".json"))
    print(f"Available layouts ({len(layouts)}):")
    for lid in layouts:
        out = get_output_name(lid)
        tag = " <- priority" if lid in FRIENDLY_NAMES else ""
        print(f"  {lid:45s} -> {out}{tag}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        generate_all()
    elif sys.argv[1] == "--list":
        list_available()
    elif sys.argv[1] == "--help":
        print(__doc__)
    else:
        print("Generating keymaps...")
        for layout_id in sys.argv[1:]:
            generate_one(layout_id)
