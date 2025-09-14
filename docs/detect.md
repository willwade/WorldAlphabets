# Language Detection

WorldAlphabets uses a **hybrid detection system** that combines word-based and character-based approaches to maximize language coverage.

## Detection Methods

### 1. Word-Based Detection (Primary)

The primary detection method uses Top-200 token lists stored under `data/freq/top200`. Each file is a UTF-8 list of tokens in rank order. Languages without explicit word boundaries contain a header line `# type=bigram` followed by character bigrams.

**Coverage**: 86 languages with frequency data
**Threshold**: 0.05 (configurable)
**Accuracy**: High for languages with sufficient training data

### 2. Character-Based Detection (Fallback)

When word frequency data is unavailable, the system falls back to character-based analysis using alphabet data from `data/alphabets/`. This method analyzes:

- **Character overlap**: How well the alphabet covers the input text characters
- **Character frequencies**: Weighted scoring using character frequency data from alphabet files
- **Distinctive characters**: Bonus for rare characters that are unique to specific languages

**Coverage**: 331 languages (all languages with alphabet data)
**Threshold**: 0.02 (lower threshold for character-based detection)
**Accuracy**: Good for languages with distinctive scripts or character sets

## Configuration

At runtime the frequency directory can be overridden by setting the environment variable `WORLDALPHABETS_FREQ_DIR` to a custom path.

Scores combine script/codepoint priors with detection overlap using these weights:
- `PRIOR_WEIGHT` (default `0.65`) - Weight for language priors
- `FREQ_WEIGHT` (default `0.35`) - Weight for word-based frequency overlap
- `CHAR_WEIGHT` (default `0.2`) - Weight for character-based overlap (fallback only)

These constants can be overridden via environment variables `WA_FREQ_PRIOR_WEIGHT`, `WA_FREQ_OVERLAP_WEIGHT`.

## Detection Flow

1. **Word-based detection** is attempted first for all candidate languages
2. If word-based detection succeeds (score > 0.05), the result is used
3. If word-based detection fails, **character-based detection** is attempted
4. Character-based results use a lower threshold (0.02) and are marked as fallback
5. Results are sorted with a small boost for word-based detections to maintain priority

## Examples

```python
# Word-based detection (English has frequency data)
detect_languages("Hello world", candidate_langs=['en', 'de'])
# [('en', 0.158), ('de', 0.142)]  # Both detected via word frequency

# Character-based fallback (Abkhazian lacks frequency data)
detect_languages("Аҧсуа бызшәа", candidate_langs=['ab', 'ru'])
# [('ab', 0.146), ('ru', 0.136)]  # ab via character analysis, ru via word frequency
```

This hybrid approach enables detection of **4x more languages** compared to word-based detection alone.
