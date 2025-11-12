#!/usr/bin/env python3
import argparse
import os
import json
import platform
import re
from pathlib import Path
from typing import Any, Optional, Dict, List
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tts_wrapper import (  # noqa: E402
    ElevenLabsClient,
    GoogleClient,
    MicrosoftTTS,
    OpenAIClient,
    PollyClient,
    SherpaOnnxClient,
    UpliftAIClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)

# Platform-specific imports
if platform.system() == "Darwin":  # macOS
    from tts_wrapper import AVSynthClient

from scripts.lib.data_layout import RepoDataLayout  # noqa: E402

DATA_LAYOUT = RepoDataLayout()
ALPHABETS_DIR = DATA_LAYOUT.legacy_alphabet_dir()
TTS_INDEX_PATH = Path("data/tts_index.json")
TEXT_FIELD = "hello_how_are_you"  # field added by your translate step
# Legacy output directory retained for compatibility
LEGACY_AUDIO_DIR = DATA_LAYOUT.legacy_audio_dir()
AUDIO_INDEX_PATH = LEGACY_AUDIO_DIR / "index.json"


def sanitize_voice_id(voice_id: str, max_len: int = 20) -> str:
    # Lowercase, replace non-alphanumeric with underscore, truncate
    safe = re.sub(r"[^a-z0-9]+", "_", voice_id.lower())
    return safe[:max_len].strip("_")


def add_index_entry(
    audio_index: Dict[str, List[Dict[str, str]]],
    *,
    lang: str,
    engine: str,
    voice_id: str,
    path: Path,
) -> Dict[str, str]:
    entry = {"engine": engine, "voice_id": voice_id, "path": str(path.as_posix())}
    items = audio_index.setdefault(lang, [])
    # de-duplicate by exact path
    if not any(it.get("path") == entry["path"] for it in items):
        items.append(entry)
    return entry


def get_tts_client(engine_name: str) -> Optional[Any]:
    """Initializes and returns a TTS client based on the engine name."""
    client = None
    try:
        if engine_name == "polly":
            if os.getenv("POLLY_AWS_KEY_ID"):
                client = PollyClient(
                    credentials=(
                        os.getenv("POLLY_REGION"),
                        os.getenv("POLLY_AWS_KEY_ID"),
                        os.getenv("POLLY_AWS_ACCESS_KEY"),
                    )
                )
        elif engine_name == "microsoft":
            if os.getenv("MICROSOFT_TOKEN"):
                client = MicrosoftTTS(
                    credentials=(
                        os.getenv("MICROSOFT_TOKEN"),
                        os.getenv("MICROSOFT_REGION"),
                    )
                )
        elif engine_name == "watson":
            if os.getenv("WATSON_API_KEY"):
                client = WatsonClient(
                    credentials=(
                        os.getenv("WATSON_API_KEY"),
                        os.getenv("WATSON_REGION"),
                        os.getenv("WATSON_INSTANCE_ID"),
                    )
                )
        elif engine_name == "google":
            # Google Cloud TTS requires service account credentials (JSON file)
            if os.getenv("GOOGLE_SA_PATH"):
                client = GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH"))
            # Alternative: Application Default Credentials (if gcloud is configured)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                client = GoogleClient(credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
            # Note: GOOGLE_TTS_KEY (API key) is not supported by Google Cloud TTS
            # You need a service account JSON file
        elif engine_name == "elevenlabs":
            if os.getenv("ELEVENLABS_API_KEY"):
                client = ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY"))
        elif engine_name == "witai":
            if os.getenv("WITAI_TOKEN"):
                client = WitAiClient(credentials=(os.getenv("WITAI_TOKEN"),))
        elif engine_name == "openai":
            if os.getenv("OPENAI_API_KEY"):
                client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        elif engine_name == "upliftai":
            if os.getenv("UPLIFTAI_KEY"):
                client = UpliftAIClient(api_key=os.getenv("UPLIFTAI_KEY"))
        elif engine_name == "sherpaonnx":
            client = SherpaOnnxClient()
        elif engine_name == "espeak":
            client = eSpeakClient()
        elif engine_name == "avsynth" and platform.system() == "Darwin":
            client = AVSynthClient()
    except Exception as e:
        print(f"  - Error initializing {engine_name} client: {e}")
        return None

    return client


def read_sample_phrase(lang_code: str) -> Optional[str]:
    """Returns TEXT_FIELD from data/alphabets/{lang_code}.json if present."""
    candidates: List[Path] = []
    if "-" in lang_code:
        lang, script = lang_code.split("-", 1)
        candidate = DATA_LAYOUT.alphabet_path(lang, script)
        candidates.append(candidate)
    candidates.append(ALPHABETS_DIR / f"{lang_code}.json")
    if "-" in lang_code:
        lang = lang_code.split("-", 1)[0]
        candidates.append(ALPHABETS_DIR / f"{lang}.json")

    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                val = obj.get(TEXT_FIELD)
                if isinstance(val, str) and val.strip():
                    return val
        except Exception:
            continue
    return None


def safe_engine_suffix(engine: str) -> str:
    s = (engine or "").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in s) or "engine"


def generate_audio_files(skip_existing: bool = True) -> None:
    """
    Iterate alphabet files (the source of truth), synth audio for each voice found in
    tts_index.json that matches the alphabet's language code, using the phrase in TEXT_FIELD.
    """
    LEGACY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing audio index if present
    audio_index: Dict[str, List[Dict[str, str]]] = {}
    if AUDIO_INDEX_PATH.exists():
        try:
            with AUDIO_INDEX_PATH.open("r", encoding="utf-8") as f:
                audio_index = json.load(f)
            if not isinstance(audio_index, dict):
                audio_index = {}
        except Exception:
            audio_index = {}

    # Load TTS index (maps lang_code -> list[ {engine, voice_id, ...}, ... ])
    try:
        with TTS_INDEX_PATH.open("r", encoding="utf-8") as f:
            tts_index: Dict[str, List[Dict[str, Any]]] = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure you have run the TTS indexing first.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: {TTS_INDEX_PATH} is not valid JSON: {e}")
        return

    # Build the set of languages we actually have alphabet files for
    alphabet_langs_set: set[str] = set()
    if DATA_LAYOUT.root.exists():
        for lang_dir in DATA_LAYOUT.root.iterdir():
            alphabet_dir = lang_dir / "alphabet"
            if alphabet_dir.is_dir():
                alphabet_langs_set.update(p.stem for p in alphabet_dir.glob("*.json"))

    if not alphabet_langs_set and ALPHABETS_DIR.exists():
        alphabet_langs_set.update(p.stem for p in ALPHABETS_DIR.glob("*.json"))

    alphabet_langs = sorted(alphabet_langs_set)

    print("Starting audio generation...")
    generated = 0
    skipped_no_phrase = 0
    skipped_no_voices = 0

    for lang_code in alphabet_langs:
        phrase = read_sample_phrase(lang_code)
        if not phrase:
            print(f"Skipping {lang_code} (no '{TEXT_FIELD}' in alphabets file).")
            skipped_no_phrase += 1
            continue

        # Extract base language code for TTS lookup (e.g., "en-Latn" -> "en")
        base_lang_code = lang_code.split('-')[0]
        canonical_lang = DATA_LAYOUT.canonical_code(base_lang_code)

        # Try both full lang_code and base language code
        voices = tts_index.get(lang_code) or tts_index.get(base_lang_code) or []
        if not voices:
            print(f"Skipping {lang_code} (no TTS voices listed in tts_index.json for '{lang_code}' or '{base_lang_code}').")
            skipped_no_voices += 1
            continue

        for voice_info in voices:
            engine = voice_info.get("engine")
            voice_id = voice_info.get("voice_id")
            if not engine or not voice_id:
                print(f"  Skipping {lang_code} (invalid voice entry: {voice_info}).")
                continue

            engine_slug = safe_engine_suffix(engine)
            safe_voice = sanitize_voice_id(voice_id)
            lang_output_dir = DATA_LAYOUT.audio_dir(canonical_lang)
            lang_output_dir.mkdir(parents=True, exist_ok=True)
            out_path = lang_output_dir / f"{lang_code}_{engine_slug}_{safe_voice}.wav"

            # If the file already exists and skip_existing is True, skip it
            if out_path.exists() and skip_existing:
                # Use base language code for audio index (e.g., "en-Latn" -> "en")
                base_lang_for_index = canonical_lang
                add_index_entry(
                    audio_index,
                    lang=base_lang_for_index,
                    engine=engine,
                    voice_id=voice_id,
                    path=out_path,
                )
                # Immediately save audio index after adding entry
                try:
                    AUDIO_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with AUDIO_INDEX_PATH.open("w", encoding="utf-8") as f:
                        json.dump(audio_index, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Warning: failed to write audio index: {e}")

                rel_path = out_path.relative_to(DATA_LAYOUT.root)
                DATA_LAYOUT.update_metadata(
                    base_lang_for_index,
                    "audio",
                    {
                        "file": str(rel_path),
                        "engine": engine,
                        "voice_id": voice_id,
                        "status": "existing",
                    },
                )
                DATA_LAYOUT.append_source_entry(
                    base_lang_for_index,
                    "audio",
                    "Audio sample already present on disk",
                    {"engine": engine, "voice": voice_id, "file": str(rel_path)},
                )

                print(
                    f"Skipping {lang_code} ({engine_slug}, voice {voice_id}): already exists."
                )
                continue

            print(
                f"Generating {lang_code} using {engine} (voice {voice_id}) -> {out_path.name}"
            )

            tts_client = get_tts_client(engine)
            if not tts_client:
                print(
                    f"  Could not initialize TTS client for {engine}. Check environment variables."
                )
                continue

            ok = synth_to_temp_and_commit(tts_client, phrase, voice_id, out_path)
            if ok:
                print(f"  -> Saved to {out_path}")
                generated += 1
                # Use base language code for audio index (e.g., "en-Latn" -> "en")
                base_lang_for_index = canonical_lang
                add_index_entry(
                    audio_index,
                    lang=base_lang_for_index,
                    engine=engine,
                    voice_id=voice_id,
                    path=out_path,
                )
                # Immediately save audio index after adding entry
                try:
                    AUDIO_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with AUDIO_INDEX_PATH.open("w", encoding="utf-8") as f:
                        json.dump(audio_index, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Warning: failed to write audio index: {e}")

                rel_path = out_path.relative_to(DATA_LAYOUT.root)
                DATA_LAYOUT.update_metadata(
                    base_lang_for_index,
                    "audio",
                    {
                        "file": str(rel_path),
                        "engine": engine,
                        "voice_id": voice_id,
                        "status": "generated",
                    },
                )
                DATA_LAYOUT.append_source_entry(
                    base_lang_for_index,
                    "audio",
                    "Generated audio sample",
                    {"engine": engine, "voice": voice_id, "file": str(rel_path)},
                )

            else:
                print(
                    f"  Skipped (invalid/failed synth) for {lang_code} ({engine_slug}, voice {voice_id})."
                )
    # Removed final bulk save of audio index since incremental saves are done

    for lang, entries in audio_index.items():
        per_lang_index_path = DATA_LAYOUT.audio_dir(lang) / "index.json"
        per_lang_index_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with per_lang_index_path.open("w", encoding="utf-8") as fh:
                json.dump(entries, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Warning: failed to write {per_lang_index_path}: {exc}")

    print(
        f"\nAudio generation complete. Files created: {generated}. "
        f"Skipped (no phrase): {skipped_no_phrase}. Skipped (no voices): {skipped_no_voices}."
    )


MIN_WAV_BYTES = 2048  # reject files smaller than this (likely empty/error)


def is_valid_wav(path: Path, min_bytes: int = MIN_WAV_BYTES) -> bool:
    """Very lightweight WAV validation: RIFF/WAVE header present and file big enough."""
    try:
        if not path.exists() or path.stat().st_size < min_bytes:
            return False
        with path.open("rb") as f:
            header = f.read(12)
            # RIFF chunk descriptor: 0-3 'RIFF', 8-11 'WAVE'
            if len(header) < 12 or header[0:4] != b"RIFF" or header[8:12] != b"WAVE":
                return False
        return True
    except Exception:
        return False


def synth_to_temp_and_commit(
    tts_client: Any, text: str, voice_id: str, final_path: Path
) -> bool:
    """
    Synthesize to a temporary file first, then validate. If valid, atomically move to final.
    Returns True on success; False if synth failed or the result is invalid.
    """
    tmp_path = final_path.with_suffix(final_path.suffix + ".part")
    # Ensure any stale .part is removed
    try:
        if tmp_path.exists():
            tmp_path.unlink()
    except Exception:
        pass

    try:
        synth_save(tts_client, text, voice_id, str(tmp_path))
    except Exception:
        # If the synth call itself raised, clean up and fail
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        return False

    # Some engines log errors but still write files; validate before committing
    if not is_valid_wav(tmp_path):
        try:
            tmp_path.unlink()
        except Exception:
            pass
        return False

    # Atomically move into place
    os.replace(str(tmp_path), str(final_path))
    return True


# Add this helper near the top of your file:
def synth_save(tts_client: Any, text: str, voice_id: str, out_path: str) -> None:
    """
    Call the wrapper with the right signature across engines.
    Prefers synth_to_file(); falls back to synth() with keyword args.
    """

    # 1) Preferred: synth_to_file(text, filename, voice_id=...)
    if hasattr(tts_client, "synth_to_file"):
        try:
            return tts_client.synth_to_file(text, out_path, voice_id=voice_id)
        except TypeError:
            # Some impls might use 'voice' instead of 'voice_id'
            return tts_client.synth_to_file(text, out_path, voice=voice_id)

    # 2) Fallback: synth() but make sure we pass filename as a keyword
    if hasattr(tts_client, "synth"):
        # Try common keyword names for the output file
        for kw in ("outfile", "output_path", "filename", "path"):
            try:
                return tts_client.synth(text, voice_id=voice_id, **{kw: out_path})
            except TypeError:
                continue
        # Absolute last resort: some clients accept format='wav' only and write elsewhere
        # (Not recommended, but avoids crashing.)
        return tts_client.synth(text, voice_id)

    raise RuntimeError("TTS client exposes neither synth_to_file nor synth")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate audio files for alphabet data using TTS engines"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip generating audio for files that already exist (default: True)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of all audio files (overrides --skip-existing)"
    )
    args = parser.parse_args()

    # If --force is specified, don't skip existing files
    skip_existing = not args.force if args.force else args.skip_existing

    generate_audio_files(skip_existing=skip_existing)
