#!/usr/bin/env python3
import os
import json
import platform
from pathlib import Path
from typing import Any, Optional, Dict, List

from tts_wrapper import (
    ElevenLabsClient,
    GoogleClient,
    MicrosoftTTS,
    OpenAIClient,
    PollyClient,
    SherpaOnnxClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)

# Platform-specific imports
if platform.system() == "Darwin":  # macOS
    from tts_wrapper import AVSynthClient

ALPHABETS_DIR = Path("data/alphabets")
TTS_INDEX_PATH = Path("data/tts_index.json")
OUTPUT_DIR = Path("web/audio")
TEXT_FIELD = "hello_how_are_you"  # field added by your translate step


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
            if os.getenv("GOOGLE_SA_PATH"):
                client = GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH"))
        elif engine_name == "elevenlabs":
            if os.getenv("ELEVENLABS_API_KEY"):
                client = ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY"))
        elif engine_name == "witai":
            if os.getenv("WITAI_TOKEN"):
                client = WitAiClient(credentials=(os.getenv("WITAI_TOKEN"),))
        elif engine_name == "openai":
            if os.getenv("OPENAI_API_KEY"):
                client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
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


def safe_engine_suffix(engine: str) -> str:
    s = (engine or "").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in s) or "engine"


def generate_audio_files() -> None:
    """
    Iterate alphabet files (the source of truth), synth audio for each voice found in
    tts_index.json that matches the alphabet's language code, using the phrase in TEXT_FIELD.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    alphabet_langs = sorted(p.stem for p in ALPHABETS_DIR.glob("*.json"))

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

        voices = tts_index.get(lang_code) or []
        if not voices:
            print(f"Skipping {lang_code} (no TTS voices listed in tts_index.json).")
            skipped_no_voices += 1
            continue

        engine_counts: Dict[str, int] = {}

        for voice_info in voices:
            engine = voice_info.get("engine")
            voice_id = voice_info.get("voice_id")
            if not engine or not voice_id:
                print(f"  Skipping {lang_code} (invalid voice entry: {voice_info}).")
                continue

            engine_slug = safe_engine_suffix(engine)
            count = engine_counts.get(engine_slug, 0) + 1
            engine_counts[engine_slug] = count

            suffix = f"_{engine_slug}" + (f"_{count}" if count > 1 else "")
            out_path = OUTPUT_DIR / f"{lang_code}{suffix}.wav"

            if out_path.exists():
                print(
                    f"Skipping {lang_code} ({engine_slug}{'' if count == 1 else f' #{count}'}): already exists."
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
            else:
                print(
                    f"  Skipped (invalid/failed synth) for {lang_code} ({engine_slug}{'' if count == 1 else f' #{count}'})."
                )
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
    generate_audio_files()
