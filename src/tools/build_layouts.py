from pathlib import Path
import argparse

from worldalphabets.models.keyboard import KeyboardLayout
from .parsers.kbdlayout_xml import parse_xml

def build_layout(layout_id: str, source_dir: Path, output_dir: Path) -> None:
    """
    Builds a single keyboard layout from source files.
    """
    print(f"Building layout: {layout_id}")

    # Determine file paths
    # This is a temporary mapping until the scraping logic is in place.
    layout_to_file = {
        "de-DE-qwertz": "kbdgr.xml",
        "en-GB-qwerty": "kbduk.xml",
    }
    xml_file_name = layout_to_file.get(layout_id, f"{layout_id}.xml")

    xml_path = source_dir / layout_id / xml_file_name

    if not xml_path.exists():
        print("  -> Skipping, source file not found.")
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
        # Build all layouts found in the source directory
        layouts_to_build = [d.name for d in source_root.iterdir() if d.is_dir()]

    for layout_id in layouts_to_build:
        build_layout(layout_id, source_root, output_root)

    print("Keyboard layout build process finished.")

if __name__ == "__main__":
    main()
