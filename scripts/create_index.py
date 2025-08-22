import os
import json
import requests
from bs4 import BeautifulSoup
import langcodes

# Define paths
ALPHABETS_DIR = os.path.join("data", "alphabets")
INDEX_FILE = os.path.join("data", "index.json")
TABLE_FILE = "table.md"

# Wikipedia URLs
WRITING_SYSTEMS_URL = "https://en.wikipedia.org/wiki/List_of_writing_systems"
ISO_639_1_URL = "https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes"

def get_language_info():
    """
    Scrapes Wikipedia to get language information.
    Returns a dictionary mapping language codes to their names.
    """
    response = requests.get(ISO_639_1_URL)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        table = soup.find("table", {"class": "wikitable"}).find("tbody")
    except AttributeError:
        raise ValueError("Could not find the language table on the Wikipedia page.")

    lang_code_to_name = {}

    for row in table.find_all("tr")[1:]:  # Skip header row
        columns = row.find_all("td")
        if len(columns) > 4:
            # The ISO 639-1 code is in the 4th column
            iso_code = columns[3].get_text(strip=True)
            # The language name is in the 5th column
            lang_name_cell = columns[4]
            lang_name_link = lang_name_cell.find("a")
            if lang_name_link:
                lang_name = lang_name_link.get_text(strip=True)
            else:
                lang_name = lang_name_cell.get_text(strip=True)

            if iso_code and lang_name:
                lang_code_to_name[iso_code] = lang_name

    return lang_code_to_name

def get_direction_for_script(script_name):
    """
    Returns the writing direction for a given script.
    """
    rtl_scripts = ["Arabic", "Hebrew", "Thaana", "Syriac", "Pahlavi", "Phoenician", "N'Ko", "Adlam"]
    if any(rtl_script in script_name for rtl_script in rtl_scripts):
        return "rl"
    return "lr"

def get_script_info():
    """
    Scrapes Wikipedia to get script information.
    Returns a dictionary mapping language names to their script and direction.
    """
    response = requests.get(WRITING_SYSTEMS_URL)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all tables with class "wikitable"
    tables = soup.find_all("table", {"class": "wikitable"})

    # The table we want is the "List of writing systems by adoption"
    # Let's find it by looking for a specific header
    target_table = None
    for table in tables:
        headers = [header.get_text(strip=True) for header in table.find_all("th")]
        if "Name of script" in headers and "Languages associated with" in headers:
            target_table = table
            break

    if not target_table:
        raise ValueError("Could not find the target table on the Wikipedia page.")

    lang_to_script = {}

    for row in target_table.find_all("tr")[1:]:  # Skip header row
        columns = row.find_all(["td", "th"])
        if len(columns) > 3:
            script_name = columns[0].get_text(strip=True)
            script_type = columns[1].get_text(strip=True)
            direction = get_direction_for_script(script_name)

            # Get all language links in the 'Languages associated with' column
            languages_cell = columns[3]
            language_links = languages_cell.find_all("a")

            for link in language_links:
                lang_name = link.get_text(strip=True)
                if lang_name:
                    # Clean up the language name
                    lang_clean = lang_name.split('(')[0].strip()
                    if lang_clean and lang_clean not in lang_to_script:
                         lang_to_script[lang_clean] = {
                            "script-type": script_type,
                            "direction": direction
                        }

    return lang_to_script


# Manual mapping for language names that differ from Wikipedia
MANUAL_LANG_MAP = {
    "bn": "Bengali",
    "zh-min-nan": "Min",
    "zh-yue": "Yue",
    "zh": "Mandarin",
    "mo": "Romanian",  # Moldovan is a dialect of Romanian
    "tl": "Tagalog",
}

def create_index():
    """
    Generates the index.json file.
    """
    language_info = get_language_info()
    script_info = get_script_info()
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
                    language_name = language_info.get(lang_code, lang_code)

            # A more robust way to get script_data
            script_data = script_info.get(language_name)
            if not script_data:
                # Try matching with the first word of the language name
                script_data = script_info.get(language_name.split(" ")[0])
            if not script_data:
                # Try matching with the lang code
                if lang_code in script_info:
                    script_data = script_info[lang_code]
            if not script_data:
                script_data = {}

            script_type_raw = script_data.get("script-type", "TBD")
            script_type = script_type_raw.split('(')[0].strip().split(',')[0]
            direction = script_data.get("direction", "TBD")

            index.append({
                "language": lang_code,
                "language-name": language_name,
                "frequency-avail": frequency_avail,
                "script-type": script_type,
                "direction": direction,
            })

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    create_index()
