import json
from pathlib import Path
import argparse

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

def build_layout(layout_id: str, source_dir: Path, output_dir: Path) -> None:
    """
    Builds a single keyboard layout from source files.
    """
    print(f"Building layout: {layout_id}")

    # Determine file paths
    # This is a temporary mapping until the scraping logic is in place.
    layout_to_driver = {
        "de-DE-qwertz": "KBDGR",
        "en-GB-qwerty": "KBDUK",
        "en-US-qwerty": "KBDUS",
    }
    driver_name = layout_to_driver.get(layout_id)
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

    # Create final layout object
    layout = KeyboardLayout(
        id=layout_id,
        name=layout_id, # Placeholder name
        source="kbdlayout.info",
        flags=flags,
        keys=xml_keys,
        dead_keys=dead_keys,
    )

    # Write to output file
    output_path = output_dir / f"{layout_id}.json"
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

    if args.only:
        layouts_to_build = args.only
    else:
        # Build all layouts found in the index
        index_path = Path("data/index.json")
        index_data = json.loads(index_path.read_text(encoding="utf-8"))
        layouts_to_build = []
        for lang in index_data:
            if "keyboards" in lang:
                layouts_to_build.extend(lang["keyboards"])

    for layout_id in layouts_to_build:
        build_layout(layout_id, source_root, output_root)

    print("Keyboard layout build process finished.")

if __name__ == "__main__":
    main()
