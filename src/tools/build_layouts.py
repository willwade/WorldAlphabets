import json
from pathlib import Path
import argparse

import re
from worldalphabets.models.keyboard import KeyboardLayout
from .parsers.kbdlayout_xml import parse_xml

import requests

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

    # Parse source files
    flags, xml_keys, dead_keys = parse_xml(xml_content)

    # Scancode and ISO position mapping is not yet implemented for the KbdDll format.
    # This will be added later.

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
