import os
import json
import platform
from typing import Any, Optional
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

def get_tts_client(engine_name: str) -> Optional[Any]:
    """Initializes and returns a TTS client based on the engine name."""
    client = None
    try:
        if engine_name == 'polly':
            if os.getenv("POLLY_AWS_KEY_ID"):
                client = PollyClient(credentials=(os.getenv("POLLY_REGION"), os.getenv("POLLY_AWS_KEY_ID"), os.getenv("POLLY_AWS_ACCESS_KEY")))
        elif engine_name == 'microsoft':
            if os.getenv("MICROSOFT_TOKEN"):
                client = MicrosoftTTS(credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION")))
        elif engine_name == 'watson':
            if os.getenv("WATSON_API_KEY"):
                client = WatsonClient(credentials=(os.getenv("WATSON_API_KEY"), os.getenv("WATSON_REGION"), os.getenv("WATSON_INSTANCE_ID")))
        elif engine_name == 'google':
            if os.getenv("GOOGLE_SA_PATH"):
                client = GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH"))
        elif engine_name == 'elevenlabs':
            if os.getenv("ELEVENLABS_API_KEY"):
                client = ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY"))
        elif engine_name == 'witai':
            if os.getenv("WITAI_TOKEN"):
                client = WitAiClient(credentials=(os.getenv("WITAI_TOKEN"),))
        elif engine_name == 'openai':
            if os.getenv("OPENAI_API_KEY"):
                client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
        elif engine_name == 'sherpaonnx':
            client = SherpaOnnxClient()
        elif engine_name == 'espeak':
            client = eSpeakClient()
        elif engine_name == 'avsynth' and platform.system() == "Darwin":
            client = AVSynthClient()
    except Exception as e:
        print(f"  - Error initializing {engine_name} client: {e}")
        return None

    return client

def generate_audio_files() -> None:
    """
    Generates .wav files for each language using the translations and available
    TTS voices.
    """
    if not os.path.exists("web/audio"):
        os.makedirs("web/audio")

    try:
        with open("data/translations.json", "r", encoding="utf-8") as f:
            translations = json.load(f)
        with open("data/tts_index.json", "r", encoding="utf-8") as f:
            tts_index = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure you have run the translation and TTS indexing scripts first.")
        return

    print("Starting audio generation...")
    for lang_code, text in translations.items():
        if not text:
            print(f"Skipping {lang_code} (no translation).")
            continue

        if lang_code not in tts_index or not tts_index[lang_code]:
            print(f"Skipping {lang_code} (no TTS voice found).")
            continue

        voice_info = tts_index[lang_code][0]
        engine = voice_info['engine']
        voice_id = voice_info['voice_id']

        output_path = f"web/audio/{lang_code}.wav"

        if os.path.exists(output_path):
            print(f"Skipping {lang_code} (audio file already exists).")
            continue

        print(f"Generating audio for {lang_code} using {engine} voice {voice_id}...")

        tts_client = get_tts_client(engine)
        if not tts_client:
            print(f"  Could not initialize TTS client for {engine}. Check your environment variables.")
            continue

        try:
            tts_client.synth(text, voice_id, output_path)
            print(f"  -> Saved to {output_path}")
        except Exception as e:
            print(f"  Could not generate audio for {lang_code}: {e}")

    print("\nAudio generation complete.")

if __name__ == "__main__":
    generate_audio_files()
