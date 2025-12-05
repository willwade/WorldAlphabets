import pytest
from worldalphabets import (
    generate_c_header,
    get_available_layouts,
    load_keyboard,
    KeyboardLayout,
    find_layouts_by_keycode,
    extract_layers,
    DEFAULT_LAYERS,
    load_alphabet,
    get_available_codes,
    load_frequency_list,
    get_scripts,
    get_index_data,
    get_language,
)


def test_get_available_layouts() -> None:
    layouts = get_available_layouts()
    assert isinstance(layouts, list)
    assert "de-DE-qwertz" in layouts
    assert "en-GB-qwerty" in layouts


def test_load_german_layout() -> None:
    layout = load_keyboard("de-DE-qwertz")
    assert isinstance(layout, KeyboardLayout)
    assert layout.id == "de-DE-qwertz"

    # Check flags
    assert layout.flags.get("rightAltIsAltGr") is True

    # Check a specific key (Q)
    q_key = next((k for k in layout.keys if k.vk == "VK_Q"), None)
    assert q_key is not None
    assert q_key.legends.base == "q"
    assert q_key.legends.shift == "Q"
    assert q_key.legends.altgr == "@"

    # Check a dead key
    dead_key = next((k for k in layout.keys if k.dead), None)
    assert dead_key is not None
    assert layout.dead_keys is not None
    assert len(layout.dead_keys) > 0
    assert layout.dead_keys[0].trigger == "´"
    assert layout.dead_keys[0].compose.get("a") == "á"


def test_get_unicode() -> None:
    layout = load_keyboard("de-DE-qwertz")
    e_key = next((k for k in layout.keys if k.vk == "VK_E"), None)
    assert e_key is not None
    assert e_key.get_unicode("base") == "U+0065"
    assert e_key.get_unicode("altgr") == "U+20AC"


def test_load_uk_layout() -> None:
    layout = load_keyboard("en-GB-qwerty")
    assert isinstance(layout, KeyboardLayout)
    assert layout.id == "en-GB-qwerty"

    # Check a specific key
    quote_key = next((k for k in layout.keys if k.vk == "VK_OEM_3"), None)
    assert quote_key is not None
    assert quote_key.legends.shift == "@"

    # This layout should have no dead keys
    assert not layout.dead_keys


def test_load_non_existent_layout() -> None:
    with pytest.raises(
        ValueError, match="Keyboard layout 'non-existent-layout' not found."
    ):
        load_keyboard("non-existent-layout")


def test_generate_c_header() -> None:
    header = generate_c_header(
        "fr-french-standard-azerty",
        layers=["base", "shift", "altgr", "shift_altgr"],
        guard=False,
    )
    assert "keyboard_layout_t" in header
    assert '{ 0x04, "q" }' in header
    assert '{ 0x14, "a" }' in header
    assert ".layer_count = 4u" in header


def test_find_layouts_by_keycode() -> None:
    matches = find_layouts_by_keycode("IntlBackslash", layer="base")
    ids = [m["id"] for m in matches]
    assert "fr-french-standard-azerty" in ids
    fr = next(m for m in matches if m["id"] == "fr-french-standard-azerty")
    assert fr["legend"] == "<"


def test_extract_layers() -> None:
    layout = load_keyboard("de-DE-qwertz")
    layers = extract_layers(layout, ["base", "shift", "altgr"])
    assert "base" in layers
    assert "shift" in layers
    assert "altgr" in layers
    # Check specific mappings
    assert layers["base"]["VK_Q"] == "q"
    assert layers["shift"]["VK_Q"] == "Q"
    assert layers["altgr"]["VK_Q"] == "@"


def test_default_layers() -> None:
    # Verify DEFAULT_LAYERS is available and has expected values
    assert "base" in DEFAULT_LAYERS
    assert "shift" in DEFAULT_LAYERS
    assert "altgr" in DEFAULT_LAYERS


# ========== Alphabet API Tests ==========


def test_load_alphabet() -> None:
    alpha = load_alphabet("en")
    assert len(alpha.uppercase) == 26
    assert len(alpha.lowercase) == 26
    assert "a" in alpha.frequency
    assert alpha.frequency["a"] > 0


def test_load_alphabet_with_script() -> None:
    alpha = load_alphabet("mr", script="Latn")
    assert len(alpha.uppercase) > 0


def test_load_alphabet_invalid() -> None:
    with pytest.raises(FileNotFoundError):
        load_alphabet("nonexistent-language")


def test_get_available_codes() -> None:
    codes = get_available_codes()
    assert isinstance(codes, list)
    assert len(codes) > 10
    assert "en" in codes
    assert "fr" in codes


def test_load_frequency_list() -> None:
    freq = load_frequency_list("en")
    assert freq.language == "en"
    assert len(freq.tokens) > 100
    assert freq.mode in ("word", "bigram")


def test_load_frequency_list_invalid() -> None:
    with pytest.raises(FileNotFoundError):
        load_frequency_list("nonexistent")


def test_get_scripts() -> None:
    # Chinese should have multiple scripts
    scripts = get_scripts("zh")
    assert isinstance(scripts, list)
    assert len(scripts) > 0


def test_get_index_data() -> None:
    data = get_index_data()
    assert isinstance(data, list)
    assert len(data) > 10
    # Each entry should have language field
    for entry in data[:5]:
        assert "language" in entry


def test_get_language() -> None:
    lang = get_language("en")
    assert lang is not None
    assert "uppercase" in lang
    assert "lowercase" in lang


def test_get_language_invalid() -> None:
    lang = get_language("nonexistent")
    assert lang is None
