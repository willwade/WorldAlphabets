#!/usr/bin/env python3
"""
CommonVoice Data Fetcher for WorldAlphabets

Fetches transcribed speech data from Mozilla CommonVoice datasets and extracts:
1. Word frequency lists
2. Character frequency data

Downloads CommonVoice datasets directly from Mozilla's website using API credentials.

Usage:
    uv run python scripts/fetch_commonvoice.py --lang dga --limit 1000
    uv run python scripts/fetch_commonvoice.py --list-languages
    uv run python scripts/fetch_commonvoice.py --lang ady --output data/freq/top1000/ady.txt

Requirements:
    pip install requests
"""

import argparse
import csv
import re
import tarfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' library not installed. Install with: pip install requests")


# Mozilla Data Collective API credentials (from user)
MDC_CLIENT_ID = "mdc_b16705fca5fa9ca411c3c9211b0b025e"
MDC_API_KEY = "5c79215b9f428a291c65bbc8c6671775560bfc1f7f19a563804acc066993f490"
MDC_BASE_URL = "https://datacollective.mozillafoundation.org/api"

# Cache directory for downloaded datasets
CACHE_DIR = Path(".cache/commonvoice")

# Known CommonVoice dataset IDs on Mozilla Data Collective
# These need to be discovered manually from the web interface at:
# https://datacollective.mozillafoundation.org/datasets
# Search for "Common Voice" and filter by language
# Format: {language_code: dataset_id}
KNOWN_DATASET_IDS = {
    # Confirmed working:
    "ady": "cmflnuzw4txwhavlnqbgq1g2r",  # Adyghe (West Circassian) - 934 MB

    # CommonVoice Spontaneous Speech datasets (from search results):
    "top": "cmflnuzz4wyrkutthowtknout",  # Papantla Totonac
    "ttj": "cmflnuzz4vhppvj6wsbmdxr70",  # Rutoro
    "ukv": "cmflnuzz4tpqhjtjib1z0cxyn",  # Kuku
    "seh": "cmflnuzz4s02aw77a4rc5elaa",  # Sena
    "mel": "cmflnuzz4rtj5db9eiok9bnx8",  # Central Melanau
    "xkl": "cmflnuzz4r5kns0vaem2awqqg",  # Kenyah
    "ruc": "cmflnuzz4onc7tkesjgh380bj",  # Ruuli
    "mmc": "cmflnuzz4o68p1jzp1i8bhcr9",  # Michoacán Mazahua
    "msi": "cmflnuzz4n2iqmo2wmt1yzmkn",  # Sabah Malay
    "meh": "cmflnuzz4k7dxqixum94ltueg",  # Southwestern Tlaxiaco Mixtec
    "tob": "cmflnuzz4hdum6fm7fr1cc73u",  # Toba Qom

    # To find more dataset IDs:
    # 1. Visit https://datacollective.mozillafoundation.org/datasets
    # 2. Search for "Common Voice" or specific language name
    # 3. Click on dataset and copy ID from URL
    # 4. Add to this dictionary
}


def get_dataset_info(dataset_id: str) -> Optional[Dict]:
    """
    Get dataset information from Mozilla Data Collective API.

    Args:
        dataset_id: Dataset ID (e.g., 'cmflnuzw4txwhavlnqbgq1g2r')

    Returns:
        Dataset information dict, or None if failed
    """
    if not REQUESTS_AVAILABLE:
        print("Error: 'requests' library required. Install with: pip install requests")
        return None

    try:
        url = f"{MDC_BASE_URL}/datasets/{dataset_id}"
        headers = {
            "Authorization": f"Bearer {MDC_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Error fetching dataset info for {dataset_id}: {e}")
        return None


def list_commonvoice_languages() -> List[str]:
    """List all known CommonVoice languages with dataset IDs."""
    return sorted(list(KNOWN_DATASET_IDS.keys()))


def download_dataset(lang_code: str) -> Optional[Path]:
    """
    Download CommonVoice dataset for a language using Mozilla Data Collective API.

    Args:
        lang_code: Language code (e.g., 'dga', 'ady')

    Returns:
        Path to extracted dataset directory, or None if failed
    """
    if not REQUESTS_AVAILABLE:
        print("Error: 'requests' library required.")
        return None

    # Create cache directory
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    lang_cache = CACHE_DIR / lang_code

    # Check if already downloaded
    if lang_cache.exists() and (lang_cache / "validated.tsv").exists():
        print(f"Using cached dataset for '{lang_code}'")
        return lang_cache

    # Check if we have a dataset ID for this language
    dataset_id = KNOWN_DATASET_IDS.get(lang_code)
    if not dataset_id:
        print(f"No dataset ID known for language '{lang_code}'")
        print(f"Known languages: {', '.join(KNOWN_DATASET_IDS.keys())}")
        return None

    try:
        print(f"Downloading CommonVoice dataset for '{lang_code}'...")
        print(f"Dataset ID: {dataset_id}")

        headers = {
            "Authorization": f"Bearer {MDC_API_KEY}",
            "Content-Type": "application/json"
        }

        # Step 1: Create download session
        print("Creating download session...")
        create_url = f"{MDC_BASE_URL}/datasets/{dataset_id}/download"
        create_response = requests.post(create_url, headers=headers, timeout=30)
        create_response.raise_for_status()

        download_info = create_response.json()
        download_token = download_info.get("downloadToken")
        download_url = download_info.get("downloadUrl")

        if not download_token or not download_url:
            print(f"Failed to get download token. Response: {download_info}")
            return None

        print(f"Download token: {download_token}")

        # Step 2: Download the file
        print("Downloading dataset file...")
        download_response = requests.get(download_url, headers=headers, stream=True, timeout=600)
        download_response.raise_for_status()

        # Save to temp file
        tar_path = CACHE_DIR / f"{lang_code}.tar.gz"
        total_size = int(download_response.headers.get('content-length', 0))
        downloaded = 0

        with open(tar_path, "wb") as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"  Progress: {percent:.1f}%", end="\r")

        print(f"\nDownload complete: {tar_path}")

        # Extract tar file
        print("Extracting dataset...")
        lang_cache.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(lang_cache)

        # Remove tar file
        tar_path.unlink()

        print(f"✅ Dataset downloaded and extracted to {lang_cache}")
        return lang_cache

    except Exception as e:
        print(f"Error downloading dataset for '{lang_code}': {e}")
        return None


def fetch_commonvoice_transcriptions(
    lang_code: str,
    split: str = "validated",
    max_samples: Optional[int] = None
) -> List[str]:
    """
    Fetch transcriptions from CommonVoice dataset for a language.

    Args:
        lang_code: Language code (e.g., 'en', 'dga', 'ady')
        split: Dataset split ('validated', 'train', 'dev', 'test', or 'all')
        max_samples: Maximum number of samples to fetch (None = all)

    Returns:
        List of transcription strings
    """
    # Download dataset
    dataset_dir = download_dataset(lang_code)

    if not dataset_dir:
        return []

    try:
        print(f"Loading transcriptions from '{split}' split...")

        # Determine which TSV files to read
        if split == "all":
            tsv_files = ["validated.tsv", "train.tsv", "dev.tsv", "test.tsv"]
        else:
            tsv_files = [f"{split}.tsv"]

        transcriptions = []

        for tsv_file in tsv_files:
            tsv_path = dataset_dir / tsv_file

            if not tsv_path.exists():
                # Try in subdirectory (CommonVoice extracts to cv-corpus-*/)
                subdirs = list(dataset_dir.glob("cv-corpus-*"))
                if subdirs:
                    tsv_path = subdirs[0] / lang_code / tsv_file

            # Try Spontaneous Speech format (sps-corpus-*/)
            if not tsv_path.exists():
                sps_subdirs = list(dataset_dir.glob("sps-corpus-*"))
                if sps_subdirs:
                    # Spontaneous Speech uses different file naming
                    sps_file = sps_subdirs[0] / f"ss-corpus-{lang_code}.tsv"
                    if sps_file.exists():
                        tsv_path = sps_file

            if not tsv_path.exists():
                continue

            print(f"Reading {tsv_path.name}...")

            # Read TSV file
            with open(tsv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")

                for i, row in enumerate(reader):
                    if max_samples and len(transcriptions) >= max_samples:
                        break

                    # Get sentence text (try multiple field names)
                    # 'sentence' = regular CommonVoice
                    # 'transcription' = Spontaneous Speech
                    # 'text' = other formats
                    text = row.get("sentence", row.get("transcription", row.get("text", ""))).strip()
                    if text:
                        transcriptions.append(text)

        print(f"✅ Extracted {len(transcriptions)} transcriptions")
        return transcriptions

    except Exception as e:
        print(f"Error reading transcriptions for '{lang_code}': {e}")
        return []


def calculate_word_frequencies(transcriptions: List[str]) -> Counter:
    """Calculate word frequencies from transcriptions."""
    word_counts = Counter()
    
    for text in transcriptions:
        # Simple word tokenization (split on whitespace and punctuation)
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts.update(words)
    
    return word_counts


def calculate_char_frequencies(transcriptions: List[str]) -> Counter:
    """Calculate character frequencies from transcriptions."""
    char_counts = Counter()
    
    for text in transcriptions:
        # Count all alphabetic characters
        chars = [c.lower() for c in text if c.isalpha()]
        char_counts.update(chars)
    
    return char_counts


def generate_frequency_list(
    lang_code: str,
    limit: int = 1000,
    split: str = "all",
    max_samples: Optional[int] = None,
    use_bigrams: bool = False
) -> Tuple[List[str], str]:
    """
    Generate frequency list from CommonVoice data.
    
    Args:
        lang_code: Language code
        limit: Number of top items to return
        split: Dataset split to use
        max_samples: Maximum samples to process
        use_bigrams: Generate character bigrams instead of words
    
    Returns:
        Tuple of (frequency list, mode)
    """
    # Fetch transcriptions
    transcriptions = fetch_commonvoice_transcriptions(lang_code, split, max_samples)
    
    if not transcriptions:
        return [], "word"
    
    if use_bigrams:
        # Generate character bigrams
        all_text = " ".join(transcriptions)
        bigrams = [all_text[i:i+2] for i in range(len(all_text) - 1)]
        bigram_counts = Counter(bigrams)
        top_items = [bigram for bigram, _ in bigram_counts.most_common(limit)]
        mode = "bigram"
    else:
        # Generate word frequencies
        word_counts = calculate_word_frequencies(transcriptions)
        top_items = [word for word, _ in word_counts.most_common(limit)]
        mode = "word"
    
    return top_items, mode


def save_frequency_list(
    tokens: List[str],
    output_path: Path,
    mode: str = "word"
) -> None:
    """Save frequency list to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    header = f"# type={mode}\n" if mode == "bigram" else ""
    content = header + "\n".join(tokens) + "\n"
    
    output_path.write_text(content, encoding="utf-8")
    print(f"✅ Saved {len(tokens)} {mode}s to {output_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        help="Language code to fetch (e.g., 'dga', 'ady', 'en')"
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all available CommonVoice languages"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of top items to extract (default: 1000)"
    )
    parser.add_argument(
        "--split",
        default="validated",
        choices=["validated", "train", "dev", "test", "all"],
        help="Dataset split to use (default: validated)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        help="Maximum number of samples to process (default: all)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: data/freq/top1000/<lang>.txt)"
    )
    parser.add_argument(
        "--bigrams",
        action="store_true",
        help="Generate character bigrams instead of words"
    )
    
    args = parser.parse_args()

    if not REQUESTS_AVAILABLE:
        print("Error: 'requests' library required.")
        print("Install with: pip install requests")
        return
    
    if args.list_languages:
        print("Available CommonVoice languages:")
        languages = list_commonvoice_languages()
        for i, lang in enumerate(languages, 1):
            print(f"  {i:3d}. {lang}")
        print(f"\nTotal: {len(languages)} languages")
        return
    
    if not args.lang:
        print("Error: --lang required (or use --list-languages)")
        parser.print_help()
        return
    
    # Generate frequency list
    print(f"\n🔍 Fetching CommonVoice data for '{args.lang}'...")
    tokens, mode = generate_frequency_list(
        args.lang,
        limit=args.limit,
        split=args.split,
        max_samples=args.max_samples,
        use_bigrams=args.bigrams
    )
    
    if not tokens:
        print(f"❌ No data found for language '{args.lang}'")
        return
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = Path(f"data/freq/top1000/{args.lang}.txt")
    
    # Save frequency list
    save_frequency_list(tokens, output_path, mode)
    
    print(f"\n✅ Successfully generated frequency list for '{args.lang}'")
    print(f"   Mode: {mode}")
    print(f"   Items: {len(tokens)}")
    print(f"   Output: {output_path}")


if __name__ == "__main__":
    main()

