import os
import json
import langcodes

# Define paths
ALPHABETS_DIR = os.path.join("data", "alphabets")
INDEX_FILE = os.path.join("data", "index.json")

# Manual mapping for language names that differ from Wikipedia
MANUAL_LANG_MAP = {
    "bn": "Bengali",
    "zh-min-nan": "Min",
    "zh-yue": "Yue",
    "zh": "Mandarin",
    "mo": "Romanian",  # Moldovan is a dialect of Romanian
    "tl": "Tagalog",
}

def get_direction_for_script(script_name: str | None) -> str:
    """
    Returns the writing direction for a given script.
    """
    if script_name is None:
        return "TBD"
    rtl_scripts = ["Arab", "Hebr", "Thaa", "Syrc", "Phli", "Phnx", "Nkoo", "Adlm"]
    if script_name in rtl_scripts:
        return "rtl"
    return "ltr"

def create_index() -> None:
    """
    Generates the index.json file.
    """
    index = []

    for filename in sorted(os.listdir(ALPHABETS_DIR)):
        if filename.endswith(".json"):
            lang_code = filename.split(".")[0]
            filepath = os.path.join(ALPHABETS_DIR, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            frequency_avail = sum(data.get("frequency", {}).values()) > 0

            if lang_code in MANUAL_LANG_MAP:
                language_name = MANUAL_LANG_MAP[lang_code]
            else:
                try:
                    language_name = langcodes.Language.get(lang_code).display_name()
                except langcodes.LanguageTagError:
                    language_name = lang_code

            language = langcodes.Language.get(lang_code).maximize()
            script = language.script
            if script:
                script_name = language.script_name()
            else:
                script_name = "TBD"

            direction = get_direction_for_script(script)

            index.append({
                "language": lang_code,
                "language-name": language_name,
                "frequency-avail": frequency_avail,
                "script-type": script_name,
                "direction": direction,
            })

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    create_index()
