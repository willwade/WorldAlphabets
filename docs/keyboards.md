# Keyboard Layouts

This document explains the keyboard layout feature of `worldalphabets`.

## Concept

The keyboard layout feature provides a standardized way to access keyboard layout information from different platforms (Windows, macOS, Linux/XKB).

### ISO/IEC 9995 Grid

To allow for consistent comparison between layouts, key positions are normalized to the **ISO/IEC 9995** standard grid. This grid assigns a unique code to each key based on its row and column. For example, the key that produces "E" on a QWERTY layout is at position `D03`.

### Layers

A key can produce different characters depending on the modifier keys pressed (e.g., Shift, AltGr). These are called "layers". The following layers are supported:
- `base`: No modifiers.
- `shift`: Shift key is pressed.
- `caps`: Caps Lock is active.
- `altgr`: AltGr (Right Alt) is pressed.
- `shift_altgr`: Shift and AltGr are pressed.

### Dead Keys

A dead key is a key that does not produce a character by itself, but modifies the character produced by the next key pressed. For example, pressing the dead key for `´` followed by `a` produces `á`.

### Ligatures

A ligature is a combination of two or more characters that are represented as a single glyph. For example, `f` and `f` can be combined to form `ﬀ`.

## Data Model

The keyboard layout data is structured according to a defined JSON schema. The main Pydantic/TypeScript types are:

### `KeyboardLayout`
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique identifier, e.g., "en-US-qwerty". |
| `name` | `string` | Human-readable name. |
| `source` | `string` | Data source (e.g., "kbdlayout.info"). |
| `iso_variant`| `string`| ISO variant (e.g., "ANSI-104"). |
| `flags` | `object` | Layout-specific flags. |
| `keys` | `KeyEntry[]` | List of keys in the layout. |
| `deadKeys` | `DeadKey[]` | List of dead key definitions. |
| `ligatures` | `Ligature[]` | List of ligature definitions. |

### `KeyEntry`
| Field | Type | Description |
|---|---|---|
| `pos` | `string` | ISO/IEC 9995 position. |
| `legends` | `LayerLegends` | Character output for each layer. |
| `...` | | Other fields for geometry, scan codes, etc. |

## How to Add a New Layout

To add a new layout, you need to:
1. Obtain the source data (e.g., Windows KLC file, XKB symbols file).
2. Write a parser in the `tools/` directory to convert the source data into the normalized JSON format.
3. Add the parser to the `wa-build-layouts` CLI tool.
4. Add the new layout ID to the `data/index.json` file under the corresponding language.

## Examples

### Python

```python
from worldalphabets import load_keyboard, get_available_layouts

# Get a list of all available layout IDs
layouts = get_available_layouts()
print(layouts)

# Load a specific layout
kb = load_keyboard("en-US-qwerty")

# Print all base characters
for key in kb.keys:
    if key.legends.base:
        print(key.legends.base, end=" ")
```

### Node.js

```javascript
const { loadKeyboard, getAvailableLayouts } = require('worldalphabets');

async function main() {
    // Get a list of all available layout IDs
    const layouts = await getAvailableLayouts();
    console.log(layouts);

    // Load a specific layout
    const kb = await loadKeyboard('en-US-qwerty');

    // Print all base characters
    const baseChars = kb.keys
        .map(k => k.legends.base)
        .filter(Boolean)
        .join(' ');
    console.log(baseChars);
}

main();
```
