#!/usr/bin/env python3
"""
Sync data files from main data/ directory to Python package data directory.

This script ensures that the Python package includes all the generated data files
by copying them from data/ to src/worldalphabets/data/.
"""

import shutil
import sys
from pathlib import Path


def sync_alphabets(source_dir: Path, target_dir: Path) -> int:
    """Sync alphabet files from source to target directory."""
    source_alphabets = source_dir / "alphabets"
    target_alphabets = target_dir / "alphabets"

    if not source_alphabets.exists():
        print(f"Warning: Source alphabets directory {source_alphabets} does not exist")
        return 0

    # Create target directory if it doesn't exist
    target_alphabets.mkdir(parents=True, exist_ok=True)

    # Copy all alphabet files
    copied = 0
    for alphabet_file in source_alphabets.glob("*.json"):
        target_file = target_alphabets / alphabet_file.name
        shutil.copy2(alphabet_file, target_file)
        copied += 1

    print(
        f"Copied {copied} alphabet files from {source_alphabets} to {target_alphabets}"
    )
    return copied


def sync_frequency_data(source_dir: Path, target_dir: Path) -> int:
    """Sync frequency data from source to target directory."""
    source_freq = source_dir / "freq"
    target_freq = target_dir / "freq"

    if not source_freq.exists():
        print(f"Warning: Source frequency directory {source_freq} does not exist")
        return 0

    # Remove existing frequency data and recreate
    if target_freq.exists():
        shutil.rmtree(target_freq)

    # Copy entire frequency directory structure
    shutil.copytree(source_freq, target_freq)

    # Count files
    freq_files = len(list(target_freq.rglob("*.txt")))
    print(
        f"Copied frequency data directory with {freq_files} files from {source_freq} to {target_freq}"
    )
    return freq_files


def sync_index_file(source_dir: Path, target_dir: Path) -> bool:
    """Sync index.json file."""
    source_index = source_dir / "index.json"
    target_index = target_dir / "index.json"

    if not source_index.exists():
        print(f"Warning: Source index file {source_index} does not exist")
        return False

    shutil.copy2(source_index, target_index)
    print(f"Copied index.json from {source_index} to {target_index}")
    return True


def sync_other_data_files(source_dir: Path, target_dir: Path) -> int:
    """Sync other data files like stats.json, etc."""
    copied = 0

    # List of additional files to sync
    additional_files = [
        "stats.json",
        "tts_index.json",
    ]

    for filename in additional_files:
        source_file = source_dir / filename
        target_file = target_dir / filename

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"Copied {filename}")
            copied += 1
        else:
            print(f"Warning: {filename} not found in source directory")

    return copied


def update_manifest(root_dir: Path) -> None:
    """Update MANIFEST.in to include the package data correctly."""
    manifest_file = root_dir / "MANIFEST.in"

    # Read current content
    if manifest_file.exists():
        current_content = manifest_file.read_text().strip()
    else:
        current_content = ""

    # Required lines for package data
    required_lines = [
        "recursive-include src/worldalphabets/data *",
        "include src/worldalphabets/py.typed",
    ]

    # Check if we need to update
    lines = current_content.split("\n") if current_content else []
    needs_update = False

    for required_line in required_lines:
        if required_line not in lines:
            lines.append(required_line)
            needs_update = True

    # Remove old incorrect line if present
    if "recursive-include data *" in lines:
        lines.remove("recursive-include data *")
        needs_update = True

    if needs_update:
        manifest_file.write_text("\n".join(lines) + "\n")
        print("Updated MANIFEST.in")
    else:
        print("MANIFEST.in is already up to date")


def main() -> None:
    """Main sync function."""
    root_dir = Path(__file__).parent.parent
    source_dir = root_dir / "data"
    target_dir = root_dir / "src" / "worldalphabets" / "data"

    print("WorldAlphabets Package Data Sync")
    print("=" * 40)
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print()

    if not source_dir.exists():
        print(f"Error: Source data directory {source_dir} does not exist")
        print(
            "Please run the data pipeline first: uv run scripts/build_data_pipeline.py"
        )
        sys.exit(1)

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Sync different types of data
    total_files = 0

    # Sync alphabets
    total_files += sync_alphabets(source_dir, target_dir)

    # Sync frequency data
    total_files += sync_frequency_data(source_dir, target_dir)

    # Sync index file
    if sync_index_file(source_dir, target_dir):
        total_files += 1

    # Sync other data files
    total_files += sync_other_data_files(source_dir, target_dir)

    # Update MANIFEST.in
    update_manifest(root_dir)

    print()
    print(
        f"✅ Sync complete! {total_files} files synced to Python package data directory"
    )
    print()
    print("Next steps:")
    print("1. Build the package: uv run python -m build")
    print(
        "2. Test the package: uv run python -c 'from worldalphabets import get_available_codes; print(len(get_available_codes()))'"
    )


if __name__ == "__main__":
    main()
