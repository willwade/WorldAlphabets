import json
from pathlib import Path
import argparse

import re
from worldalphabets.models.keyboard import KeyboardLayout
from .parsers.kbdlayout_xml import parse_xml
from .parsers.kle_json import parse_kle_json

import requests

# Mapping of keyboard scan codes (from the XML) to physical key identifiers
# expressed as DOM ``KeyboardEvent.code`` values.  This is not exhaustive but
# covers the common keys present on standard 101/104 keyboards.  Keys missing
# from this mapping will fall back to a row/column identifier derived from the
# KLE geometry.
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

def download_layout_sources(layout_id: str, driver_name: str, source_dir: Path) -> bool:
    """
    Downloads the source files for a given layout.
    """
    print(f"Downloading sources for {layout_id}...")
    layout_source_dir = source_dir / layout_id
    layout_source_dir.mkdir(parents=True, exist_ok=True)

    xml_url = f"http://kbdlayout.info/{driver_name.lower()}/download/xml"
    kle_url = f"http://kbdlayout.info/{driver_name.lower()}/download/json"

    try:
        # Download XML
        response = requests.get(xml_url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        with open(layout_source_dir / f"{driver_name.lower()}.xml", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Download KLE JSON
        response = requests.get(kle_url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        with open(layout_source_dir / "kle.json", "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"  -> Successfully downloaded sources for {layout_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  -> Error downloading sources for {layout_id}: {e}")
        return False

def slugify(text: str) -> str:
    """
    Converts a string to a filename-safe slug.
    """
    text = text.lower()
    text = re.sub(r"[\s\(\)]+", "-", text)  # Replace spaces and parens with a hyphen
    text = re.sub(r"[^a-z0-9\-]", "", text)  # Remove all other non-alphanumeric chars
    text = text.strip("-")
    return text

def build_layout(
    layout_id: str,
    lang_code: str,
    driver_mapping: dict[str, str],
    kbd_layouts: dict[str, dict[str, str]],
    source_dir: Path,
    output_dir: Path,
) -> None:
    """
    Builds a single keyboard layout from source files.
    """
    print(f"Building layout: {layout_id}")

    # Determine file paths
    driver_name = driver_mapping.get(layout_id)
    if not driver_name:
        print(f"  -> Skipping, no driver mapping found for {layout_id}.")
        return

    xml_file_name = f"{driver_name.lower()}.xml"
    xml_path = source_dir / layout_id / xml_file_name

    if not xml_path.exists():
        if not download_layout_sources(layout_id, driver_name, source_dir):
            return

    # Read source files
    xml_content = xml_path.read_text(encoding="utf-8")

    # Parse the XML for key legends and metadata
    flags, xml_keys, dead_keys = parse_xml(xml_content)

    # Parse geometry from the accompanying KLE file and merge it with the keys.
    kle_path = source_dir / layout_id / "kle.json"
    if kle_path.exists():
        try:
            geometries = parse_kle_json(kle_path.read_text(encoding="utf-8"))
            for key, geo in zip(xml_keys, geometries):
                key.row = geo["row"]
                key.col = geo["col"]
                key.shape = geo["shape"]
                key.pos = SCANCODE_TO_CODE.get(
                    key.sc or "", f"r{geo['row']}c{geo['col']}"
                )
            geom_len = len(geometries)
            xml_len = len(xml_keys)
            if geom_len < xml_len:
                print(
                    f"  -> Note: geometry covers {geom_len} of {xml_len} keys for {layout_id}"
                )
            elif geom_len > xml_len:
                print(
                    f"  -> Warning: geometry has extra keys for {layout_id}"
                )
        except Exception as e:
            print(f"  -> Warning: failed to parse KLE for {layout_id}: {e}")
    else:
        print(f"  -> Warning: no KLE JSON found for {layout_id}")

    # Get layout info
    layout_info = kbd_layouts.get(layout_id)
    if not layout_info:
        print(f"  -> Skipping, no layout info found for {layout_id}.")
        return
    full_name = layout_info.get("full_name", layout_id)
    sanitized_name = slugify(full_name)
    new_layout_id = f"{lang_code}-{sanitized_name}"

    # Create final layout object
    layout = KeyboardLayout(
        id=new_layout_id,
        name=full_name,
        source="kbdlayout.info",
        flags=flags,
        keys=xml_keys,
        dead_keys=dead_keys,
    )

    # Write to output file
    output_path = output_dir / f"{new_layout_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(layout.model_dump_json(indent=2))

    print(f"  -> Successfully built {output_path}")


def main() -> None:
    """
    Builds keyboard layouts from source files.
    """
    parser = argparse.ArgumentParser(description="Build keyboard layouts.")
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only build the specified layout(s).",
        default=None,
    )
    args = parser.parse_args()

    source_root = Path("data/sources")
    output_root = Path("data/layouts")
    output_root.mkdir(parents=True, exist_ok=True)

    # Load mappings
    driver_mapping_path = Path("data/mappings/layout_to_driver.json")
    kbdlayouts_path = Path("data/kbdlayouts.json")
    index_path = Path("data/index.json")

    if not all([p.exists() for p in [driver_mapping_path, kbdlayouts_path, index_path]]):
        print("Error: Required data files not found.")
        print("Please run `wa-populate-layouts` first.")
        return

    driver_mapping = json.loads(driver_mapping_path.read_text(encoding="utf-8"))
    kbd_layouts = json.loads(kbdlayouts_path.read_text(encoding="utf-8"))
    index_data = json.loads(index_path.read_text(encoding="utf-8"))

    layouts_to_build: list[tuple[str, str]] = []
    if args.only:
        # If --only is used, we need to find the lang_code for the given layout_id
        for layout_id in args.only:
            found = False
            for lang in index_data:
                if layout_id in lang.get("keyboards", []):
                    layouts_to_build.append((layout_id, lang["language"]))
                    found = True
                    break
            if not found:
                print(f"Warning: Could not find language for layout {layout_id}.")
    else:
        # Build all layouts found in the index
        for lang in index_data:
            lang_code = lang["language"]
            for layout_id in lang.get("keyboards", []):
                layouts_to_build.append((layout_id, lang_code))

    for layout_id, lang_code in layouts_to_build:
        build_layout(
            layout_id, lang_code, driver_mapping, kbd_layouts, source_root, output_root
        )

    print("Keyboard layout build process finished.")

if __name__ == "__main__":
    main()
