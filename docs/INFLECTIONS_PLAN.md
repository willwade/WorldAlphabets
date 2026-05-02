# Inflections Data Plan

## Goal

Add language-neutral word form and inflection-rule datasets to WorldAlphabets.
The data should support broad morphology and word-form use cases, not only one
communication workflow or product category.

## Naming

Use neutral names in paths, scripts, public APIs, and metadata:

- `inflections`
- `word forms`
- `rules`
- `morphology`

Avoid product- or use-case-specific names in public interfaces.

## Data Layout

Published data lives in the existing category-based `data/` structure:

```text
data/inflections/
  index.json
  <locale>/
    words.json
    rules.json
```

Generation artifacts live separately from published data:

```text
data/sources/inflections/
  manifest.json
  batches/
  raw_results/
  validation_reports/
```

Packaged Python data is synced to:

```text
src/worldalphabets/data/inflections/
```

This follows the current repository pattern where final runtime data is grouped
by type, while raw and intermediate materials live under `data/sources/`.

## Published Files

Each locale directory contains two files:

- `words.json`: word-level part of speech, base-form, priority, antonym,
  example, and inflection data.
- `rules.json`: rule, test, substitution, and cardinal-location data.

The top-level index records available locales and lightweight metadata:

```json
{
  "_type": "inflection_index",
  "_version": "0.1",
  "locales": {
    "en": {
      "words": "en/words.json",
      "rules": "en/rules.json",
      "base_locale": null,
      "priority_batch": 1,
      "word_count": 1000,
      "rule_count": 0
    }
  }
}
```

## Locale Strategy

Support as many languages as the repository can reasonably provide inputs for.
The first generation batch should prioritize the languages listed in
`MorphPRD.txt`, but the infrastructure should discover later candidates from
existing WorldAlphabets data.

Candidate discovery uses:

- `data/index.json` for language/script metadata.
- `data/freq/top1000/*.txt` for ranked tokens.

The first priority batch is:

```text
en, en-GB, en-CA, en-AU, en-NZ, en-ZA
es, es-419, eu, ca
fr, fr-CA
pt, pt-BR
de, nl, nl-BE, da, no, sv, fo, af
ru, uk, pl, cs, sk, sl, hr
ar, he
fi
cy
```

For regional variants, prefer a base-language pack plus overrides unless the
variant has meaningful spelling or morphology differences.

## Generation Workflow

1. Build `data/sources/inflections/manifest.json` from PRD-priority locales,
   the language index, and available frequency lists.
2. Prepare JSONL batch request files under `data/sources/inflections/batches/`.
3. Upload the JSONL files with `scripts/inflections_batch.py`, or keep them for
   manual upload.
4. Store downloaded raw results under `data/sources/inflections/raw_results/`.
5. Ingest results into `data/inflections/<locale>/`.
6. Regenerate `data/inflections/index.json`.
7. Sync runtime data into `src/worldalphabets/data/inflections/`.

## Validation

Validation should be intentionally strict about structural integrity but
language-neutral about grammatical labels.

Required checks:

- `words.json` has `_type: "words"`, `_locale`, and `_version`.
- Each word entry has `types` and `inflections`.
- `priority`, when present, is an integer from 1 to 10.
- `rules.json` has `_type: "rules"`, `_locale`, and `_version`.
- Each rule has `id`, `type`, and either `inflection` or `overrides`.
- Rule tests are arrays with at least pre-text, word, and post-text.
- `inflection_locations` entries use valid cardinal locations.

Coverage checks are separate from structural validation. Use
`scripts/report_inflections.py` to compare generated word counts against the
ranked frequency-list inputs, and fail CI or review gates with `--min-coverage`
once a target coverage threshold is agreed.

## Bulk Data Sources

LLM generation is useful for bootstrapping rules and filling gaps, but it should
not be the only route to large word-form inventories.

Preferred source order for bulk word forms:

1. Curated/generated morphology tables such as UniMorph where available.
2. Language-specific finite-state analyzers/generators such as HFST/GiellaLT,
   Omorfi, Voikko, or Apertium where installable and license-compatible.
3. Wiktionary-derived data via Wiktextract for languages with strong coverage.
4. Chunked LLM generation for languages or forms not covered by deterministic
   sources.

HFST is best treated as an optional provider layer, not a universal dependency.
It can generate high-quality forms for languages with available transducers, but
coverage, installation, tags, and licenses differ by language.

Deterministic source imports use `scripts/import_inflection_sources.py`.
Supported inputs:

- UniMorph TSV: `lemma<TAB>form<TAB>features`
- Wiktextract JSONL: entries with `word`, `pos`, and `forms`
- HFST-style normalized TSV: `base<TAB>form<TAB>tags<TAB>part_of_speech`
- Previously normalized JSONL rows

Examples:

```bash
uv run python scripts/fetch_inflection_sources.py \
  --source unimorph \
  --locales ar,ca,fr,pt

uv run python scripts/import_inflection_sources.py \
  --locale fi \
  --source-type hfst-tsv \
  --input data/sources/inflections/providers/fi/omorfi.tsv \
  --source-name omorfi \
  --write-normalized

uv run python scripts/import_inflection_sources.py \
  --locale en \
  --source-type unimorph \
  --input data/sources/inflections/providers/en/unimorph.tsv \
  --source-name unimorph
```

By default imports are filtered to the locale frequency list so generated packs
stay focused on useful words. Use `--all-forms` for full source imports.

## Public Interfaces

Python:

```python
get_available_inflection_locales()
load_inflection_words(locale)
load_inflection_rules(locale)
load_inflection_data(locale)
get_word_forms(locale, word)
inflect_word(locale, word, inflection)
```

Node:

```js
getAvailableInflectionLocales()
loadInflectionWords(locale)
loadInflectionRules(locale)
loadInflectionData(locale)
getWordForms(locale, word)
inflectWord(locale, word, inflection)
```

C should expose read-only lookup helpers once the JSON shape is stable and the
generated-data size is understood.

No .NET project is currently present in this repository. A .NET wrapper can use
the same JSON paths or the C ABI once the target package location is known.

## Initial Implementation Scope

The first infrastructure pass should add:

- Manifest generation.
- Batch JSONL preparation.
- Structural validation.
- Runtime data sync.
- Python and Node loaders.

Actual generated language data can be added incrementally after reviewing the
first batch outputs.

Rules can be generated separately after word inventories are available:

```bash
uv run python scripts/build_inflection_tests.py --locales ar,ca,pt
uv run --with requests python scripts/inflections_batch.py submit \
  --batch-file data/sources/inflections/batches/<tests-batch>.jsonl
uv run python scripts/ingest_inflection_tests.py --input <downloaded-output.jsonl>

uv run python scripts/build_inflection_rules.py --locales ar,ca,pt
uv run --with requests python scripts/inflections_batch.py submit \
  --batch-file data/sources/inflections/batches/<rules-batch>.jsonl
uv run python scripts/ingest_inflection_rules.py --input <downloaded-output.jsonl>
uv run python scripts/validate_inflections.py
```

The demo-tools runtime reads tests from `rules.json.tests`; `tests.csv` is the
authoring format. Run `scripts/sync_inflection_tests.py` after editing or
generating `tests.csv` so the browser/runtime contract stays valid.

## Batch Commands

Submit the latest prepared JSONL batch:

```bash
uv run python scripts/inflections_batch.py submit
```

Check the latest submitted batch:

```bash
uv run python scripts/inflections_batch.py status
```

Download results once the batch is complete:

```bash
uv run python scripts/inflections_batch.py download
```

Ingest downloaded results into published data files:

```bash
uv run python scripts/ingest_inflections.py
uv run python scripts/validate_inflections.py
uv run python scripts/report_inflections.py --expected-limit 100
```
