# Inflection Data Pipeline

## What We Are Building

WorldAlphabets will publish neutral word-form and inflection-rule datasets for
many locales. The data is intended to be useful anywhere software needs common
word forms, simple morphology, or context-sensitive word replacement.

Published data lives under:

```text
data/inflections/<locale>/
  words.json
  rules.json
  tests.csv        # authoring/review format when available
```

Packaged Python data is synced to:

```text
src/worldalphabets/data/inflections/<locale>/
```

Browser and Node package artifacts are generated from the same source files.

The runtime contract follows the existing demo-tools inflections implementation:

- `words.json` is a JSON object keyed by word.
- `rules.json.rules` contains executable rules.
- `rules.json.tests` contains runtime regression tests as arrays.
- `tests.csv` is only an authoring/import/export format and must be synced into
  `rules.json.tests` before publication.

## Why This Matters

The immediate compatibility target is the existing inflections demo/runtime at:

```text
https://tools.openaac.org/inflections/inflections.html
```

That runtime can:

- look up a word and its known forms;
- apply context-sensitive rules based on prior words;
- suggest replacements such as plural forms, verb forms, or pronoun forms;
- run a test suite against the rules and word data.

The broader use case is not tied to one AAC or communication workflow. These
datasets can also support:

- button coloring or part-of-speech hints;
- word-form pickers;
- grammar suggestions;
- text-entry assistance;
- educational language tools;
- offline embedded language utilities.

## Current Principles

1. Keep naming neutral: use `inflections`, `word forms`, `rules`, and
   `morphology` in code and public APIs.
2. Prefer curated or deterministic data over free-form generation when possible.
3. Generate tests before trusting rules.
4. Treat `tests.csv` as an authoring format and `rules.json.tests` as the
   runtime format.
5. Keep base-language packs canonical. Use regional packs only for real
   overrides.
6. Measure coverage. Do not accept tiny valid JSON as useful data.

## Current Generation Strategy

### 1. Canonical Imports

Where curated demo-compatible files already exist, import them first.

```bash
uv run python scripts/import_demo_inflections.py --locales en,es
uv run python scripts/sync_inflection_tests.py --locales en,es
uv run python scripts/validate_inflections.py
```

This currently gives English a strong baseline with thousands of words, dozens
of rules, and the existing broad test suite.

### 2. Deterministic Word-Form Sources

Use deterministic morphology sources to bulk out word inventories.

Supported import formats:

- UniMorph TSV: `lemma<TAB>form<TAB>features`
- Wiktextract JSONL: entries with `word`, `pos`, and `forms`
- HFST-style normalized TSV: `base<TAB>form<TAB>tags<TAB>part_of_speech`
- normalized JSONL rows from previous imports

Example:

```bash
uv run python scripts/fetch_inflection_sources.py \
  --source unimorph \
  --locales ar,ca,fr,pt

uv run python scripts/fetch_inflection_sources.py \
  --source unimorph \
  --all \
  --skip-existing

uv run python scripts/import_inflection_sources.py \
  --locale pt \
  --source-type unimorph \
  --input data/sources/inflections/providers/pt/unimorph.tsv \
  --source-name unimorph \
  --write-normalized

uv run python scripts/import_inflection_sources.py \
  --source-type unimorph \
  --all-fetched \
  --limit-top 1000
```

These imports are filtered against frequency lists by default so published data
stays focused on useful words. Use `--all-forms` only when a full source import
is intentional.

`fetch_inflection_sources.py --all` attempts every locale in `data/index.json`
using ISO-639-3 codes plus known overrides. It writes a provider fetch report at
`data/sources/inflections/providers/unimorph_fetch_report.json`.

### 3. Coverage Reporting

Coverage is tracked against frequency-list seeds:

```bash
uv run python scripts/report_inflections.py --expected-limit 100
uv run python scripts/report_inflections.py --expected-limit 100 --min-coverage 0.4
```

This catches cases where a generated file is structurally valid but only contains
one or two useful entries.

### 4. Tests-First LLM Pass

For locales without a curated test suite, generate tests before generating or
trusting rules.

The batch prompt now asks for JSON test arrays, not escaped CSV strings, because
CSV-in-JSON caused malformed/truncated outputs.

```bash
uv run python scripts/build_inflection_tests.py --locales ar,ca,pt
uv run --with requests python scripts/inflections_batch.py submit \
  --batch-file data/sources/inflections/batches/<tests-batch>.jsonl
uv run --with requests python scripts/inflections_batch.py download --batch-id <batch-id>
uv run python scripts/ingest_inflection_tests.py --input <downloaded-output.jsonl> --allow-errors
uv run python scripts/validate_inflections.py
```

Ingestion converts JSON test arrays into `tests.csv` and syncs them into
`rules.json.tests`.

Generated tests should include negative `no_rule` cases, but those should be a
minority. By default ingestion rejects suites where more than 35% of rows are
`no_rule`. Use `scripts/prune_inflection_tests.py` to remove previously ingested
test suites that exceed this threshold.

### 5. Rules-Only LLM Pass

Only after a locale has word forms and tests should we generate rules.

```bash
uv run python scripts/build_inflection_rules.py --locales ar,ca,pt
uv run --with requests python scripts/inflections_batch.py submit \
  --batch-file data/sources/inflections/batches/<rules-batch>.jsonl
uv run --with requests python scripts/inflections_batch.py download --batch-id <batch-id>
uv run python scripts/ingest_inflection_rules.py --input <downloaded-output.jsonl>
uv run python scripts/validate_inflections.py
```

The rules prompt should generate executable `lookback`/`inflection`/`overrides`
rules, not prose grammar notes.

### 6. Sync And Package

After modifying data:

```bash
uv run python scripts/sync_package_data.py
node scripts/generate_browser_modules.js
node scripts/generate_browser_freq.js
node scripts/generate_browser_index_mjs.js
```

Then run targeted checks:

```bash
uv run python scripts/validate_inflections.py
uv run python scripts/check_inflection_runtime.py --locales en
uv run pytest tests/test_import_inflection_sources.py tests/test_inflections.py
npm test -- --runTestsByPath tests/inflections.test.js
```

## Regional Locale Policy

Do not generate full regional packs by default.

Recommended default:

- `en` is canonical for English.
- `fr` is canonical for French.
- `pt` is canonical for Portuguese.
- Regional packs such as `en-GB`, `en-NZ`, `fr-CA`, or `pt-BR` should be small
  override packs unless there are real morphology, spelling, vocabulary, or rule
  differences.

The package loader can fall back from `language-region` to base `language`.
The index records `base_locale` for regional packs when a base pack exists, and
runtime loaders fall back to the base locale if a regional file is missing.

## Current State

As of this document:

- English has been imported from the demo-tools canonical data.
- Spanish has the demo-tools minimal data.
- Arabic, Catalan, French Canadian, Portuguese, and Brazilian Portuguese have
  been bulked out with UniMorph word forms.
- A first rules-only pass added executable rules for those enriched locales.
- The first CSV-string tests batch showed why tests should be returned as JSON
  arrays and converted locally.

## Open Work

- Run the JSON-array tests-first pass and review generated `tests.csv` files.
- Use tests to refine generated rules.
- Expand runtime compatibility checks in `scripts/check_inflection_runtime.py`
  until generated locale tests pass the same lookup semantics as demo-tools.
- Add base-locale fallback behavior to public loaders for regional variants.
- Decide which generated regional packs should be removed or converted into
  overrides.
