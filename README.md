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

## Supported Languages

Alphabet JSON files are available for these ISO language codes
(language names from [langcodes](https://pypi.org/project/langcodes/)):

| Code | Language |
|------|----------|
| af | Afrikaans |
| ak | Akan |
| am | Amharic |
| ar | Arabic |
| ast | Asturian |
| az | Azerbaijani |
| ba | Bashkir |
| ban | Balinese |
| bax | Bamun |
| be | Belarusian |
| bg | Bulgarian |
| bku | Buhid |
| bm | Bambara |
| bn | Bangla |
| bo | Tibetan |
| bug | Buginese |
| bya | Batak |
| ca | Catalan |
| ceb | Cebuano |
| chr | Cherokee |
| ckb | Central Kurdish |
| cop | Coptic |
| cs | Czech |
| cv | Chuvash |
| da | Danish |
| de | German |
| dz | Dzongkha |
| el | Greek |
| en | English |
| eo | Esperanto |
| es | Spanish |
| et | Estonian |
| eu | Basque |
| fa | Persian |
| fi | Finnish |
| fo | Faroese |
| fr | French |
| fur | Friulian |
| ga | Irish |
| gd | Scottish Gaelic |
| gez | Geez |
| gl | Galician |
| gu | Gujarati |
| gv | Manx |
| haw | Hawaiian |
| he | Hebrew |
| hi | Hindi |
| hnn | Hanunoo |
| ht | Haitian Creole |
| hu | Hungarian |
| hy | Armenian |
| ie | Interlingue |
| is | Icelandic |
| it | Italian |
| ja | Japanese |
| jv | Javanese |
| ka | Georgian |
| kab | Kabyle |
| kk | Kazakh |
| kl | Kalaallisut |
| km | Khmer |
| kn | Kannada |
| ko | Korean |
| ks | Kashmiri |
| ksh | Colognian |
| ku | Kurdish |
| ky | Kyrgyz |
| la | Latin |
| lb | Luxembourgish |
| lep | Lepcha |
| lif | Limbu |
| lij | Ligurian |
| lis | Lisu |
| lo | Lao |
| lt | Lithuanian |
| lv | Latvian |
| mg | Malagasy |
| mid | Mandaic |
| mk | Macedonian |
| ml | Malayalam |
| mn | Mongolian |
| mo | Romanian |
| my | Burmese |
| mzn | Mazanderani |
| nds | Low German |
| ne | Nepali |
| nn | Norwegian Nynorsk |
| no | Norwegian |
| nqo | N’Ko |
| nso | Northern Sotho |
| oc | Occitan |
| or | Odia |
| pl | Polish |
| ps | Pashto |
| pt | Portuguese |
| rej | Rejang |
| rm | Romansh |
| ro | Romanian |
| ru | Russian |
| sa | Sanskrit |
| sam | Samaritan Aramaic |
| saz | Saurashtra |
| sc | Sardinian |
| se | Northern Sami |
| sg | Sango |
| si | Sinhala |
| sl | Slovenian |
| sn | Shona |
| so | Somali |
| sr | Serbian |
| su | Sundanese |
| sv | Swedish |
| syr | Syriac |
| szl | Silesian |
| ta | Tamil |
| tbw | Tagbanwa |
| te | Telugu |
| tg | Tajik |
| th | Thai |
| ti | Tigrinya |
| tk | Turkmen |
| tl | Filipino |
| tn | Tswana |
| tr | Turkish |
| tt | Tatar |
| uk | Ukrainian |
| ur | Urdu |
| vai | Vai |
| vec | Venetian |
| wo | Wolof |
| zh | Chinese |
| zh-classical | Classical Chinese |
| zh-min-nan | Min Nan Chinese |
| zh-yue | Cantonese |
| zra | Kara (Korea) |

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

## Future work

- Add sample text or unigram support for more languages.
