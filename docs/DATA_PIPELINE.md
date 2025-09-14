# WorldAlphabets Data Collection Pipeline

## Overview

The WorldAlphabets data collection pipeline is a unified Python-based system that generates comprehensive language and alphabet data from multiple authoritative sources. The pipeline follows a clear separation between data generation (Python) and data consumption (Python/Node.js libraries).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION PIPELINE                     │
│                         (Python Only)                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GENERATED DATA FILES                      │
│                    (JSON in data/ directory)                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONSUMPTION LIBRARIES                       │
│              (Python: src/worldalphabets/)                     │
│              (Node.js: index.js)                               │
│              (Web UI: web/src/)                                │
└─────────────────────────────────────────────────────────────────┘
```

## Data Sources (Priority Order)

### Primary Sources
1. **CLDR (Unicode Common Locale Data Repository)**
   - Purpose: Exemplar characters, script information
   - URL: `https://github.com/unicode-org/cldr-json`
   - Coverage: ~700 locales
   - Fallback: Manual alphabet definitions

2. **ISO 639-3 Registry**
   - Purpose: Language codes, names, macrolanguage relationships
   - URL: `https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab`
   - Coverage: ~7,000 languages
   - Fallback: langcodes library

3. **Simia Unigrams Dataset**
   - Purpose: Letter frequency data
   - URL: `http://simia.net/letters/unigrams.zip`
   - Coverage: ~300 languages
   - Fallback: OpenSubtitles frequencies

### Secondary Sources
4. **Wikidata SPARQL**
   - Purpose: Language-script mappings
   - Query: Language entities with script properties
   - Coverage: ~1,400 language-script pairs
   - Fallback: Manual mappings

5. **OpenSubtitles Frequencies**
   - Purpose: Fallback frequency data
   - Source: Word frequency analysis
   - Coverage: ~100 languages
   - Fallback: Uniform distribution

### Fallback Sources
6. **Manual Definitions**
   - Purpose: Critical missing languages
   - Location: `src/worldalphabets/data/fallbacks.json`
   - Coverage: Hand-curated essential languages
   - Examples: Maori, Cherokee, constructed languages

## Pipeline Stages

### Stage 1: Source Data Collection
**Function**: `collect_sources()`
**Purpose**: Download and cache all external data sources
**Outputs**:
- `data/sources/cldr/` - CLDR JSON files
- `data/sources/iso639-3.tab` - ISO language registry
- `data/sources/unigrams/` - Frequency data
- `data/sources/wikidata_language_scripts.json` - Language-script mappings

### Stage 2: Language Registry Building
**Function**: `build_language_registry()`
**Purpose**: Create comprehensive language database
**Inputs**: ISO 639-3, Wikidata, manual additions
**Outputs**:
- `data/language_registry.json` - Complete language database
- `data/language_scripts.json` - Language-script mappings (enhanced)

### Stage 3: Alphabet Generation
**Function**: `build_alphabets()`
**Purpose**: Generate alphabet files for all language-script pairs
**Inputs**: Language registry, CLDR, frequency data
**Outputs**: `data/alphabets/{lang}-{script}.json`

### Stage 4: Translation Generation
**Function**: `build_translations()`
**Purpose**: Add "Hello, how are you?" translations to alphabet files
**Inputs**: Google Translate API, alphabet files
**Outputs**: Enhanced alphabet files with `hello_how_are_you` field
**Requirements**: `GOOGLE_TRANS_KEY` environment variable

### Stage 5: Keyboard Layout Building
**Function**: `build_keyboards()`
**Purpose**: Generate keyboard layout files and mappings
**Inputs**: Language index, keyboard layout definitions
**Outputs**:
- `data/layouts/{lang}-{layout}.json` - Keyboard layout files
- `data/layouts/index.json` - Keyboard layout index

### Stage 6: Top-200 Token Lists
**Function**: `build_top200()` (uses unified pipeline)
**Purpose**: Generate compact token frequency lists for language detection
**Script**: `scripts/build_top200_unified.py`

**5-Priority Source Pipeline**:
1. **Leipzig Corpora Collection** - High-quality news/web corpora (CC-BY)
2. **HermitDave FrequencyWords** - OpenSubtitles/Wikipedia sources (CC-BY)
3. **Tatoeba sentences** - Sentence-based extraction (CC-BY 2.0 FR)
4. **Existing alphabet frequency data** - Character-level fallback
5. **Simia unigrams** - CJK character data

**Coverage**: 90.9% (130/143 languages)

**Outputs**:
- `data/freq/top200/<lang>.txt` - Top-200 tokens per language
- `data/freq/top200/BUILD_REPORT_UNIFIED.json` - Build summary with source attribution

### Stage 7: TTS Voice Indexing
**Function**: `build_tts_index()`
**Purpose**: Index available TTS voices from all providers
**Inputs**: TTS provider APIs
**Outputs**: `data/tts_index.json` - Available voices by language

### Stage 8: Audio Generation
**Function**: `build_audio()`
**Purpose**: Generate audio files using TTS engines
**Inputs**: TTS index, alphabet files
**Outputs**:
- `data/audio/*.wav` - Audio files
- `data/audio/index.json` - Audio file index

### Stage 9: Index Generation
**Function**: `build_index()`
**Purpose**: Create searchable indexes and metadata
**Script**: `scripts/create_index.js` (Node.js)
**Inputs**: All alphabet files
**Outputs**:
- `data/index.json` - Main searchable index
- `data/scripts.json` - Script groupings
- `data/stats.json` - Coverage statistics

### Stage 10: Data Validation
**Function**: `validate_data()`
**Purpose**: Comprehensive data validation
**Outputs**: Validation reports and error logs

## File Formats

### Language Registry Entry
```json
{
  "code": "mi",
  "iso639_1": "mi",
  "iso639_3": "mri",
  "name": "Māori",
  "scripts": ["Latn"],
  "macrolanguage": null,
  "status": "active",
  "sources": ["iso639-3", "manual"]
}
```

### Alphabet File Format
```json
{
  "language": "Māori",
  "iso639_1": "mi",
  "iso639_3": "mri",
  "script": "Latn",
  "alphabetical": ["A", "E", "H", "I", "K", "M", "N", "O", "P", "R", "T", "U", "W"],
  "uppercase": ["A", "E", "H", "I", "K", "M", "N", "O", "P", "R", "T", "U", "W"],
  "lowercase": ["a", "e", "h", "i", "k", "m", "n", "o", "p", "r", "t", "u", "w"],
  "frequency": {"a": 0.1234, "e": 0.0987, ...},
  "digits": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  "direction": "ltr",
  "hello_how_are_you": "Kia ora, kei te pēhea koe?",
  "sources": ["cldr", "simia"],
  "last_updated": "2025-01-15T10:30:00Z"
}
```

## Error Handling & Fallbacks

### Missing CLDR Data
1. Check manual fallback definitions
2. Use basic Latin alphabet for Latin-script languages
3. Skip if no fallback available, log warning

### Missing Frequency Data
The unified Top-200 pipeline handles missing data through a comprehensive 5-priority fallback:
1. **Leipzig Corpora** - Major languages with news/web corpora
2. **HermitDave FrequencyWords** - 47 languages from subtitles/Wikipedia
3. **Tatoeba sentences** - Under-resourced languages via sentence extraction
4. **Existing alphabet frequencies** - Character-level data from existing alphabets
5. **Simia unigrams** - CJK character data as final fallback

This approach achieves 90.9% coverage, with only 19 very low-resource languages remaining without frequency data.

### Missing Language Information
1. Use langcodes library for basic info
2. Check manual overrides
3. Generate minimal entry with warnings

## Build Commands

### Full Pipeline
```bash
# Run complete consolidated pipeline
uv run scripts/build_data_pipeline.py

# With verbose output
uv run scripts/build_data_pipeline.py --verbose
```

### Individual Stages
```bash
# Run specific pipeline stage
uv run scripts/build_data_pipeline.py --stage collect_sources
uv run scripts/build_data_pipeline.py --stage build_language_registry
uv run scripts/build_data_pipeline.py --stage build_alphabets
uv run scripts/build_data_pipeline.py --stage build_translations
uv run scripts/build_data_pipeline.py --stage build_keyboards
uv run scripts/build_data_pipeline.py --stage build_tts_index
uv run scripts/build_data_pipeline.py --stage build_audio
uv run scripts/build_data_pipeline.py --stage build_index
uv run scripts/build_data_pipeline.py --stage validate_data
```

### Development/Testing
```bash
# Build single language
uv run scripts/build_data_pipeline.py --language mi --script Latn

# Build all scripts for a language
uv run scripts/build_data_pipeline.py --language zh

# Verbose output for debugging
uv run scripts/build_data_pipeline.py --stage build_alphabets --verbose
```

### Legacy Commands (Deprecated)
```bash
# Old fragmented approach - DO NOT USE
uv run scripts/build_all_data.py  # Replaced by build_data_pipeline.py
```

## Quality Assurance

### Automated Validation
- Schema validation for all JSON files
- Cross-reference validation between indexes
- Coverage reports for missing languages
- Frequency data sanity checks

### Manual Review Points
- New language additions require manual review
- Fallback definitions need linguistic validation
- Frequency data outliers flagged for review

## Maintenance

### Regular Updates
- CLDR: Updated with Unicode releases (~2x/year)
- ISO 639-3: Updated annually
- Wikidata: Updated monthly via automated queries

### Monitoring
- Track coverage statistics over time
- Monitor build success rates
- Alert on significant data changes
