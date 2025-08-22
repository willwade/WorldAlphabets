from lxml import etree as ET
from typing import Dict, List, Tuple, Any, Optional

from worldalphabets.models.keyboard import KeyEntry, LayerLegends, DeadKey

def get_layer_name(modifiers: Optional[str], right_alt_is_alt_gr: bool) -> Optional[str]:
    if not modifiers:
        return "base"
    mods = set(modifiers.split())
    if right_alt_is_alt_gr and "VK_CONTROL" in mods and "VK_MENU" in mods:
        mods.remove("VK_CONTROL")
        mods.remove("VK_MENU")
        mods.add("VK_ALTGR")
    layer_map = {
        "VK_SHIFT": "shift", "VK_CAPITAL": "caps", "VK_ALTGR": "altgr",
        "VK_SHIFT VK_ALTGR": "shift_altgr", "VK_CONTROL": "ctrl", "VK_MENU": "alt"
    }
    return layer_map.get(" ".join(sorted(list(mods))))

def parse_keyboard_layout_xml(xml_content: str) -> Tuple[Dict[str, Any], List[KeyEntry], List[DeadKey]]:
    parser = ET.XMLParser(recover=True, resolve_entities=False)
    root = ET.fromstring(xml_content, parser=parser)
    flags = {
        "rightAltIsAltGr": root.attrib.get("RightAltIsAltGr") == "true",
        "shiftCancelsCapsLock": root.attrib.get("ShiftCancelsCapsLock") == "true",
        "changesDirectionality": root.attrib.get("ChangesDirectionality") == "true",
    }
    right_alt_is_alt_gr = flags["rightAltIsAltGr"]
    keys: List[KeyEntry] = []
    dead_keys: List[DeadKey] = []
    for pk in root.findall(".//PK"):
        legends: Dict[str, Optional[str]] = {}
        is_dead = False
        for result in pk.findall("./Result"):
            layer_name = get_layer_name(result.attrib.get("With"), right_alt_is_alt_gr)
            dead_key_table = result.find("DeadKeyTable")
            if dead_key_table is not None:
                is_dead = True
                trigger = dead_key_table.attrib.get("Accent")
                if trigger:
                    compositions = {}
                    for d in dead_key_table.findall("Result"):
                        base_char = d.attrib.get("With")
                        composed_char = d.attrib.get("Text")
                        if base_char and composed_char:
                            compositions[base_char] = composed_char
                    dead_keys.append(DeadKey(name=dead_key_table.attrib.get("Name"), trigger=trigger, compose=compositions))
                    if layer_name:
                        legends[layer_name] = trigger
            elif layer_name:
                legends[layer_name] = result.attrib.get("Text")
        keys.append(KeyEntry(vk=pk.attrib.get("VK"), sc=pk.attrib.get("SC"), legends=LayerLegends.model_validate(legends), dead=is_dead))
    return flags, keys, dead_keys

def parse_kbd_dll_xml(xml_content: str) -> Tuple[Dict[str, Any], List[KeyEntry], List[DeadKey]]:
    parser = ET.XMLParser(recover=True, resolve_entities=False)
    root = ET.fromstring(xml_content, parser=parser)

    modifiers_node = root.find(".//MODIFIERS")
    if modifiers_node is None:
        return {}, [], []

    mod_numbers_str = modifiers_node.attrib.get("ModNumber")
    if not mod_numbers_str:
        return {}, [], []

    mod_numbers = [int(n) for n in mod_numbers_str.split()]
    layer_map = {0: "base", 1: "shift", 2: "ctrl", 3: "caps", 4: "altgr", 5: "shift_altgr"}
    keys: List[KeyEntry] = []
    for vktw in root.findall(".//VK_TO_WCHARS"):
        vk = vktw.attrib.get("VirtualKey")
        wch_codes = vktw.attrib.get("Wch", "").split()
        legends: Dict[str, Optional[str]] = {}
        for i, code_str in enumerate(wch_codes):
            if i < len(mod_numbers):
                mod_num = mod_numbers[i]
                layer_name = layer_map.get(mod_num)
                if layer_name:
                    try:
                        char_code = int(code_str, 16)
                        if char_code > 0 and char_code < 0xF000:
                            legends[layer_name] = chr(char_code)
                    except ValueError:
                        pass
        keys.append(KeyEntry(vk=vk, sc=None, legends=LayerLegends.model_validate(legends), dead=False))
    return {}, keys, []

def parse_xml(xml_content: str) -> Tuple[Dict[str, Any], List[KeyEntry], List[DeadKey]]:
    if "<KbdDll>" in xml_content:
        return parse_kbd_dll_xml(xml_content)
    elif "<KeyboardLayout" in xml_content:
        return parse_keyboard_layout_xml(xml_content)
    else:
        raise NotImplementedError("This XML format is not supported yet.")
