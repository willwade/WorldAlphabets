from typing import Any

from pydantic import BaseModel


class LayerLegends(BaseModel):
    base: str | None = None
    shift: str | None = None
    caps: str | None = None
    altgr: str | None = None
    shift_altgr: str | None = None
    ctrl: str | None = None
    alt: str | None = None

class KeyEntry(BaseModel):
    pos: str | None = None
    hid: str | None = None
    row: int | None = None
    col: int | None = None
    shape: dict[str, float] | None = None
    vk: str | None = None
    sc: str | None = None
    legends: LayerLegends
    dead: bool = False
    notes: list[str] = []

    def get_unicode(self, layer: str) -> str | None:
        char = getattr(self.legends, layer, None)
        if char:
            return f"U+{ord(char):04X}"
        return None

class DeadKey(BaseModel):
    name: str | None = None
    trigger: str
    compose: dict[str, str]

class Ligature(BaseModel):
    keys: list[str]
    output: str

class KeyboardLayout(BaseModel):
    id: str
    name: str
    source: str
    iso_variant: str | None = None
    flags: dict[str, bool] = {}
    keys: list[KeyEntry] = []
    dead_keys: list[DeadKey] | None = None
    ligatures: list[Ligature] | None = None
    meta: dict[str, Any] = {}
