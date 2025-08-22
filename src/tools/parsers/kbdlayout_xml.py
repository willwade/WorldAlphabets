from lxml import etree as ET
from typing import Dict, List, Tuple, Any, Optional

from worldalphabets.models.keyboard import KeyEntry, LayerLegends, DeadKey

def get_layer_name(modifiers: Optional[str], right_alt_is_alt_gr: bool) -> Optional[str]:
    """Maps a 'With' attribute string to a LayerLegends field name."""
    if not modifiers:
        return "base"

    mods = set(modifiers.split())

    if right_alt_is_alt_gr:
        if "VK_CONTROL" in mods and "VK_MENU" in mods:
            mods.remove("VK_CONTROL")
            mods.remove("VK_MENU")
            mods.add("VK_ALTGR")

    if mods == {"VK_SHIFT"}:
        return "shift"
    if mods == {"VK_CAPITAL"}:
        return "caps"
    if mods == {"VK_ALTGR"}:
        return "altgr"
    if mods == {"VK_SHIFT", "VK_ALTGR"}:
        return "shift_altgr"
    if mods == {"VK_CONTROL"}:
        return "ctrl"
    if mods == {"VK_MENU"}:
        return "alt"

    # Handle other combinations if necessary, for now return None
    return None

def parse_kbdlayout_xml(xml_content: str) -> Tuple[Dict[str, Any], List[KeyEntry], List[DeadKey]]:
    # Use a recovering parser to handle badly-formed XML from the source
    parser = ET.XMLParser(recover=True)
    root = ET.fromstring(xml_content.encode('utf-8'), parser=parser)

    flags = {
        "rightAltIsAltGr": root.attrib.get("RightAltIsAltGr") == "true",
        "shiftCancelsCapsLock": root.attrib.get("ShiftCancelsCapsLock") == "true",
        "changesDirectionality": root.attrib.get("ChangesDirectionality") == "true",
    }
    right_alt_is_alt_gr = flags["rightAltIsAltGr"]

    keys: List[KeyEntry] = []
    dead_keys: List[DeadKey] = []

    for pk in root.findall(".//PK"):
        vk = pk.attrib.get("VK")
        sc = pk.attrib.get("SC")

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
                    for dead_result in dead_key_table.findall("Result"):
                        base_char = dead_result.attrib.get("With")
                        composed_char = dead_result.attrib.get("Text")
                        if base_char and composed_char:
                            compositions[base_char] = composed_char

                    dead_keys.append(DeadKey(
                        name=dead_key_table.attrib.get("Name"),
                        trigger=trigger,
                        compose=compositions
                    ))
                    if layer_name:
                        legends[layer_name] = trigger

            else:
                if layer_name:
                    legends[layer_name] = result.attrib.get("Text")

        keys.append(KeyEntry(
            vk=vk,
            sc=sc,
            legends=LayerLegends.model_validate(legends),
            dead=is_dead
        ))

    return flags, keys, dead_keys
