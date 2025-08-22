import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

def main() -> None:
    """
    Scrapes the main page of kbdlayout.info to build a mapping of layout names
    to driver file names.
    """
    print("Scraping kbdlayout.info...")

    url = "http://kbdlayout.info"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    layout_map = {}

    # Find all links that point to a driver file page
    driver_links = soup.find_all("a", href=re.compile(r"\/[A-Z0-9]+\/$"))

    for link in driver_links:
        href = link.get("href")
        # The driver name is the part between the slashes
        driver_name_match = re.match(r"\/([A-Z0-9]+)\/", href)
        if driver_name_match:
            driver_name = driver_name_match.group(1)
            # The KLID and layout name are in the previous `td`
            prev_td = link.parent.find_previous_sibling("td")
            if prev_td:
                layout_name = prev_td.get_text(strip=True)
                # We will use the layout name as the key.
                # This is not perfect, as some names are duplicated.
                # For now, we will just take the first one.
                if layout_name not in layout_map:
                    layout_map[layout_name] = driver_name

    output_path = Path("data/mappings/layout_to_driver.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(layout_map, f, indent=2, sort_keys=True)

    print(f"Successfully wrote {len(layout_map)} layout mappings to {output_path}")


if __name__ == "__main__":
    main()
