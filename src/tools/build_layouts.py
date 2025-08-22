import json
from pathlib import Path
import argparse

from worldalphabets.models.keyboard import KeyboardLayout
from .parsers.kbdlayout_xml import parse_kbdlayout_xml

def build_layout(layout_id: str, source_dir: Path, output_dir: Path) -> None:
    """
    Builds a single keyboard layout from source files.
    """
    print(f"Building layout: {layout_id}")

    # Determine file paths
    # The user provided kbdgr.xml for de-DE-qwertz
    xml_file_name = "kbdgr.xml" if layout_id == "de-DE-qwertz" else f"{layout_id}.xml"

    xml_path = source_dir / layout_id / xml_file_name
    kle_path = source_dir / layout_id / "kle.json"

    if not xml_path.exists() or not kle_path.exists():
        print("  -> Skipping, source files not found.")
        return

    # Read source files
    xml_content = xml_path.read_text(encoding="utf-8")

    # Parse source files
    flags, xml_keys, dead_keys = parse_kbdlayout_xml(xml_content)

    # Load scancode to ISO position mapping
    mapping_path = Path("data/mappings/iso105_to_iso9995.json")
    sc_to_pos = {v["sc"]: k for k, v in json.loads(mapping_path.read_text()).items()}

    # Assign ISO position to keys
    for key in xml_keys:
        key.pos = sc_to_pos.get(key.sc)

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
    output_root = Path("src/worldalphabets/data/layouts")
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
