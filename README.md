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

# Language detection (see Language Detection section for details)
from worldalphabets import optimized_detect_languages
results = optimized_detect_languages("Hello world")  # Automatic detection
print("Detected languages:", results)
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


#### ES Modules (Browser / Node ESM)

If your project uses ES modules (e.g. Vite/webpack/Next.js or `"type": "module"` in Node), you can import directly. The ES module build also supports automatic candidate selection for language detection.

```javascript
import { getAvailableCodes, getScripts, detectLanguages } from 'worldalphabets';

const codes = await getAvailableCodes();
console.log('Available codes (first 5):', codes.slice(0, 5));

// Automatic candidate selection (pass null). Also works in the browser.
const textKo = '나는 매우 행복하고 돈이 많이 있습니다.';
const top = await detectLanguages(textKo, null, {}, 3);
console.log(top);
// e.g. [['ko', 0.1203], ['ja', ...], ...]
```

Notes:
- CommonJS (`require`) API requires `candidateLangs` (array) for detection.
- ES Module (`import`) API supports `candidateLangs = null` and will select smart candidates via character analysis.
- Both builds share the same detection algorithm; ES module uses `fetch()` to load data (browser-friendly), CommonJS uses `fs`.

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

### Diacritic Utilities

Both interfaces provide helpers to work with diacritic marks.

#### Python

```python
from worldalphabets import strip_diacritics, has_diacritics

strip_diacritics("café")  # "cafe"
has_diacritics("é")       # True
```

#### Node.js

```javascript
const { stripDiacritics, hasDiacritics } = require('worldalphabets');

stripDiacritics('café'); // 'cafe'
hasDiacritics('é');      // true
```

Use `characters_with_diacritics`/`charactersWithDiacritics` to extract letters
with diacritic marks from a list.

Use `get_diacritic_variants`/`getDiacriticVariants` to list base letters and
their diacritic forms for a given language.

```python
from worldalphabets import get_diacritic_variants

get_diacritic_variants("pl", "Latn")["L"]  # ["L", "Ł"]
```

```javascript
const { getDiacriticVariants } = require('worldalphabets');

getDiacriticVariants('pl').then((v) => v.L); // ['L', 'Ł']
```

### Language Detection

The library provides two language detection approaches:

1. **Word-based detection** (primary): Uses Top-1000 frequency lists for languages with available word frequency data
2. **Character-based fallback**: For languages without frequency data, analyzes character sets and character frequencies from alphabet data

#### Automatic Detection (Recommended)

The optimized detection automatically selects candidate languages using character analysis:

```python
from worldalphabets import optimized_detect_languages

# Automatic detection - analyzes ALL 310+ languages intelligently
optimized_detect_languages("Hello world")
# [('en', 0.158), ('de', 0.142), ('fr', 0.139)]

optimized_detect_languages("Аҧсуа бызшәа")  # Abkhazian
# [('ab', 0.146), ('ru', 0.136), ('bg', 0.125)]

optimized_detect_languages("ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ")  # Coptic
# [('cop', 0.077)]

# Still supports manual candidate specification
optimized_detect_languages("Hello world", candidate_langs=['en', 'de', 'fr'])
# [('en', 0.158), ('de', 0.142), ('fr', 0.139)]
```

#### Manual Candidate Selection

The original detection requires you to specify candidate languages:

```python
from worldalphabets import detect_languages

# Must specify candidate languages
detect_languages("Hello world", candidate_langs=['en', 'de', 'fr'])
# [('en', 0.158), ('de', 0.142), ('fr', 0.139)]

detect_languages("Аҧсуа бызшәа", candidate_langs=['ab', 'ru', 'bg'])
# [('ab', 0.146), ('ru', 0.136), ('bg', 0.125)]
```

#### Node.js (Manual Candidates Required)

```javascript
const { detectLanguages } = require('worldalphabets');

// Must specify candidate languages
detectLanguages('Hello world', ['en', 'de', 'fr']).then(console.log);
// [['en', 0.158], ['de', 0.142], ['fr', 0.139]]

detectLanguages('ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ', ['cop', 'el', 'ar']).then(console.log);
// [['cop', 0.077], ['el', 0.032], ['ar', 0.021]]
```

The detection system supports **310+ languages** total: 86 with word frequency data and 224+ with character-based analysis.

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

The alphabet builder preserves the ordering from CLDR exemplar lists and
places diacritic forms immediately after their base letters when the CLDR
index omits them. For languages with tonal variants such as Vietnamese,
common tone marks are stripped before deduplication to avoid generating
separate entries for every tone combination.

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

#### Consolidated Pipeline (Recommended)

The WorldAlphabets project uses a unified Python-based data collection pipeline:

```bash
# Build complete dataset with all stages
uv run scripts/build_data_pipeline.py

# Build with verbose output
uv run scripts/build_data_pipeline.py --verbose

# Run specific pipeline stage
uv run scripts/build_data_pipeline.py --stage build_alphabets

# Build single language
uv run scripts/build_data_pipeline.py --language mi --script Latn
```

**Pipeline Stages:**
1. **collect_sources** - Download CLDR, ISO 639-3, frequency data
2. **build_language_registry** - Create comprehensive language database
3. **build_alphabets** - Generate alphabet files from CLDR + fallbacks
4. **build_translations** - Add "Hello, how are you?" translations
5. **build_keyboards** - Generate keyboard layout files
6. **build_top1000** - Generate Top-1000 token lists for detection
7. **build_tts_index** - Index available TTS voices
8. **build_audio** - Generate audio files using TTS
9. **build_index** - Create searchable indexes and metadata
10. **validate_data** - Comprehensive data validation

For detailed pipeline documentation, see [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md).

#### Legacy Individual Scripts (Deprecated)

The following individual scripts are deprecated in favor of the consolidated pipeline:

**Add ISO language codes**
```bash
uv run scripts/add_iso_codes.py  # Use: --stage build_language_registry
```

**Fetch language-script mappings**
```bash
uv run scripts/fetch_language_scripts.py  # Use: --stage collect_sources
```

**Build alphabets from CLDR**
```bash
uv run scripts/build_alphabet_from_cldr.py  # Use: --stage build_alphabets
```

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
uv run scripts/populate_layouts.py
```

To skip languages that already have keyboard data:

```bash
uv run scripts/populate_layouts.py --skip-existing
```

### Linting and type checking

```bash
ruff check .
mypy .
```

### Top-1000 token lists

The language detection helpers rely on comprehensive frequency lists for each language.
These lists contain the 1000 most common words per language, sourced from real external
data sources like HermitDave FrequencyWords, Leipzig Corpora, and Tatoeba sentences.
This provides significantly improved accuracy over the previous top-200 approach.

For major languages (French, English, Spanish), the expanded lists include:
- Common vocabulary: "heureux" (happy), "argent" (money), "travail" (work)
- Numbers, colors, family terms, everyday objects
- Improved word coverage: 60% → 80% for typical sentences

The lists are generated using a unified 5-priority pipeline that maximizes
coverage across as many languages as we can:

```bash
# Generate expanded frequency lists
uv run python scripts/expand_to_top1000.py
```

**Priority Sources (in order):**
1. **Leipzig Corpora Collection** - High-quality news/web corpora (CC-BY)
2. **HermitDave FrequencyWords** - OpenSubtitles/Wikipedia sources (CC-BY)
3. **Tatoeba sentences** - Sentence-based extraction (CC-BY 2.0 FR)
4. **Existing alphabet frequency data** - Character-level fallback
5. **Simia unigrams** - CJK character data

The script writes results to ``data/freq/top1000`` with build reports in
``BUILD_REPORT_UNIFIED.json``. The unified pipeline also runs within the
consolidated data pipeline as the ``build_top1000`` stage.

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

