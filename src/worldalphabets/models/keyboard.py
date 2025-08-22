from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class LayerLegends(BaseModel):
    base: Optional[str] = None
    shift: Optional[str] = None
    caps: Optional[str] = None
    altgr: Optional[str] = None
    shift_altgr: Optional[str] = None
    ctrl: Optional[str] = None
    alt: Optional[str] = None

class KeyEntry(BaseModel):
    pos: Optional[str] = None
    row: Optional[int] = None
    col: Optional[int] = None
    shape: Optional[Dict[str, float]] = None
    vk: Optional[str] = None
    sc: Optional[str] = None
    legends: LayerLegends
    dead: bool = False
    notes: List[str] = []

    def get_unicode(self, layer: str) -> Optional[str]:
        char = getattr(self.legends, layer, None)
        if char:
            return f"U+{ord(char):04X}"
        return None

class DeadKey(BaseModel):
    name: Optional[str] = None
    trigger: str
    compose: Dict[str, str]

class Ligature(BaseModel):
    keys: List[str]
    output: str

class KeyboardLayout(BaseModel):
    id: str
    name: str
    source: str
    iso_variant: Optional[str] = None
    flags: Dict[str, bool] = {}
    keys: List[KeyEntry] = []
    dead_keys: Optional[List[DeadKey]] = None
    ligatures: Optional[List[Ligature]] = None
    meta: Dict[str, Any] = {}
