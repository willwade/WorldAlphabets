# WorldAlphabets

<div align="center">
  <img src="web/public/logo.png" alt="World Alphabets Logo" width="200" height="auto">
</div>

A tool to access alphabets of the world with Python and Node interfaces.

## Usage

### Python

Install the package:

```bash
pip install worldalphabets
```

To load the data in Python (omitting ``script`` uses the first script listed):

```python
from worldalphabets import get_available_codes, get_scripts, load_alphabet

codes = get_available_codes()
print("Loaded", len(codes), "alphabets")

alphabet = load_alphabet("en")  # defaults to first script (Latn)
print("English uppercase:", alphabet.uppercase[:5])
print("English digits:", alphabet.digits)

scripts = get_scripts("mr")
print("Marathi scripts:", scripts)

alphabet_mr = load_alphabet("mr", script=scripts[0])
print("Marathi uppercase:", alphabet_mr.uppercase[:5])
print("Marathi frequency for 'a':", alphabet_mr.frequency["a"])

# Example with Arabic digits
alphabet_ar = load_alphabet("ar", "Arab")
print("Arabic digits:", alphabet_ar.digits)
```

### Node.js

#### From npm

Install the package from npm:

```bash
npm install worldalphabets
```

Then, you can use the functions in your project:

```javascript
const {
  getUppercase,
  getLowercase,
  getFrequency,
  getDigits,
  getAvailableCodes,
  getScripts,
} = require('worldalphabets');

async function main() {
  const codes = await getAvailableCodes();
  console.log('Available codes (first 5):', codes.slice(0, 5));

  const scriptsSr = await getScripts('sr');
  console.log('Serbian scripts:', scriptsSr);

  const uppercaseSr = await getUppercase('sr', scriptsSr[0]);
  console.log('Serbian uppercase:', uppercaseSr);

  const lowercaseFr = await getLowercase('fr');
  console.log('French lowercase:', lowercaseFr);

  const frequencyDe = await getFrequency('de');
  console.log('German frequency for "a":', frequencyDe['a']);

  const digitsAr = await getDigits('ar', 'Arab');
  console.log('Arabic digits:', digitsAr);
}

main();
```

TypeScript projects receive typings automatically via `index.d.ts`.

#### Local Usage

If you have cloned the repository, you can use the module directly:

```javascript
const { getUppercase } = require('./index');

async function main() {
    const uppercaseSr = await getUppercase('sr', 'Latn');
    console.log('Serbian Latin uppercase:', uppercaseSr);
}

main();
```

### Examples

The `examples/` directory contains small scripts demonstrating the library:

- `examples/python/` holds Python snippets for printing alphabets, collecting
  stats, listing scripts, and more.
- `examples/node/` includes similar examples for Node.js.

### Audio Samples

Audio recordings are stored under `data/audio/` and named
`{langcode}_{engine}_{voiceid}.wav`. Available voices are listed in
`data/audio/index.json`.

### Web Interface

The Vue app under `web/` compiles to a static site with `npm run build`.
To work on the interface locally, install its dependencies and start the
development server:

```bash
cd web
npm install
npm run dev
```
GitHub Pages publishes the contents of `web/dist` through a workflow that
runs on every push to `main`.

Each language view is addressable at `/<code>`, allowing pages to be
bookmarked directly.

### Alphabet Index

This library also provides an index of all available alphabets with additional metadata.

#### Python

```python
from worldalphabets import get_index_data, get_language, get_scripts

# Get the entire index
index = get_index_data()
print(f"Index contains {len(index)} languages.")

# Show available scripts for Serbian
scripts = get_scripts("sr")
print(f"Serbian scripts: {scripts}")

# Load Marathi in the Latin script
marathi_latn = get_language("mr", script="Latn")
print(f"Script: {marathi_latn['script']}")
print(f"First letters: {marathi_latn['alphabetical'][:5]}")
```

#### Node.js

```javascript
const { getIndexData, getLanguage, getScripts } = require('worldalphabets');

async function main() {
  // Get the entire index
  const index = await getIndexData();
  console.log(`Index contains ${index.length} languages.`);

  // Show available scripts for Serbian
  const scripts = await getScripts('sr');
  console.log(`Serbian scripts: ${scripts}`);

  // Load Marathi in the Latin script
  const marathiLatn = await getLanguage('mr', 'Latn');
  console.log(`Script: ${marathiLatn.script}`);
  console.log(`First letters: ${marathiLatn.alphabetical.slice(0, 5)}`);
}

main();
```

### Keyboard Layouts

Key entries expose `pos` (a [`KeyboardEvent.code`](https://developer.mozilla.org/docs/Web/API/KeyboardEvent/code) when available) along with `row`, `col`, and size information.

#### Python

The script `examples/python/keyboard_md_table.py` demonstrates rendering a
layout as a Markdown table. Copy the `layout_to_markdown` helper into your
project and use it like this:

```python
from keyboard_md_table import layout_to_markdown

print(layout_to_markdown("en-united-kingdom"))
```

Output:


| ` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 | - | = |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q | w | e | r | t | y | u | i | o | p | [ | ] |  |
| a | s | d | f | g | h | j | k | l | ; | ' | # |  |
| z | x | c | v | b | n | m | , | . | / |  |  |  |
| ␠ |  |  |  |  |  |  |  |  |  |  |  |  |

or with --offset flag

| ` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 | - | = |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | q | w | e | r | t | y | u | i | o | p | [ | ] |
|  | a | s | d | f | g | h | j | k | l | ; | ' | # |
|  |  | z | x | c | v | b | n | m | , | . | / |  |
|  |  |  |  |  | ␠ |  |  |  |  |  |  |  |

#### Node.js

```javascript
const {
  getAvailableLayouts,
  loadKeyboard,
  getUnicode,
} = require('worldalphabets');

async function main() {
  const layouts = await getAvailableLayouts();
  console.log('Available layouts (first 5):', layouts.slice(0, 5));

  const kb = await loadKeyboard('en-us');
  console.log('First key Unicode:', getUnicode(kb.keys[1], 'base'));
  console.log('First key position:', kb.keys[1].pos, kb.keys[1].row, kb.keys[1].col);
}

main();
```

## Supported Languages

For a detailed list of supported languages and their metadata, including available
keyboard layouts, see the [Alphabet Table](table.md).

## Developer Guide

Older versions of this project relied on a Java repository and assorted helper
scripts to scrape alphabets and estimate letter frequencies. Those utilities
have been deprecated in favor of a cleaner pipeline based on Unicode CLDR and
Wikidata. The remaining scripts focus on fetching language–script mappings and
building alphabet JSON files directly from CLDR exemplar characters, enriching
them with frequency counts from the Simia dataset or OpenSubtitles when
available.

Each JSON file includes:

- `language` – English language name
- `iso639_3` – ISO 639-3 code
- `iso639_1` – ISO 639-1 code when available
- `alphabetical` – letters of the alphabet (uppercase when the script has
  case)
- `uppercase` – uppercase letters
- `lowercase` – lowercase letters
- `frequency` – relative frequency of each lowercase letter (zero when no
  sample text is available)

Example JSON snippet:

```json
{
  "language": "English",
  "iso639_3": "eng",
  "iso639_1": "en",
  "alphabetical": ["A", "B"],
  "uppercase": ["A", "B"],
  "lowercase": ["a", "b"],
  "frequency": {"a": 0.084, "b": 0.0208}
}
```

### Setup

This project uses `uv` for dependency management. To set up the development
environment:

```bash
# Install uv
pipx install uv

# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e '.[dev]'
```

### Data Generation

**Add ISO language codes**

```bash
uv run scripts/add_iso_codes.py
```

Adds English language names and ISO 639 codes to each alphabet JSON.

**Fetch language-script mappings**

```bash
uv run scripts/fetch_language_scripts.py
```

Queries Wikidata for the scripts used by each language and writes
`data/language_scripts.json` mapping ISO codes to ISO 15924 script codes.

**Build alphabets from CLDR**

Generate alphabet files from CLDR exemplar character data:

```bash
uv run scripts/build_alphabet_from_cldr.py <language> <script>
```

To build alphabets for every language-script pair in the mapping file:

```bash
uv run scripts/build_alphabet_from_cldr.py --manifest data/language_scripts.json
```

Each file is written to `data/alphabets/<language>-<script>.json` and combines
CLDR exemplar characters with letter frequencies, preferring the Simia unigrams
dataset when available and otherwise falling back to OpenSubtitles word
frequencies. Locales missing from the CLDR dataset are skipped automatically.

We verified the importer on English, Spanish, Russian, Arabic, Hindi, Kurdish
(Latin and Arabic scripts), and Greek. The generated alphabets matched or
improved on existing data—Spanish gained accented vowels and Arabic shed
contextual forms—so this CLDR-based pipeline is now the recommended way to
refresh alphabet JSON files.

**Generate translations**

Populate a sample translation for each alphabet using Google Translate. The
script iterates over every language and script combination, writing a
`hello_how_are_you` field to `data/alphabets/<code>-<script>.json`.

```bash
GOOGLE_TRANS_KEY=<key> uv run scripts/generate_translations.py
```

To skip languages that already have translations:

```bash
GOOGLE_TRANS_KEY=<key> uv run scripts/generate_translations.py --skip-existing
```

**Populate keyboard layouts**

To refresh keyboard layout references after restructuring, run:

```bash
uv run src/scripts/populate_layouts.py
```

To skip languages that already have keyboard data:

```bash
uv run src/scripts/populate_layouts.py --skip-existing
```

### Linting and type checking

```bash
ruff check .
mypy .
```

## Sources

- [kalenchukov/Alphabet](https://github.com/kalenchukov/Alphabet)
- [Simia unigrams dataset](http://simia.net/letters/)
- [Wikipedia](https://wikipedia.org)
- [ICU locale data](http://site.icu-project.org/)
- [Unicode](https://unicode.org/)
- [Kbdlayout](https://kbdlayout.info)


## Licence Info

- This project is licensed under the MIT License.
- Data sourced from [kalenchukov/Alphabet](https://github.com/kalenchukov/Alphabet) is licensed under the Apache 2.0 License. 
- Data sourced from [Simia unigrams dataset](http://simia.net/letters/) (Data from [Wiktionary](https://wiktionary.org)) is licensed under the Creative Commons Attribution-ShareAlike License.
- Data sourced from [Wikipedia](https://wikipedia.org) is licensed under the Creative Commons Attribution-ShareAlike License. 

