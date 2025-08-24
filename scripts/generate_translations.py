import os
import json
from google.cloud import translate_v2 as translate

def generate_translations() -> None:
    """
    Generates translations for the text "Hello, how are you?" for all languages
    in the data/index.json file.

    This script requires the GOOGLE_TRANS_KEY environment variable to be set
    with a valid Google Translate API key.

    The translations are saved to data/translations.json.
    """
    # Get API key from environment variable
    api_key = os.environ.get("GOOGLE_TRANS_KEY")
    if not api_key:
        print("Error: GOOGLE_TRANS_KEY environment variable not set.")
        print("Please set it to your Google Translate API key.")
        return

    # Initialize the translation client
    try:
        translate_client = translate.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Google Translate client: {e}")
        return

    # Load the language index
    try:
        with open("data/index.json", "r", encoding="utf-8") as f:
            languages = json.load(f)
    except FileNotFoundError:
        print("Error: data/index.json not found. Make sure you are running this script from the root of the project.")
        return

    text_to_translate = "Hello, how are you?"
    translations = {}

    print("Starting translation process...")
    for lang_info in languages:
        lang_code = lang_info["language"]
        lang_name = lang_info["language-name"]

        # Google Translate API may not support all language codes directly
        # For example, it uses 'zh-CN' for simplified Chinese, but the index might have 'zh'
        # We will try the code from the index first.
        target_code = lang_code
        if lang_code == 'zh':
            target_code = 'zh-CN' # Use simplified chinese for 'zh'

        print(f"Translating for {lang_name} ({target_code})...")

        try:
            result = translate_client.translate(text_to_translate, target_language=target_code)
            translations[lang_code] = result["translatedText"]
            print(f"  -> {result['translatedText']}")
        except Exception as e:
            print(f"Could not translate for {lang_name} ({lang_code}): {e}")
            # Add a placeholder to indicate that translation was attempted but failed
            translations[lang_code] = None

    # Save the translations to a file
    try:
        with open("data/translations.json", "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        print("\nTranslations saved to data/translations.json")
    except IOError as e:
        print(f"\nError saving translations to data/translations.json: {e}")

if __name__ == "__main__":
    generate_translations()
