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

#ifdef __cplusplus
}
#endif
