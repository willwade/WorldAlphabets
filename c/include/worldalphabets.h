// WorldAlphabets C interface
// Generated data lives in c/generated; runtime helpers are in c/src.

#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuration macros for embedded use:
// WA_STATIC_MATCH_BUFFER_SIZE - Pre-allocated buffer size for wa_find_layouts_by_hid
//                               Set to 0 to use dynamic allocation (default)
// WA_DISABLE_LANGUAGE_DETECTION - Exclude language detection to reduce code size
// WA_MAX_STATIC_MATCHES - Maximum static match array size (default: 32)

#ifndef WA_MAX_STATIC_MATCHES
#define WA_MAX_STATIC_MATCHES 32
#endif

typedef struct {
    const char **items;
    size_t len;
} wa_string_array;

typedef struct {
    const char *ch;
    double freq;
} wa_freq_entry;

typedef struct {
    const char *language;
    const char *script;
    const char **uppercase;
    size_t uppercase_len;
    const char **lowercase;
    size_t lowercase_len;
    const wa_freq_entry *frequency;
    size_t frequency_len;
    const char **digits;
    size_t digits_len;
} wa_alphabet;

typedef struct {
    const char *language;
    const char *mode; // "word" or "bigram"
    const char **tokens;
    size_t token_count;
} wa_frequency_list;

typedef struct {
    const char *language;
    const char **scripts;
    size_t script_count;
} wa_script_entry;

typedef struct {
    const char *id;
    const char *name;
    const struct wa_keyboard_layer *layers;
    size_t layer_count;
} wa_keyboard_layout;

typedef struct {
    uint16_t keycode; // HID usage
    const char *value;
} wa_keyboard_mapping;

typedef struct wa_keyboard_layer {
    const char *name;
    const wa_keyboard_mapping *entries;
    size_t entry_count;
} wa_keyboard_layer;

typedef struct {
    const char *language;
    double score;
} wa_detect_result;

typedef struct {
    wa_detect_result *items;
    size_t len;
} wa_detect_result_array;

typedef struct {
    const char *language;
    double prior;
} wa_prior;

typedef struct {
    const char *key;
    const char *value;
} wa_inflection_form;

typedef struct {
    const char *word;
    const char *base;
    const char **types;
    size_t type_count;
    const wa_inflection_form *forms;
    size_t form_count;
} wa_inflection_entry;

typedef struct {
    const char *locale;
    const wa_inflection_entry **entries;
    size_t entry_count;
} wa_inflection_table;

typedef struct {
    const char **words;
    size_t word_count;
    const char *match_type;
    int optional;
    int condense;
} wa_lookback_check;

typedef struct {
    const char *key;
    const char *value;
} wa_rule_override;

typedef struct {
    const char *id;
    const char *type;
    const char *inflection;
    const wa_lookback_check *lookback;
    size_t lookback_count;
    const wa_rule_override *overrides;
    size_t override_count;
} wa_inflection_rule;

typedef struct {
    const char *locale;
    const wa_inflection_rule **rules;
    size_t rule_count;
    const struct wa_join_rule *joins;
    size_t join_count;
} wa_rules_table;

typedef struct wa_join_rule {
    const char *id;
    const char **prev;
    size_t prev_count;
    const char **next;
    size_t next_count;
    const char *next_match;
    const char *result_template;
    const char *reason;
} wa_join_rule;

typedef struct {
    const char *replacement;
    const char *rule_id;
    const char *rule_type;
} wa_lookup_result;

typedef struct {
    const wa_keyboard_layout *layout;
    const wa_keyboard_layer *layer;
    const wa_keyboard_mapping *mapping;
} wa_layout_match;

typedef struct {
    wa_layout_match *items;
    size_t len;
    size_t capacity;   // For static buffer tracking
    int is_static;     // 1 if using static buffer, 0 if dynamically allocated
} wa_layout_match_array;

// Alphabets
wa_string_array wa_get_available_codes(void);
const wa_alphabet *wa_load_alphabet(const char *code, const char *script);
wa_string_array wa_get_scripts(const char *code);

// Frequency lists
const wa_frequency_list *wa_load_frequency_list(const char *code);

// Language detection
wa_detect_result_array wa_detect_languages(const char *text,
                                           const char **candidate_langs,
                                           size_t candidate_count,
                                           const wa_prior *priors,
                                           size_t prior_count,
                                           size_t topk);
void wa_free_detect_results(wa_detect_result_array *results);

// Keyboards
wa_string_array wa_get_available_layouts(void);
const wa_keyboard_layout *wa_load_keyboard(const char *layout_id);
wa_keyboard_layer wa_extract_layer(const wa_keyboard_layout *layout,
                                   const char *layer_name);
wa_layout_match_array wa_find_layouts_by_hid(uint16_t hid_usage,
                                             const char *layer_name);
// Static buffer version - uses provided buffer, no dynamic allocation
// Returns number of matches found (up to buffer_size)
size_t wa_find_layouts_by_hid_static(uint16_t hid_usage,
                                     const char *layer_name,
                                     wa_layout_match *buffer,
                                     size_t buffer_size);
void wa_free_layout_matches(wa_layout_match_array *matches);

// Inflections
wa_string_array wa_get_available_inflection_locales(void);
const wa_inflection_table *wa_load_inflection_table(const char *locale);
const wa_inflection_entry *wa_find_inflection_entry(
    const wa_inflection_table *table, const char *word);
const char *wa_get_inflected_form(const wa_inflection_entry *entry,
                                   const char *inflection_key);

// Inflection rules + lookup
const wa_rules_table *wa_load_rules_table(const char *locale);
wa_lookup_result wa_lookup_word(const wa_inflection_table *words,
                                  const wa_rules_table *rules,
                                  const char *word,
                                  const char *prior_words);

// Join/euphony
typedef struct {
    const char *result;
    const char *rule_id;
    const char *reason;
    int replaces_pair;
} wa_join_result;

wa_join_result wa_join_words(const wa_rules_table *rules,
                              const char *prev,
                              const char *next);

// Tag features
typedef struct {
    const char *tag;
    const char *feature_key;
    const char *feature_value;
} wa_feature_entry;

typedef struct {
    const wa_feature_entry *features;
    size_t feature_count;
} wa_feature_array;

wa_feature_array wa_get_features(const char *tag);
void wa_free_features(wa_feature_array *fa);

// Apply rules to a sentence (walks tokens left-to-right)
typedef struct {
    const char *surface;
    const char *rule_id;
    const char *rule_type;
    const char *join_rule_id;
    const char *join_reason;
} wa_applied_token;

typedef struct {
    wa_applied_token *tokens;
    size_t token_count;
} wa_applied_sentence;

wa_applied_sentence wa_apply_rules(const wa_inflection_table *words,
                                    const wa_rules_table *rules,
                                    const char *sentence);
void wa_free_applied_sentence(wa_applied_sentence *sent);

#ifdef __cplusplus
}
#endif
