import json
from importlib.resources import files

INDEX_FILE = files("worldalphabets") / "data" / "index.json"

_index_data = None

def get_index_data():
    """
    Loads the index.json data.
    """
    global _index_data
    if _index_data is None:
        _index_data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return _index_data

def get_language(lang_code):
    """
    Returns information for a specific language.
    """
    data = get_index_data()
    for item in data:
        if item['language'] == lang_code:
            return item
    return None
