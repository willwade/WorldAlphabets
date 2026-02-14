#!/usr/bin/env python3
"""
Generate audio samples for all languages using SherpaOnnx models.

This script iterates through all SherpaOnnx models from merged_models.json,
downloads each model one at a time, generates audio, and then removes the model
to save disk space.
"""
import argparse
import json
import os
import re
import shutil
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("Installing soundfile...")
    os.system("pip install soundfile")
    import soundfile as sf

try:
    import sherpa_onnx
except ImportError:
    print("Installing sherpa-onnx...")
    os.system("pip install sherpa-onnx")
    import sherpa_onnx

# Project paths
ALPHABETS_DIR = Path("data/alphabets")
OUTPUT_DIR = Path("data/audio")
AUDIO_INDEX_PATH = Path("data/audio/index.json")
MODELS_JSON_URL = "https://raw.githubusercontent.com/willwade/tts-wrapper/main/tts_wrapper/engines/sherpaonnx/merged_models.json"
MODELS_JSON_PATH = Path("data/sherpa_models.json")
MODELS_CACHE_DIR = Path("data/sherpa_models_cache")

TEXT_FIELD = "hello_how_are_you"


def sanitize_model_id(model_id: str, max_len: int = 30) -> str:
    """Create a safe filename from model ID."""
    safe = re.sub(r"[^a-z0-9]+", "_", model_id.lower())
    return safe[:max_len].strip("_")


def fetch_models_json() -> Dict[str, Any]:
    """Fetch or load the merged_models.json file."""
    if MODELS_JSON_PATH.exists():
        print(f"Loading models from {MODELS_JSON_PATH}")
        with MODELS_JSON_PATH.open("r") as f:
            return json.load(f)

    print(f"Fetching models from {MODELS_JSON_URL}")
    response = requests.get(MODELS_JSON_URL, timeout=30)
    response.raise_for_status()
    models = response.json()

    # Save for future use
    MODELS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODELS_JSON_PATH.open("w") as f:
        json.dump(models, f, indent=2)

    print(f"Loaded {len(models)} models")
    return models


def get_sample_phrase(lang_code: str) -> Optional[str]:
    """Returns TEXT_FIELD from data/alphabets/{lang_code}.json if present."""
    path = ALPHABETS_DIR / f"{lang_code}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            val = obj.get(TEXT_FIELD)
            if isinstance(val, str) and val.strip():
                return val
    except Exception:
        pass
    return None


def get_project_languages() -> Dict[str, str]:
    """
    Get all language codes from the project index.
    Returns dict mapping language code -> file name
    """
    index_path = Path("data/index.json")
    if not index_path.exists():
        return {}

    with index_path.open("r", encoding="utf-8") as f:
        languages = json.load(f)

    lang_map = {}
    for lang in languages:
        lang_code = lang.get("language")
        script = lang.get("script")
        if lang_code and script:
            full_code = f"{lang_code}-{script}"
            lang_map[lang_code] = full_code
            lang_map[full_code] = full_code

    return lang_map


def extract_model_id_lang(model_id: str) -> Optional[str]:
    """
    Extract language code from SherpaOnnx model ID.
    Examples:
        mms_eng -> en
        mms_spa -> es
        mms_afr -> af
        vits-zh-CN -> zh
    """
    # MMS models: mms_<iso_639_3> or mms_<iso_639_2>
    if model_id.startswith("mms_"):
        code = model_id[4:].split("-")[0].split("_")[0]
        # Convert 3-letter ISO 639-3 to 2-letter if possible
        iso639_3_to_1 = {
            "eng": "en", "spa": "es", "fra": "fr", "deu": "de",
            "ita": "it", "por": "pt", "nld": "nl", "pol": "pl",
            "rus": "ru", "ara": "ar", "hin": "hi", "ben": "bn",
            "jpn": "ja", "kor": "ko", "zho": "zh", "tha": "th",
            "vie": "vi", "tur": "tr", "fin": "fi", "swe": "sv",
            "nor": "no", "dan": "da", "ces": "cs", "ell": "el",
            "heb": "he", "ukr": "uk", "ron": "ro", "hun": "hu",
            "afr": "af", "amh": "am", "asm": "as", "aze": "az",
            "bel": "be", "bul": "bg", "cat": "ca", "ceb": "ceb",
            "ckb": "ku", "dzo": "dz", "est": "et", "fas": "fa",
            "gle": "ga", "glg": "gl", "guj": "gu", "hye": "hy",
            "ibo": "ig", "ind": "id", "jav": "jv", "kat": "ka",
            "khm": "km", "lao": "lo", "lav": "lv", "lit": "lt",
            "lug": "lg", "mal": "ml", "mar": "mr", "mkd": "mk",
            "mlt": "mt", "mya": "my", "nep": "ne", "pan": "pa",
            "pus": "ps", "sin": "si", "slk": "sk", "slv": "sl",
            "sna": "sn", "som": "so", "sqi": "sq", "srp": "sr",
            "swa": "sw", "tam": "ta", "tel": "te", "tgk": "tg",
            "tlh": "tlh", "tsn": "tn",
            "urd": "ur", "uzb": "uz", "wol": "wo", "xho": "xh",
            "yor": "yo", "zul": "zu",
            # Additional 3-letter codes
            "aag": "aa", "aak": "aa", "aau": "aa",
            "abk": "ab", "ady": "ady", "afh": "af",
            "agq": "agq", "aht": "aht", "aia": "aia",
            "aka": "ak", "als": "als",
            # Add more as needed from MMS model list
        }
        return iso639_3_to_1.get(code, code)

    # VITS/models with lang codes
    if "-" in model_id:
        parts = model_id.split("-")
        if len(parts) >= 2:
            # zh-CN, zh-TW, en-US, etc.
            potential_lang = parts[1].split("_")[0]
            # Convert zh-CN to zh, etc.
            return potential_lang.split("-")[0][:2].lower()

    # Kokoro models with language info in name
    if "kokoro" in model_id:
        if "en" in model_id.lower():
            return "en"
        if "zh" in model_id.lower():
            return "zh"

    # Matcha models
    if "matcha" in model_id:
        if "en" in model_id.lower():
            return "en"
        if "es" in model_id.lower() or "spanish" in model_id.lower():
            return "es"
        if "fr" in model_id.lower() or "french" in model_id.lower():
            return "fr"

    return None


def find_model_for_language(lang_code: str, all_models: Dict[str, Any]) -> List[str]:
    """
    Find all SherpaOnnx model IDs that match a given language code.
    Returns list of model IDs.
    """
    matching_models = []

    for model_id, model_data in all_models.items():
        # Check language field in model data
        languages = model_data.get("language", [])
        if not languages:
            # Try to extract from model_id
            model_lang = extract_model_id_lang(model_id)
            if model_lang and model_lang.lower() == lang_code.lower():
                matching_models.append(model_id)
            continue

        for lang_info in languages:
            # Handle both JSON formats: "lang_code" (new) and "Iso Code" (MMS models)
            iso_code = lang_info.get("lang_code") or lang_info.get("Iso Code", "")
            if not iso_code:
                continue
            # Handle both 2-letter and 3-letter codes
            if iso_code.lower() == lang_code.lower() or iso_code.lower().startswith(lang_code.lower()):
                matching_models.append(model_id)
                break

    return matching_models


def download_model(model_id: str, model_url: str, dest_dir: Path) -> bool:
    """Download and extract a SherpaOnnx model."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Downloading model {model_id} from {model_url}")

    try:
        if model_url.endswith(('.tar.bz2', '.tar.gz', '.tgz')):
            # Archive download
            response = requests.get(model_url, stream=True, timeout=120)
            response.raise_for_status()

            temp_archive = dest_dir / "temp_archive"
            with open(temp_archive, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Extract
            if model_url.endswith('.tar.bz2'):
                with tarfile.open(temp_archive, "r:bz2") as tar:
                    tar.extractall(dest_dir, filter="data")
            elif model_url.endswith('.tar.gz') or model_url.endswith('.tgz'):
                with tarfile.open(temp_archive, "r:gz") as tar:
                    tar.extractall(dest_dir, filter="data")

            temp_archive.unlink()

        else:
            # Direct file download (MMS models from HuggingFace)
            # URL format: https://huggingface.co/.../resolve/main/eng
            # Need to append filenames to the full URL
            base_url = model_url.rstrip("/")

            # Download model.onnx
            model_onnx_url = f"{base_url}/model.onnx"
            tokens_url = f"{base_url}/tokens.txt"

            model_path = dest_dir / "model.onnx"
            tokens_path = dest_dir / "tokens.txt"

            print(f"    Downloading from: {model_onnx_url}")
            response = requests.get(model_onnx_url, timeout=60)
            response.raise_for_status()
            model_path.write_bytes(response.content)

            print(f"    Downloading from: {tokens_url}")
            response = requests.get(tokens_url, timeout=60)
            response.raise_for_status()
            tokens_path.write_bytes(response.content)

        print(f"  Model {model_id} downloaded successfully")
        return True

    except Exception as e:
        print(f"  Error downloading model {model_id}: {e}")
        return False


def find_model_files(model_dir: Path) -> tuple:
    """Find model.onnx and tokens.txt in extracted directory."""
    model_file = None
    tokens_file = None
    data_dir = ""
    voices_bin = None
    espeak_dir = None

    for root, dirs, files in os.walk(model_dir):
        for file in files:
            if file == "model.onnx" or file.endswith(".onnx"):
                model_file = Path(root) / file
            if file == "tokens.txt":
                tokens_file = Path(root) / file
            if file == "voices.bin":
                voices_bin = Path(root) / file

        if "espeak-ng-data" in dirs:
            espeak_dir = Path(root) / "espeak-ng-data"

    # If model not found, might be in a vits subdirectory
    if not model_file:
        for item in model_dir.rglob("*.onnx"):
            model_file = item
            break

    # If tokens not found
    if not tokens_file:
        for item in model_dir.rglob("tokens.txt"):
            tokens_file = item
            break

    return model_file, tokens_file, data_dir, voices_bin, espeak_dir


def synthesize_with_model(model_dir: Path, text: str, model_id: str) -> Optional[tuple]:
    """Synthesize audio using a downloaded model."""
    model_file, tokens_file, data_dir, voices_bin, espeak_dir = find_model_files(model_dir)

    if not model_file:
        print(f"    Could not find model.onnx for {model_id}")
        return None

    if not tokens_file:
        print(f"    Could not find tokens.txt for {model_id}")
        return None

    print(f"    Using model: {model_file}")
    print(f"    Using tokens: {tokens_file}")

    try:
        # Determine model type
        model_type = determine_model_type(model_id)

        # Create appropriate config
        if model_type == "kokoro":
            if not voices_bin:
                print("    Kokoro model requires voices.bin")
                return None
            config = create_kokoro_config(model_file, tokens_file, voices_bin, espeak_dir)
        elif model_type == "matcha":
            config = create_matcha_config(model_file, tokens_file, espeak_dir)
        elif model_type == "vits":
            config = create_vits_config(model_file, tokens_file, data_dir, espeak_dir)
        else:
            config = create_vits_config(model_file, tokens_file, data_dir, espeak_dir)

        # Create TTS
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=config,
            rule_fsts="",
            max_num_sentences=1,
        )
        tts = sherpa_onnx.OfflineTts(tts_config)

        # Generate audio
        print(f"    Synthesizing: {text[:50]}...")
        audio = tts.generate(text)

        if len(audio.samples) == 0:
            print("    No audio generated")
            return None

        # Convert to bytes
        audio_array = np.array(audio.samples)
        audio_bytes = (audio_array * 32767).astype(np.int16).tobytes()

        return audio_bytes, tts.sample_rate

    except Exception as e:
        print(f"    Error synthesizing: {e}")
        import traceback
        traceback.print_exc()
        return None


def determine_model_type(model_id: str) -> str:
    """Determine model type from model_id."""
    model_lower = model_id.lower()
    if model_lower.startswith("kokoro"):
        return "kokoro"
    if model_lower.startswith("matcha") or "matcha" in model_lower:
        return "matcha"
    if model_lower.startswith("icefall") and "matcha" in model_lower:
        return "matcha"
    # Default to vits
    return "vits"


def create_kokoro_config(model_file, tokens_file, voices_bin, espeak_dir):
    """Create Kokoro model config."""
    kokoro_cfg = sherpa_onnx.OfflineTtsKokoroModelConfig(
        model=str(model_file),
        voices=str(voices_bin) if voices_bin else "",
        tokens=str(tokens_file),
        data_dir=str(espeak_dir) if espeak_dir else "",
    )
    return sherpa_onnx.OfflineTtsModelConfig(
        kokoro=kokoro_cfg,
        provider="cpu",
        debug=False,
        num_threads=1,
    )


def create_matcha_config(model_file, tokens_file, espeak_dir):
    """Create Matcha model config (requires vocoder)."""
    # Download vocoder if needed
    vocoder_path = MODELS_CACHE_DIR / "vocoder" / "vocos-22khz-univ.onnx"
    vocoder_path.parent.mkdir(parents=True, exist_ok=True)

    if not vocoder_path.exists():
        print("    Downloading vocoder for Matcha model...")
        vocoder_url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/vocos-22khz-univ.onnx"
        response = requests.get(vocoder_url, timeout=60)
        response.raise_for_status()
        vocoder_path.write_bytes(response.content)

    matcha_cfg = sherpa_onnx.OfflineTtsMatchaModelConfig(
        acoustic_model=str(model_file),
        vocoder=str(vocoder_path),
        lexicon="",
        tokens=str(tokens_file),
        data_dir=str(espeak_dir) if espeak_dir else "",
    )
    return sherpa_onnx.OfflineTtsModelConfig(
        matcha=matcha_cfg,
        provider="cpu",
        debug=False,
        num_threads=1,
    )


def create_vits_config(model_file, tokens_file, data_dir, espeak_dir):
    """Create VITS model config."""
    vits_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
        model=str(model_file),
        lexicon="",
        tokens=str(tokens_file),
        data_dir=str(espeak_dir) if espeak_dir else "",
        dict_dir="",
    )
    return sherpa_onnx.OfflineTtsModelConfig(
        vits=vits_cfg,
        provider="cpu",
        debug=False,
        num_threads=1,
    )


def save_audio_file(audio_bytes: bytes, sample_rate: int, output_path: Path) -> bool:
    """Save audio bytes to WAV file."""
    try:
        import numpy as np
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        sf.write(str(output_path), audio_array, sample_rate)
        return True
    except Exception as e:
        print(f"    Error saving audio: {e}")
        return False


def cleanup_model(model_dir: Path):
    """Remove downloaded model files to save disk space."""
    try:
        if model_dir.exists():
            shutil.rmtree(model_dir)
            print(f"  Cleaned up model directory: {model_dir}")
    except Exception as e:
        print(f"  Warning: could not clean up {model_dir}: {e}")


def load_audio_index() -> Dict[str, List[Dict[str, str]]]:
    """Load existing audio index."""
    if AUDIO_INDEX_PATH.exists():
        with AUDIO_INDEX_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_audio_index(index: Dict[str, List[Dict[str, str]]]):
    """Save audio index."""
    AUDIO_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIO_INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def add_audio_entry(
    index: Dict[str, List[Dict[str, str]]],
    lang: str,
    engine: str,
    voice_id: str,
    path: Path,
):
    """Add entry to audio index."""
    entry = {"engine": engine, "voice_id": voice_id, "path": str(path)}
    items = index.setdefault(lang, [])
    if not any(it.get("path") == entry["path"] for it in items):
        items.append(entry)


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio using all SherpaOnnx models from merged_models.json"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of existing audio files"
    )
    parser.add_argument(
        "--model-id",
        type=str,
        help="Only process a specific model ID"
    )
    parser.add_argument(
        "--lang-code",
        type=str,
        help="Only process a specific language code"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SherpaOnnx Audio Generator")
    print("=" * 60)

    # Load models JSON
    all_models = fetch_models_json()
    print(f"Total models available: {len(all_models)}")

    # Get project languages
    project_languages = get_project_languages()
    print(f"Project languages: {len(project_languages)}")

    # Load audio index
    audio_index = load_audio_index()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Stats
    processed = 0
    generated = 0
    skipped = 0
    failed = 0

    # Filter models if specific model or language requested
    if args.model_id:
        all_models = {k: v for k, v in all_models.items() if k == args.model_id}
        print(f"Filtering to model: {args.model_id}")

    if args.lang_code:
        project_languages = {k: v for k, v in project_languages.items()
                          if k.lower() == args.lang_code.lower() or args.lang_code.lower() in k.lower()}
        print(f"Filtering to language: {args.lang_code}")

    # Process each project language
    for lang_code, full_code in sorted(project_languages.items()):
        # Skip duplicate base language codes
        if "-" not in lang_code and lang_code in [lc.split("-")[0] for lc in project_languages if "-" in lc]:
            # This is a base code that will be covered by full code
            continue

        actual_lang_code = lang_code.split("-")[0]
        phrase = get_sample_phrase(full_code)

        if not phrase:
            print(f"\nSkipping {full_code}: no '{TEXT_FIELD}' in alphabet file")
            skipped += 1
            continue

        # Find matching models
        matching_models = find_model_for_language(actual_lang_code, all_models)

        if not matching_models:
            print(f"\nSkipping {full_code}: no SherpaOnnx models for language '{actual_lang_code}'")
            skipped += 1
            continue

        print(f"\n{'=' * 60}")
        print(f"Language: {full_code} ({actual_lang_code})")
        print(f"Phrase: {phrase[:60]}...")
        print(f"Matching models: {len(matching_models)}")
        print(f"{'=' * 60}")

        for model_id in matching_models:
            processed += 1
            model_data = all_models[model_id]

            # Generate output filename
            safe_model_id = sanitize_model_id(model_id)
            output_file = OUTPUT_DIR / f"{full_code}_sherpaonnx_{safe_model_id}.wav"

            # Check if already exists
            if output_file.exists() and not args.force:
                print(f"\n[{processed}] {model_id}: Already exists, skipping")
                # Add to index if not already there
                add_audio_entry(audio_index, actual_lang_code, "sherpaonnx", model_id, output_file)
                skipped += 1
                continue

            print(f"\n[{processed}] Processing model: {model_id}")
            print(f"  Model type: {model_data.get('model_type', 'unknown')}")
            print(f"  File size: {model_data.get('filesize_mb', 'N/A')} MB")

            # Download model
            model_url = model_data["url"]
            model_dir = MODELS_CACHE_DIR / model_id

            try:
                success = download_model(model_id, model_url, model_dir)

                if not success:
                    print("  Failed to download model")
                    failed += 1
                    cleanup_model(model_dir)
                    continue

                # Synthesize audio
                result = synthesize_with_model(model_dir, phrase, model_id)

                if result is None:
                    print("  Failed to synthesize audio")
                    failed += 1
                    cleanup_model(model_dir)
                    continue

                audio_bytes, sample_rate = result

                # Save audio file
                if save_audio_file(audio_bytes, sample_rate, output_file):
                    print(f"  -> Saved: {output_file.name}")
                    generated += 1

                    # Add to audio index
                    add_audio_entry(audio_index, actual_lang_code, "sherpaonnx", model_id, output_file)
                    save_audio_index(audio_index)
                else:
                    failed += 1

            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

            finally:
                # Always clean up the model to save disk space
                cleanup_model(model_dir)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Processed: {processed}")
    print(f"Generated: {generated}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
