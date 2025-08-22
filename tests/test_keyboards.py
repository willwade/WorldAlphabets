import pytest
from worldalphabets import get_available_layouts, load_keyboard, KeyboardLayout

def test_get_available_layouts() -> None:
    layouts = get_available_layouts()
    assert isinstance(layouts, list)
    assert "de-DE-qwertz" in layouts

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


def test_load_non_existent_layout() -> None:
    with pytest.raises(ValueError, match="Keyboard layout 'non-existent-layout' not found."):
        load_keyboard("non-existent-layout")
