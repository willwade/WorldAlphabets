# WorldAlphabets

A tool to access alphabets of the world with Python and Node interfaces.

## Usage

### Python

To load the data in Python:

```python
from worldalphabets import load_alphabet

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
const { getUppercase, getLowercase, getFrequency, getAvailableCodes } = require('worldalphabets');

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

## Supported Languages

Alphabet JSON files are available for these ISO language codes
(language names from [langcodes](https://pypi.org/project/langcodes/)):

| Code | Language |
|------|----------|
| af | Afrikaans* |
| am | Amharic* |
| ar | Arabic |
| ba | Bashkir |
| ban | Balinese |
| bax | Bamun |
| be | Belarusian |
| bg | Bulgarian |
| bku | Buhid |
| bn | Bangla |
| bo | Tibetan |
| bug | Buginese |
| bya | Batak |
| chr | Cherokee |
| cop | Coptic |
| cs | Czech |
| de | German |
| el | Greek |
| en | English |
| eo | Esperanto |
| es | Spanish |
| fr | French |
| gez | Geez |
| gu | Gujarati |
| he | Hebrew |
| hnn | Hanunoo |
| hu | Hungarian |
| hy | Armenian |
| it | Italian |
| jv | Javanese |
| ka | Georgian |
| kk | Kazakh |
| km | Khmer |
| kn | Kannada |
| la | Latin |
| lep | Lepcha |
| lif | Limbu |
| lis | Lisu |
| lo | Lao |
| mid | Mandaic |
| ml | Malayalam |
| mn | Mongolian |
| my | Burmese |
| nqo | N’Ko |
| or | Odia |
| pl | Polish |
| rej | Rejang |
| ru | Russian |
| sam | Samaritan Aramaic |
| saz | Saurashtra |
| si | Sinhala |
| su | Sundanese |
| syr | Syriac |
| ta | Tamil |
| tbw | Tagbanwa |
| te | Telugu |
| th | Thai |
| tl | Filipino |
| tr | Turkish |
| tt | Tatar |
| uk | Ukrainian |
| vai | Vai |
| zh | Chinese |
| zra | Kara (Korea) |

*Alphabets derived from ICU exemplar sets; frequencies from Simia unigrams.*

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
  "alphabetical": ["A", "B", ...],
  "uppercase": ["A", "B", ...],
  "lowercase": ["a", "b", ...],
  "frequency": {"a": 0.084, "b": 0.0208, ...}
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
python scripts/extract_alphabets.py
```

The script clones the Java project and stores JSON files for every available
alphabet under `data/alphabets/`, named by ISO language code. If no sample text
is available, frequency values default to zero and the language is recorded in
`data/todo_languages.csv` for follow-up.

**Update letter frequencies**

```bash
python scripts/update_frequencies.py
```

This script downloads the `unigrams.zip` archive and rewrites each alphabet's
frequency mapping using the published counts.

**Generate alphabets from locale data**

Derive an alphabet from an ICU locale's exemplar character set:

```bash
python scripts/generate_alphabet_from_locale.py <code> --locale <locale> \
  --set-type index
```

The script writes `data/alphabets/<code>.json`, using the locale's index
exemplar set for the base letters and populating frequency values from the
Simia unigrams dataset when available.

**Generate alphabets from unigrams**

For languages present in the Simia dataset but missing here:

```bash
python scripts/generate_alphabet_from_unigrams.py <code> --locale <locale> \
  --block <Unicode block>
```

The script writes `data/alphabets/<code>.json`. To list missing codes:

```bash
python scripts/missing_unigram_languages.py
```

**Generate missing alphabets**

Create alphabet files for every language in the Simia unigrams dataset that
does not yet have one:

```bash
python scripts/generate_missing_alphabets.py --limit 10
```

Omit `--limit` to process all missing languages. Each file is written under
`data/alphabets/` and combines ICU exemplar characters with Simia frequencies.

### Linting and type checking

```bash
ruff check .
mypy .
```

## Future work

- Add sample text or unigram support for more languages.
