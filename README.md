# WorldAlphabets

A tool to access alphabets of the world with Python and Node interfaces.

## Usage

### Python

To load the data in Python:

```python
from worldalphabets import get_available_codes, load_alphabet

codes = get_available_codes()
print("Loaded", len(codes), "alphabets")

alphabet = load_alphabet("en")
print(alphabet.uppercase[:5])  # ['A', 'B', 'C', 'D', 'E']
print(alphabet.frequency['e'])
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
  getAvailableCodes,
} = require('worldalphabets');

async function main() {
  const codes = await getAvailableCodes();
  console.log('Available codes (first 5):', codes.slice(0, 5));

  const uppercaseEn = await getUppercase('en');
  console.log('English uppercase:', uppercaseEn);

  const lowercaseFr = await getLowercase('fr');
  console.log('French lowercase:', lowercaseFr);

  const frequencyDe = await getFrequency('de');
  console.log('German frequency for "a":', frequencyDe['a']);
}

main();
```

TypeScript projects receive typings automatically via `index.d.ts`.

#### Local Usage

If you have cloned the repository, you can use the module directly:

```javascript
const { getUppercase } = require('./index');

async function main() {
    const uppercaseEn = await getUppercase('en');
    console.log('English uppercase:', uppercaseEn);
}

main();
```

### Examples

The `examples/` directory contains small scripts demonstrating the library:

- `examples/python/` holds Python snippets for printing alphabets, collecting
  stats, and more.
- `examples/node/` includes similar examples for Node.js.

### Alphabet Index

This library also provides an index of all available alphabets with additional metadata.

#### Python

```python
from worldalphabets import get_index_data, get_language

# Get the entire index
index = get_index_data()
print(f"Index contains {len(index)} languages.")

# Get information for a specific language
lang_info = get_language("he")
print(f"Language: {lang_info['language-name']}")
print(f"Script Type: {lang_info['script-type']}")
print(f"Direction: {lang_info['direction']}")
```

#### Node.js

```javascript
const { getIndexData, getLanguage } = require('worldalphabets');

async function main() {
  // Get the entire index
  const index = await getIndexData();
  console.log(`Index contains ${index.length} languages.`);

  // Get information for a specific language
  const langInfo = await getLanguage('he');
  console.log(`Language: ${langInfo['language-name']}`);
  console.log(`Script Type: ${langInfo['script-type']}`);
  console.log(`Direction: ${langInfo['direction']}`);
}

main();
```

### Keyboard Layouts

Key entries expose `pos` (a [`KeyboardEvent.code`](https://developer.mozilla.org/docs/Web/API/KeyboardEvent/code) when available) along with `row`, `col`, and size information.

#### Python

A helper in `examples/keyboard_md_table.py` renders a layout as a Markdown
table:

```python
from examples.keyboard_md_table import layout_to_markdown

print(layout_to_markdown("en-united-kingdom"))
```

Output:


| ` | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 | - | = |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q | w | e | r | t | y | u | i | o | p | [ | ] |
| a | s | d | f | g | h | j | k | l | ; | ' | # |
| z | x | c | v | b | n | m | , | . | / |

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

## Exanmple Usages

- [examples/python](examples/python) – Python scripts demonstrating usage
- [examples/node](examples/node) – Node.js scripts demonstrating usage

Examples include printing alphabets, collecting stats, and more.


## Supported Languages

For a detailed list of supported languages and their metadata, including available
keyboard layouts, see the [Alphabet Table](table.md).

## Developer Guide

This project uses the
[kalenchukov/Alphabet](https://github.com/kalenchukov/Alphabet) Java repository as
the source for alphabet data. A helper script clones the repository, scans all
`*Alphabet.java` files, downloads a sample Wikipedia article for supported
languages, and writes JSON files containing the alphabet and estimated letter
frequencies. A second utility can replace those estimates with corpus
frequencies from the [Simia unigrams dataset](http://simia.net/letters/).

Each JSON file includes:

- `alphabetical` – letters of the alphabet (uppercase when the script has
  case)
- `uppercase` – uppercase letters
- `lowercase` – lowercase letters
- `frequency` – relative frequency of each lowercase letter (zero when no
  sample text is available)

Example JSON snippet:

```json
{
  "alphabetical": ["A", "B", ],
  "uppercase": ["A", "B", ],
  "lowercase": ["a", "b",],
  "frequency": {"a": 0.084, "b": 0.0208, ]
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

**Extract alphabets**

```bash
uv run scripts/extract_alphabets.py
```

The script clones the Java project and stores JSON files for every available
alphabet under `data/alphabets/`, named by ISO language code. If no sample text
is available, frequency values default to zero and the language is recorded in
`data/todo_languages.csv` for follow-up.

**Update letter frequencies**

```bash
uv run scripts/update_frequencies.py
```

This script downloads the `unigrams.zip` archive and rewrites each alphabet's
frequency mapping using the published counts.

**Generate alphabets from locale data**

Derive an alphabet from an ICU locale's exemplar character set:

```bash
uv run scripts/generate_alphabet_from_locale.py <code> --locale <locale>
```

The script writes `data/alphabets/<code>.json`, using the locale's standard
exemplar set for the base letters and populating frequency values from the
Simia unigrams dataset when available. Locales without exemplar data are
skipped.

**Generate alphabets from unigrams**

For languages present in the Simia dataset but missing here:

```bash
uv run scripts/generate_alphabet_from_unigrams.py <code> --locale <locale> \
  --block <Unicode block>
```

The script writes `data/alphabets/<code>.json`. To list missing codes:

```bash
uv run scripts/missing_unigram_languages.py
```

**Generate missing alphabets**

Create alphabet files for every language in the Simia unigrams dataset that
does not yet have one:

```bash
uv run scripts/generate_missing_alphabets.py --limit 10
```

Omit `--limit` to process all missing languages. Each file is written under
`data/alphabets/` and combines ICU exemplar characters with Simia frequencies.

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
- [Kblayout](https://kblayout.info/)

## Future work

- Add sample text or unigram support for more languages.
