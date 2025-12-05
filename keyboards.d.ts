export type KeyboardLayout = {
  id: string;
  name: string;
  source: string;
  iso_variant?: string;
  flags: {
    rightAltIsAltGr?: boolean;
    shiftCancelsCapsLock?: boolean;
    changesDirectionality?: boolean;
  };
  keys: KeyEntry[];
  dead_keys?: DeadKey[];
  ligatures?: Ligature[];
  meta?: Record<string, unknown>;
};

export type KeyEntry = {
  pos?: string;
  row?: number;
  col?: number;
  shape?: { w?: number; h?: number; x?: number; y?: number; w2?: number; h2?: number; x2?: number; y2?: number; };
  vk?: string;
  sc?: string;
  legends: Partial<LayerLegends>;
  dead?: boolean;
  notes?: string[];
};

export type LayerLegends = {
  base: string | null;
  shift: string | null;
  caps: string | null;
  altgr: string | null;
  shift_altgr: string | null;
  ctrl: string | null;
  alt: string | null;
};

export type LayerName = keyof LayerLegends;

export type DeadKey = {
  name?: string;
  trigger: string;
  compose: Record<string, string>;
};

export type Ligature = {
  keys: string[];
  output: string;
};

export function getAvailableLayouts(): Promise<string[]>;
export function loadKeyboard(layoutId: string): Promise<KeyboardLayout>;
export function getUnicode(keyEntry: KeyEntry, layer: LayerName): string | null;
export const DEFAULT_LAYERS: LayerName[];
export function extractLayers(
  layout: KeyboardLayout,
  layers?: LayerName[]
): Record<string, Record<string, string>>;
export type CHeaderOptions = {
  layers?: LayerName[];
  guard?: boolean;
  symbolName?: string;
};
export function generateCHeader(
  layoutId: string,
  options?: CHeaderOptions
): Promise<string>;
export type KeycodeMatch = {
  id: string;
  name: string;
  legend: string;
  layer: LayerName;
};
export function findLayoutsByKeycode(
  keycode: string | number,
  layer?: LayerName
): Promise<KeycodeMatch[]>;
