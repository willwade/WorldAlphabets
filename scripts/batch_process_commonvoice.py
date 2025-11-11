#!/usr/bin/env python3
"""
Batch process multiple CommonVoice languages.

This script:
1. Downloads CommonVoice datasets for multiple languages
2. Generates word frequency lists
3. Creates alphabet JSON files
4. Updates the index

Usage:
    # Process specific languages
    uv run python scripts/batch_process_commonvoice.py --langs ttj meh tob
    
    # Process all configured languages
    uv run python scripts/batch_process_commonvoice.py --all
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


# Languages configured in fetch_commonvoice.py
AVAILABLE_LANGUAGES = {
    "ady": "Adyghe (West Circassian)",
    "top": "Papantla Totonac",
    "ttj": "Rutoro",
    "ukv": "Kuku",
    "seh": "Sena",
    "mel": "Central Melanau",
    "xkl": "Kenyah",
    "ruc": "Ruuli",
    "mmc": "Michoacán Mazahua",
    "msi": "Sabah Malay",
    "meh": "Southwestern Tlaxiaco Mixtec",
    "tob": "Toba Qom",
}


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False


def process_language(lang_code: str) -> bool:
    """Process a single language through the full pipeline."""
    lang_name = AVAILABLE_LANGUAGES.get(lang_code, lang_code)
    print(f"\n{'#'*60}")
    print(f"# Processing: {lang_name} ({lang_code})")
    print(f"{'#'*60}")
    
    # Step 1: Download and generate word frequency list
    if not run_command(
        ["uv", "run", "python", "scripts/fetch_commonvoice.py", "--lang", lang_code],
        f"Download CommonVoice data for {lang_code}"
    ):
        return False
    
    # Check if frequency file was created
    freq_file = Path(f"data/freq/top1000/{lang_code}.txt")
    if not freq_file.exists():
        print(f"❌ Frequency file not created for {lang_code}")
        return False
    
    # Step 2: Generate alphabet file from frequency data
    # Determine script (most are Latin, some are Cyrillic)
    cyrillic_langs = {"ady"}  # Add more as needed
    script = "Cyrl" if lang_code in cyrillic_langs else "Latn"
    
    if not run_command(
        ["uv", "run", "python", "scripts/generate_alphabet_from_freq.py", 
         "--lang", lang_code, "--script", script],
        f"Generate alphabet file for {lang_code}"
    ):
        return False
    
    # Check if alphabet file was created
    alphabet_file = Path(f"data/alphabets/{lang_code}-{script}.json")
    if not alphabet_file.exists():
        print(f"❌ Alphabet file not created for {lang_code}")
        return False
    
    print(f"\n✅ Successfully processed {lang_name} ({lang_code})")
    return True


def update_index() -> bool:
    """Update the main index after processing languages."""
    print(f"\n{'='*60}")
    print("📊 Updating index...")
    print(f"{'='*60}")
    
    result = subprocess.run(["node", "scripts/create_index.js"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        print("✅ Index updated successfully")
        return True
    else:
        print(f"❌ Index update failed: {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch process CommonVoice languages"
    )
    parser.add_argument(
        "--langs",
        nargs="+",
        help="Language codes to process (e.g., ttj meh tob)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available languages"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip languages that already have alphabet files"
    )
    
    args = parser.parse_args()
    
    # Determine which languages to process
    if args.all:
        langs_to_process = list(AVAILABLE_LANGUAGES.keys())
    elif args.langs:
        langs_to_process = args.langs
        # Validate language codes
        invalid = [l for l in langs_to_process if l not in AVAILABLE_LANGUAGES]
        if invalid:
            print(f"❌ Invalid language codes: {', '.join(invalid)}")
            print(f"Available: {', '.join(AVAILABLE_LANGUAGES.keys())}")
            return 1
    else:
        print("❌ Please specify --langs or --all")
        parser.print_help()
        return 1
    
    # Filter out existing if requested
    if args.skip_existing:
        original_count = len(langs_to_process)
        langs_to_process = [
            lang for lang in langs_to_process
            if not any(Path(f"data/alphabets/{lang}-{script}.json").exists() 
                      for script in ["Latn", "Cyrl"])
        ]
        skipped = original_count - len(langs_to_process)
        if skipped > 0:
            print(f"ℹ️  Skipping {skipped} languages that already have alphabet files")
    
    if not langs_to_process:
        print("ℹ️  No languages to process")
        return 0
    
    print(f"\n{'='*60}")
    print(f"🌍 CommonVoice Batch Processing")
    print(f"{'='*60}")
    print(f"Languages to process: {len(langs_to_process)}")
    for lang in langs_to_process:
        print(f"  - {lang}: {AVAILABLE_LANGUAGES[lang]}")
    print(f"{'='*60}\n")
    
    # Process each language
    successful = []
    failed = []
    
    for lang_code in langs_to_process:
        if process_language(lang_code):
            successful.append(lang_code)
        else:
            failed.append(lang_code)
    
    # Update index if any languages were processed successfully
    if successful:
        print(f"\n{'='*60}")
        print("📊 Updating main index...")
        print(f"{'='*60}")
        update_index()
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {len(successful)}")
    for lang in successful:
        print(f"   - {lang}: {AVAILABLE_LANGUAGES[lang]}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for lang in failed:
            print(f"   - {lang}: {AVAILABLE_LANGUAGES[lang]}")
    
    print(f"\n{'='*60}")
    
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

