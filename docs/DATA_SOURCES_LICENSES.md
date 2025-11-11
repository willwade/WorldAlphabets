# Data Sources and Licenses

This document provides licensing information for all external data sources used in the WorldAlphabets project. All sources listed here allow redistribution under their respective licenses.

## Summary

WorldAlphabets aggregates data from multiple open-source and openly-licensed sources. All data sources used in this project permit redistribution, though some require attribution or have share-alike provisions.

---

## Frequency Data Sources (Top-1000 Word Lists)

The unified frequency data pipeline (`scripts/build_top200_unified.py`) uses the following sources in priority order:

### 1. Leipzig Corpora Collection

**Source**: Wortschatz Leipzig, University of Leipzig  
**Website**: https://wortschatz.uni-leipzig.de/  
**Download Portal**: https://downloads.wortschatz-leipzig.de/  
**License**: **Creative Commons Attribution (CC BY)**  
**Languages Covered**: 77 languages (dynamically discovered via catalogue)

**License Details**:
- The text corpora offered for download are made available under the Creative Commons licence CC BY
- Attribution required when using the data
- Commercial use is permitted
- Modifications are permitted
- **Redistribution**: ✅ **Allowed** with attribution

**Terms of Use**: https://wortschatz.uni-leipzig.de/en/usage

**Usage in WorldAlphabets**:
- Primary source for high-quality frequency data
- Accessed via dynamic catalogue scraping from `https://corpora.wortschatz-leipzig.de/`
- Downloads corpus archives in `.tar.gz` format
- Extracts word frequency lists from `-words.txt` files within archives
- Prioritizes corpus types: community > news > mixed > web > newscrawl > wikipedia

**Attribution**: Data from Leipzig Corpora Collection, Wortschatz Leipzig, University of Leipzig

---

### 2. HermitDave FrequencyWords

**Source**: Hermit Dave  
**Repository**: https://github.com/hermitdave/FrequencyWords  
**License**: 
- **Code**: MIT License
- **Content**: **Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA-4.0)**

**Languages Covered**: 48 languages

**License Details**:
- Content is derived from OpenSubtitles and Wikipedia
- Attribution required
- Share-alike: Derivative works must use the same license
- Commercial use is permitted
- **Redistribution**: ✅ **Allowed** with attribution and share-alike

**Data Sources**:
- OpenSubtitles 2016: http://opus.lingfil.uu.se/OpenSubtitles2016.php
- OpenSubtitles 2018: http://opus.nlpl.eu/OpenSubtitles2018.php

**Usage in WorldAlphabets**:
- Secondary source for frequency data
- Accessed via GitHub raw content URLs
- Provides word frequency lists in format: `{word} {frequency}`

**Attribution**: Data from FrequencyWords by Hermit Dave (https://github.com/hermitdave/FrequencyWords), licensed under CC-BY-SA-4.0

---

### 3. Tatoeba Sentences

**Source**: Tatoeba Association  
**Website**: https://tatoeba.org/  
**Downloads**: https://tatoeba.org/en/downloads  
**License**: **Creative Commons Attribution 2.0 France (CC-BY 2.0 FR)**

**Languages Covered**: 73 languages

**License Details**:
- Textual sentences are under CC-BY 2.0 FR
- Attribution required
- Commercial use is permitted
- Modifications are permitted
- **Redistribution**: ✅ **Allowed** with attribution

**Terms of Use**: https://tatoeba.org/en/terms_of_use

**Usage in WorldAlphabets**:
- Tertiary source for frequency data, especially for under-resourced languages
- Sentences are tokenized and word frequencies are calculated
- Particularly valuable for languages lacking other frequency data sources

**Attribution**: Sentence data from Tatoeba (https://tatoeba.org), licensed under CC-BY 2.0 FR

---

### 4. Simia Unigrams Dataset

**Source**: Denny Vrandečić (Simia.net)  
**Website**: http://simia.net/letters/  
**Original Data Source**: Wiktionary  
**License**: **Creative Commons Attribution-ShareAlike (CC-BY-SA)**

**Languages Covered**: CJK character data and 262 language editions

**License Details**:
- Data extracted from Wikipedia using WikiExtractor
- Wiktionary content is under CC-BY-SA
- Attribution required
- Share-alike: Derivative works must use the same license
- **Redistribution**: ✅ **Allowed** with attribution and share-alike

**Usage in WorldAlphabets**:
- CJK character frequency data
- Fallback for character-level frequency information
- Stored in `data/sources/unigrams/`

**Attribution**: Character frequency data from Simia unigrams dataset (http://simia.net/letters/), derived from Wiktionary, licensed under CC-BY-SA

---

## Alphabet and Script Data Sources

### CLDR (Common Locale Data Repository)

**Source**: Unicode Consortium  
**Website**: https://cldr.unicode.org/  
**License**: **Unicode License Agreement**

**Usage in WorldAlphabets**:
- Primary source for alphabet exemplar characters
- Locale-specific character sets
- Script information

**Redistribution**: ✅ **Allowed** under Unicode License

---

### Kalenchukov/Alphabet

**Source**: Kalenchukov  
**Repository**: https://github.com/kalenchukov/Alphabet  
**License**: **Apache License 2.0**

**Usage in WorldAlphabets**:
- Supplementary alphabet data
- Character set definitions

**Redistribution**: ✅ **Allowed** under Apache 2.0

---

### Wikidata Language Scripts

**Source**: Wikidata  
**Website**: https://www.wikidata.org/  
**License**: **Creative Commons CC0 (Public Domain)**

**Usage in WorldAlphabets**:
- Language-to-script mappings
- Stored in `data/sources/wikidata_language_scripts.json`

**Redistribution**: ✅ **Allowed** (Public Domain)

---

### ISO 639-3 Language Codes

**Source**: SIL International  
**Website**: https://iso639-3.sil.org/  
**License**: **Open Data Commons Attribution License (ODC-By)**

**Usage in WorldAlphabets**:
- Language code mappings
- Language registry data
- Stored in `data/sources/iso-639-3.tab`

**Redistribution**: ✅ **Allowed** with attribution

---

### Unicode Character Database

**Source**: Unicode Consortium  
**Website**: https://unicode.org/  
**License**: **Unicode License Agreement**

**Usage in WorldAlphabets**:
- Character properties
- Script definitions
- Normalization data

**Redistribution**: ✅ **Allowed** under Unicode License

---

## Keyboard Layout Data

### Kbdlayout.info

**Source**: Kbdlayout.info  
**Website**: https://kbdlayout.info/  
**License**: Various (per-layout, generally permissive)

**Usage in WorldAlphabets**:
- Keyboard layout definitions
- Key mappings for different languages

---

## Wikipedia Content

**Source**: Wikimedia Foundation  
**Website**: https://wikipedia.org/  
**License**: **Creative Commons Attribution-ShareAlike 3.0 (CC-BY-SA-3.0)**

**Usage in WorldAlphabets**:
- Some supplementary language data
- Referenced in various data sources

**Redistribution**: ✅ **Allowed** with attribution and share-alike

---

## License Compatibility

All data sources used in WorldAlphabets are compatible with the project's MIT License for the following reasons:

1. **CC-BY** (Leipzig): Requires attribution only - compatible with MIT
2. **CC-BY-SA** (HermitDave, Simia, Wikipedia): Requires attribution and share-alike for derivatives - our redistribution maintains original licenses
3. **CC-BY 2.0 FR** (Tatoeba): Requires attribution - compatible with MIT
4. **Apache 2.0** (Kalenchukov): Compatible with MIT
5. **CC0** (Wikidata): Public domain - no restrictions
6. **Unicode License**: Permissive, allows redistribution
7. **ODC-By** (ISO 639-3): Requires attribution - compatible with MIT

## Redistribution Rights

All data sources explicitly permit redistribution under their respective licenses. When redistributing:

1. **Maintain attribution** for all sources (see attribution text above)
2. **Preserve license information** for CC-BY-SA content
3. **Include this documentation** or equivalent attribution in distributions
4. **Do not remove** copyright notices or license information from source files

## Attribution Requirements

When using WorldAlphabets data, please include:

```
This project uses data from:
- Leipzig Corpora Collection (CC-BY) - Wortschatz Leipzig, University of Leipzig
- FrequencyWords by Hermit Dave (CC-BY-SA-4.0) - https://github.com/hermitdave/FrequencyWords
- Tatoeba (CC-BY 2.0 FR) - https://tatoeba.org
- Simia unigrams dataset (CC-BY-SA) - http://simia.net/letters/ (derived from Wiktionary)
- Kalenchukov/Alphabet (Apache 2.0) - https://github.com/kalenchukov/Alphabet
- Unicode CLDR and Character Database (Unicode License)
- ISO 639-3 (ODC-By) - SIL International
- Wikidata (CC0)
```

---

## Updates and Maintenance

This document reflects the licensing status as of the date of last update. License terms may change over time. Always verify current license terms at the source websites.

**Last Updated**: 2025-11-11

**Maintained By**: WorldAlphabets Project  
**Contact**: https://github.com/willwade/WorldAlphabets

---

## Additional Resources

- **Project License**: MIT License (see `LICENSE` file)
- **Data Pipeline Documentation**: `docs/DATA_PIPELINE.md`
- **Main README**: `README.md`

