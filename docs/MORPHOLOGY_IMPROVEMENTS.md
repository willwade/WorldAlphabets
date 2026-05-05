# Morphology System Improvements

Analysis of ~/GitHub/morpho-core and ~/GitHub/morphologyAPIwLLM
for potential improvements to WorldAlphabets inflection data and APIs.

Date: 2026-05-05

---

## 1. Euphony/Join Tables (from morpho-core) — HIGH VALUE, LOW EFFORT

**Status: IN PROGRESS**

morpho-core uses a simple 4-column TSV for token-boundary operations:

```
# prev    next    result       reason
le        homme   l'homme      FR_elision
a         el      al           ES_contraction
Geburt    Tag     Geburtstag   DE_compound
a         apple   an apple     EN_a_an
dar       me      darmee       ES_clitic
```

### Languages with join data in morpho-core:

- **French** (18 rules): elision (le+homme→l'homme, je+aimer→j'aimer, que+il→qu'il),
  h-aspiré exceptions (le+heros→le heros, le+hibou→le hibou)
- **English** (10 rules): a/an selection (a+apple→an apple, a+hour→an hour,
  a+university→a university)
- **Spanish** (18 rules): contractions (a+el→al, de+el→del),
  clitic attachment (dar+me→darme, hacer+lo→hacerlo, ir+se→irse)
- **German** (9 rules): compound nouns with interfix
  (Geburt+Tag→Geburtstag, Hand+Schuhe→Handschuhe, Schule+Kind→Schulkind)

### Implementation plan:

Add a `"join"` array to rules.json:

```json
{
  "join": [
    {
      "prev": "le",
      "next_pattern": "[aeiouyh]",
      "result_template": "l'{next}",
      "reason": "FR_elision"
    },
    {
      "prev": "a",
      "next": "el",
      "result": "al",
      "reason": "ES_contraction"
    }
  ]
}
```

Engine processes join rules during lookup when two adjacent words are being
combined. Runs BEFORE override/type rules since it modifies token boundaries.

### Source files in morpho-core:
- packs/en-US/v1/join.tsv
- packs/fr-FR/v1/join.tsv
- packs/es-ES/v1/join.tsv
- packs/de-DE/v1/join.tsv
- crates/morpho-core/src/hfst.rs (PackJoinModel::from_tsv, lines 205-257)
- crates/morpho-core/src/hfst.rs (join() lookup, lines 240-250)

---

## 2. Confidence/Provenance Tracking (from morphologyAPIwLLM) — MEDIUM VALUE

Their hybrid system attaches metadata to every result:

```python
class Metadata(BaseModel):
    provenance: Provenance  # "llm", "rule", or "hybrid"
    confidence: float       # 0.0-1.0
    variety: Optional[str]  # e.g. "en-GB"
    lemma_detected_from: Optional[str]
    warnings: List[str]
    notes: List[str]
```

Hybrid fallback: if LLM confidence < 0.8, fall back to rule engine. Mark
result as HYBRID provenance. Rule engine results get confidence=1.0.

### What we could adopt:

- Add `_provenance` field to inflected forms in words.json:
  `"plural": {"value": "dogs", "provenance": "llm", "confidence": 0.9}`
- Add provenance to rule test results
- Let API consumers decide whether to trust LLM-generated forms
- Could add a `--trust-threshold` parameter to lookup functions

### Source files in morphologyAPIwLLM:
- src/morphology_service/core/config.py (confidence threshold, line 24)
- src/morphology_service/services/morphology.py (orchestration, lines 288-311)
- src/morphology_service/schemas.py (Metadata model)

---

## 3. Buffer/Sentence API (from morpho-core) — HIGH VALUE, HIGH EFFORT

morpho-core's core abstraction is a `SentenceBuffer`:

```rust
pub struct SentenceBuffer {
    tokens: Vec<TokenIntent>,  // { lemma: String, tags: Vec<String> }
    engine: Arc<MorphoEngine>,
}
```

Key operations:
- `push(lemma, tags)` — append token
- `insert(index, lemma, tags)` — insert at position
- `update(index, lemma, tags)` — update + REACTIVELY re-inflect dependent tokens
- `remove(index)` — remove + react
- `render()` — render full sentence with all inflection applied
- `render_with_diffs()` — render showing what changed

Reactive updates: when you change the subject pronoun, ALL verbs in the
sentence automatically re-inflect. Change "he" to "they" → "goes" becomes "go".
This is the key differentiator over our stateless lookup_word().

### What we could adopt:

A higher-level API on top of lookup_word():

```python
class Sentence:
    def __init__(self, locale, words_data, rules_data):
        ...
    def append(self, word: str) -> None: ...
    def insert(self, index: int, word: str) -> None: ...
    def update(self, index: int, word: str) -> None: ...
    def remove(self, index: int) -> None: ...
    def render(self) -> str: ...  # Full inflected sentence
    def render_diffs(self) -> list[Diff]: ...
```

This would be the "AAC sentence builder" use case — user builds a sentence
word by word, and the engine keeps everything grammatically consistent.

### Source files in morpho-core:
- crates/morpho-core/src/buffer.rs (SentenceBuffer, lines 101-425)
- crates/morpho-core/src/engine.rs (MorphoEngine)
- crates/morpho-core/src/types.rs (TokenIntent, RenderedToken, RenderDiff)

---

## 4. Language-Specific Euphony Modules (from morpho-core) — USEFUL REFERENCE

Small focused modules handle cross-token dependencies that single-word
transducers can't express:

### English (english.rs, 122 lines):
- `surface()`: Full verb conjugation with irregular tables
  (be→am/is/are, go→went, do→did, have→had, eat→ate)
- `past()`: Irregular past tense lookup
- `pres_third()`: 3rd person present (have→has, do→does, go→goes, be→is)
- `article_for()`: a/an selection with vowel/exception handling

### French (french.rs, 63 lines):
- `elision_via_hfst()`: Detect when adjacent tokens should merge via elision
- `elision_prefix()`: le/la→l', je→j', ne→n', que→qu', etc.
- `starts_with_vowel_or_mute_h()`: Phonetic checking
- `is_h_aspire()`: Hardcoded exception list
  (haricot, honte, hache, heros, herisson, hibou, hurler, hasard, haine)

### Spanish (spanish.rs, 16 lines):
- `is_clitic()`: {me, te, se, lo, la, los, las, le, les, nos, os}
- `is_verb()`: Tag-based or ending heuristic (-r, -ndo)

### German (german.rs, 5 lines):
- `is_noun()`: Tag check. Compound logic in buffer.rs (lines 331-369).

### What we could adopt:

These patterns are essentially what our override rules already do, but
organized per-language. The French elision and Spanish clitic lists are
good reference data for our join tables (item 1).

---

## 5. Structured Feature Model (from morphologyAPIwLLM) — HIGH VALUE, VERY HIGH EFFORT

**Status: IMPORTANT BUT DEFERRED**

### Current problem:

Our inflection keys are flat locale-specific strings with no common schema:
- German: `v_ind_pl_1_prs`, `adj_nom_masc_sg`, `n_acc_neut_pl`
- English: `plural`, `past_participle`, `3rd_person_singular`
- Arabic: `v_1_pl_ipfv_ind_act`, `n_sg_def_acc`
- French: `v_ind_prs_1_sg`, `n_pl_def`

No two locales use the same naming convention. This makes:
- Cross-language UI rendering impossible
- Feature-based filtering difficult
- Adding new locales error-prone

### morphologyAPIwLLM's approach:

Structured `PartOfSpeechFeatures` with 12+ standardized fields:

```python
class PartOfSpeechFeatures(BaseModel):
    partofspeechcategory: Optional[str]  # "verb", "noun", "adjective"
    pospsubcategory: Optional[str]
    tense: Optional[str]          # "present", "past", "infinitive"
    mood: Optional[str]           # "indicative", "imperative", "subjunctive"
    aspect: Optional[str]         # "perfective", "imperfective"
    voice: Optional[str]          # "active", "passive"
    person: Optional[str]         # "first", "second", "third"
    number: Optional[str]         # "singular", "plural", "dual"
    gender: Optional[str]         # "masculine", "feminine", "neuter"
    case: Optional[str]           # "nominative", "accusative", "dative", "genitive"
    degree: Optional[str]         # "positive", "comparative", "superlative"
    definiteness: Optional[str]   # "definite", "indefinite"
```

### Proposed migration strategy:

1. Define a canonical feature schema (Universal Morphological Features,
   inspired by UniMorph http://unimorph.github.io/)
2. Create a mapping layer: old flat key → structured features
3. Add `features` field alongside existing flat keys in words.json:
   ```json
   {
     "gehen": {
       "inflections": {
         "v_ind_pl_1_prs": "gehen",
         "v_ind_pl_1_prs_features": {
           "pos": "verb", "tense": "present", "mood": "indicative",
           "person": "1", "number": "plural"
         }
       }
     }
   }
   ```
4. Gradually migrate consumers to use structured features
5. Eventually deprecate flat keys (or auto-generate them from features)

### Source files:
- morphologyAPIwLLM/src/morphology_service/schemas.py (PartOfSpeechFeatures)
- morpho-core uses implicit feature extraction from HFST tags
- UniMorph project: http://unimorph.github.io/ — universal morphological features

---

## 6. Number Spelling (from morphologyAPIwLLM) — LOW PRIORITY

Deterministic English number-to-words via recursive decomposition:

```python
def _number_to_words_en(self, n: int) -> str:
    # Handles negatives, 0-9, 10-19, 20-99, 100-999, thousands/millions/billions
    # "4321" → "four thousand, three hundred and twenty-one"
```

LLM can spell numbers in any language. Hybrid fallback: LLM first, then
rule engine for English.

### What we could adopt:

Not core to AAC use case but could be useful for:
- Spell-out of quantities ("3" → "three")
- Number display in inflection browser
- Could be a separate utility, not part of the inflection engine

### Source files:
- morphologyAPIwLLM/src/morphology_service/services/hfst_backend.py (lines 406-449)
- morphologyAPIwLLM/src/morphology_service/services/morphology.py (lines 223-246)
