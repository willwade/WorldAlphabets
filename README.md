# WorldAlphabets
A tool to access alphabets of the world with Python and Node interfaces.

## Supported Languages

Alphabet JSON files are available for these ISO language codes
(language names from [langcodes](https://pypi.org/project/langcodes/)):

| Code | Language |
|------|----------|
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

## Getting Started

This project uses the
[kalenchukov/Alphabet](https://github.com/kalenchukov/Alphabet) Java repository as
the source for alphabet data. A helper script clones the repository, scans all
`*Alphabet.java` files, downloads a sample Wikipedia article for supported
languages, and writes JSON files containing the alphabet and estimated letter
frequencies. A second utility can replace those estimates with corpus
frequencies from the [Simia unigrams dataset](http://simia.net/letters/).

### Setup

```bash
pip install -r requirements-dev.txt
```

### Extract alphabets

```bash
python scripts/extract_alphabets.py
```

The script clones the Java project and stores JSON files for every available
alphabet under `data/alphabets/`, named by ISO language code. If no sample text
is available, frequency values default to zero and the language is recorded in
`data/todo_languages.csv` for follow-up. Each file includes:

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

To load the data in Python:

```python
from worldalphabets import load_alphabet

alphabet = load_alphabet("en")
print(alphabet.uppercase[:5])  # ['A', 'B', 'C', 'D', 'E']
print(alphabet.frequency['e'])
```

To load the data in Node.js:

```javascript
const { loadAlphabet } = require('./index');

loadAlphabet('en').then((alphabet) => {
  console.log(alphabet.uppercase.slice(0, 5)); // ['A', 'B', 'C', 'D', 'E']
  console.log(alphabet.frequency['e']);
});
```

### Update letter frequencies

```bash
python scripts/update_frequencies.py
```

This script downloads the `unigrams.zip` archive and rewrites each alphabet's
frequency mapping using the published counts.

### Linting and type checking

```bash
ruff check .
mypy .
```

## Future work

- Add sample text or unigram support for more languages.
