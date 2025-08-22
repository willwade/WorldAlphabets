import json

INDEX_FILE = "data/index.json"
TABLE_FILE = "table.md"

def generate_table() -> None:
    """
    Generates a Markdown table from the index.json file.
    """
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(TABLE_FILE, "w", encoding="utf-8") as f:
        f.write(
            "| Language | Language Name | Frequency Available | Script Type | Direction | Keyboards |\n"
        )
        f.write("|---|---|---|---|---|---|\n")

        for item in data:
            keyboards = ", ".join(item.get("keyboards", [])) or "-"
            f.write(
                f"| {item['language']} | {item['language-name']} | {item['frequency-avail']} | {item['script-type']} | {item['direction']} | {keyboards} |\n"
            )

if __name__ == "__main__":
    generate_table()
