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

            try:
                tts_client.synth(phrase, voice_id, str(out_path))
                print(f"  -> Saved to {out_path}")
                generated += 1
            except Exception as e:
                print(
                    f"  Could not generate audio for {lang_code} ({engine_slug}{'' if count == 1 else f' #{count}'}): {e}"
                )

    print(
        f"\nAudio generation complete. Files created: {generated}. "
        f"Skipped (no phrase): {skipped_no_phrase}. Skipped (no voices): {skipped_no_voices}."
    )


if __name__ == "__main__":
    generate_audio_files()
