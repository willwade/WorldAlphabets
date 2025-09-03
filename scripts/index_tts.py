import os
import json
import platform
from typing import Any, Dict, List
from tts_wrapper import (
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

def load_existing_index(path: str = "data/tts_index.json") -> Dict[str, List[Dict[str, Any]]]:
    """Loads an existing TTS index file if it exists."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {path}. Starting with an empty index.")
                return {}
    return {}

def save_index(data: Dict[str, List[Dict[str, Any]]], path: str = "data/tts_index.json") -> None:
    """Saves the TTS index to a file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nTTS voice index saved to {path}")

def clear_voices_for_providers(index: Dict[str, List[Dict[str, Any]]], providers_to_clear: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Removes all voices from the index for the given list of providers."""
    if not providers_to_clear:
        return index
    print(f"Clearing old voices for providers: {providers_to_clear}")
    for lang_code in index:
        index[lang_code] = [
            voice for voice in index[lang_code] if voice.get('engine') not in providers_to_clear
        ]
    return index

def add_voice_to_index(all_voices: Dict[str, List[Dict[str, Any]]], engine_name: str, voice_obj: Any) -> None:
    """Adds a single voice to the index, handling different voice object structures."""
    try:
        voice_id = voice_obj.get('id') if isinstance(voice_obj, dict) else voice_obj.name
        name = voice_obj.get('name') if isinstance(voice_obj, dict) else voice_obj.name
        gender_val = voice_obj.get('gender') if isinstance(voice_obj, dict) else getattr(voice_obj, 'gender', 'unknown')
        gender = str(gender_val).upper()

        language_codes = voice_obj.get('language_codes') if isinstance(voice_obj, dict) else getattr(voice_obj, 'language_codes', [])
        if not language_codes:
            lang = voice_obj.get('language') or voice_obj.get('locale')
            if lang:
                language_codes = [lang]

        if not language_codes: # Still no language codes, can't index
            return

        for lang_code_full in language_codes:
            lang_code = lang_code_full.split('-')[0]
            if lang_code not in all_voices:
                all_voices[lang_code] = []

            voice_entry = {
                'engine': engine_name,
                'voice_id': voice_id,
                'name': name,
                'gender': gender,
                'language_code': lang_code_full
            }
            if voice_entry not in all_voices[lang_code]:
                all_voices[lang_code].append(voice_entry)
    except Exception as e:
        print(f"  - Could not process a voice from {engine_name}: {e}")


def main() -> None:
    """
    Indexes available TTS voices. This script is additive, preserving voices
    from platforms other than the one it's currently running on.
    """
    all_voices = load_existing_index()

    configured_clients: List[tuple[str, Any]] = []

    # --- Detect configured clients ---
    if os.getenv("POLLY_AWS_KEY_ID"):
        configured_clients.append(("polly", PollyClient(credentials=(os.getenv("POLLY_REGION"), os.getenv("POLLY_AWS_KEY_ID"), os.getenv("POLLY_AWS_ACCESS_KEY")))))
    if os.getenv("MICROSOFT_TOKEN"):
        configured_clients.append(("microsoft", MicrosoftTTS(credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION")))))
    if os.getenv("WATSON_API_KEY"):
        configured_clients.append(("watson", WatsonClient(credentials=(os.getenv("WATSON_API_KEY"), os.getenv("WATSON_REGION"), os.getenv("WATSON_INSTANCE_ID")))))
    if os.getenv("GOOGLE_SA_PATH"):
        configured_clients.append(("google", GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH"))))
    if os.getenv("ELEVENLABS_API_KEY"):
        configured_clients.append(("elevenlabs", ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY"))))
    if os.getenv("WITAI_TOKEN"):
        configured_clients.append(("witai", WitAiClient(credentials=(os.getenv("WITAI_TOKEN"),))))
    if os.getenv("OPENAI_API_KEY"):
        configured_clients.append(("openai", OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))))
    if os.getenv("UPLIFTAI_KEY"):
        configured_clients.append(("upliftai", UpliftAIClient(api_key=os.getenv("UPLIFTAI_KEY"))))

    try:
        configured_clients.append(("sherpaonnx", SherpaOnnxClient()))
    except Exception:
        pass
    try:
        configured_clients.append(("espeak", eSpeakClient()))
    except Exception:
        pass
    if platform.system() == "Darwin":
        try:
            configured_clients.append(("avsynth", AVSynthClient()))
        except Exception:
            pass

    # --- Clear old voices for configured providers ---
    providers_to_clear = [client_info[0] for client_info in configured_clients]
    all_voices = clear_voices_for_providers(all_voices, providers_to_clear)

    # --- Index voices for configured providers ---
    for engine_name, client in configured_clients:
        print(f"Indexing voices for {engine_name}...")
        try:
            voices = client.get_voices()
            for voice in voices:
                add_voice_to_index(all_voices, engine_name, voice)
            print(f"  -> Finished indexing {engine_name}.")
        except Exception as e:
            print(f"Could not get voices for {engine_name}: {e}")

    save_index(all_voices)

if __name__ == "__main__":
    main()
