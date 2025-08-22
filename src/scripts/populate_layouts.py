import json
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# Manual mapping for language names that don't match directly
LANGUAGE_NAME_MAPPING = {
    "US": "English",
    "United Kingdom": "English",
    "United States-Dvorak": "English",
    "United States-International": "English",
    "Canadian French": "French",
    "Swiss French": "French",
    "Belgian French": "French",
    "Latin American": "Spanish",
    "Swiss German": "German",
    "Bangla": "Bengali",
    "Faeroese": "Faroese",
    "Norwegian with Sami": "Norwegian",
    "Swedish with Sami": "Swedish",
    "Sami Extended Norway": "Northern Sami",
    "Sami Extended Finland-Sweden": "Northern Sami",
}


def get_driver_name(session: requests.Session, url: str) -> str | None:
    """Fetches the driver name from a kbdlayout.info page."""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the "Layout File" table row
        layout_file_header = soup.find("th", string=re.compile(r"Layout File"))
        if layout_file_header:
            layout_file_cell = layout_file_header.find_next_sibling("td")
            if layout_file_cell:
                # Driver name is like KBDGR.DLL, we want KBDGR
                driver_name = layout_file_cell.text.strip()
                if driver_name.upper().endswith(".DLL"):
                    return driver_name[:-4]
                return driver_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None


def main() -> None:
    """
    Populates index.json with keyboard layouts and generates a driver mapping.
    """
    data_root = Path("data")
    index_path = data_root / "index.json"
    kbdlayouts_path = data_root / "kbdlayouts.json"
    driver_mapping_path = data_root / "mappings" / "layout_to_driver.json"

    with open(index_path, "r", encoding="utf-8") as f:
        index_data: List[Dict[str, Any]] = json.load(f)

    with open(kbdlayouts_path, "r", encoding="utf-8") as f:
        kbdlayouts_data: Dict[str, Any] = json.load(f)

    # Clear existing keyboard lists
    for entry in index_data:
        if "keyboards" in entry:
            entry["keyboards"] = []

    # Create a lookup for language name to its entry in index_data
    lang_name_to_entry: Dict[str, Dict[str, Any]] = {
        entry["language-name"]: entry for entry in index_data
    }

    layout_to_driver: Dict[str, str] = {}

    session = requests.Session()

    for layout_id, layout_info in kbdlayouts_data.items():
        lang_name = layout_info.get("language")
        if not lang_name:
            continue

        # Handle special cases
        lang_name = LANGUAGE_NAME_MAPPING.get(lang_name, lang_name)

        if lang_name in lang_name_to_entry:
            # Add layout_id to the keyboards list
            lang_entry = lang_name_to_entry[lang_name]
            if "keyboards" not in lang_entry:
                lang_entry["keyboards"] = []
            if layout_id not in lang_entry["keyboards"]:
                lang_entry["keyboards"].append(layout_id)

            # Get the driver name
            href = layout_info.get("href")
            if href:
                url = f"http://kbdlayout.info{href}"
                driver_name = get_driver_name(session, url)
                if driver_name:
                    layout_to_driver[layout_id] = driver_name
                    print(f"Mapped {layout_id} ({lang_name}) to {driver_name}")
                else:
                    print(f"Could not find driver for {layout_id} ({lang_name})")

    # Write updated index.json
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Updated {index_path}")

    # Write layout_to_driver.json
    driver_mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with open(driver_mapping_path, "w", encoding="utf-8") as f:
        json.dump(layout_to_driver, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote driver mapping to {driver_mapping_path}")


if __name__ == "__main__":
    main()
