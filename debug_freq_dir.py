#!/usr/bin/env python3
"""
Debug frequency directory resolution.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets.detect import DEFAULT_FREQ_DIR, _load_rank_data

def main():
    print("Debugging frequency directory resolution")
    print(f"DEFAULT_FREQ_DIR: {DEFAULT_FREQ_DIR}")
    print(f"DEFAULT_FREQ_DIR type: {type(DEFAULT_FREQ_DIR)}")
    print(f"DEFAULT_FREQ_DIR exists: {Path(str(DEFAULT_FREQ_DIR)).exists()}")
    
    # Convert to Path and check
    freq_dir = Path(str(DEFAULT_FREQ_DIR))
    print(f"freq_dir: {freq_dir}")
    print(f"freq_dir exists: {freq_dir.exists()}")
    
    # Check specific files
    for lang in ['en', 'de', 'pl']:
        file_path = freq_dir / f"{lang}.txt"
        print(f"{lang}.txt path: {file_path}")
        print(f"{lang}.txt exists: {file_path.exists()}")
        
        if file_path.exists():
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
                print(f"{lang}.txt lines: {len(lines)}")
                print(f"{lang}.txt first 3 lines: {lines[:3]}")
            except Exception as e:
                print(f"Error reading {lang}.txt: {e}")
        
        # Test _load_rank_data
        data = _load_rank_data(lang, freq_dir)
        print(f"{lang} rank data size: {len(data.ranks)}")
        print()

if __name__ == "__main__":
    main()
