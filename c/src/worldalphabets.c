#include "worldalphabets.h"

#include <ctype.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "../generated/worldalphabets_data.h"

#define PRIOR_WEIGHT 0.65
#define FREQ_WEIGHT 0.35
#define CHAR_WEIGHT 0.2

static int wa_streq(const char *a, const char *b) {
    if (a == NULL || b == NULL) return 0;
    return strcmp(a, b) == 0;
}

static const wa_alphabet *find_alphabet(const char *code, const char *script) {
    for (size_t i = 0; i < WA_ALPHABETS_COUNT; i++) {
        const wa_alphabet *alpha = &WA_ALPHABETS[i];
        if (!wa_streq(alpha->language, code)) continue;
        if (script == NULL || wa_streq(alpha->script, script)) {
            return alpha;
        }
    }
    return NULL;
}

static const wa_script_entry *find_scripts(const char *code) {
    for (size_t i = 0; i < WA_SCRIPT_ENTRIES_COUNT; i++) {
        if (wa_streq(WA_SCRIPT_ENTRIES[i].language, code)) {
            return &WA_SCRIPT_ENTRIES[i];
        }
    }
    return NULL;
}

static const wa_frequency_list *find_freq_list(const char *code) {
    for (size_t i = 0; i < WA_FREQUENCY_LISTS_COUNT; i++) {
        if (wa_streq(WA_FREQUENCY_LISTS[i].language, code)) {
            return &WA_FREQUENCY_LISTS[i];
        }
    }
    return NULL;
}

static const wa_keyboard_layout *find_keyboard(const char *id) {
    for (size_t i = 0; i < WA_KEYBOARD_LAYOUTS_COUNT; i++) {
        if (wa_streq(WA_KEYBOARD_LAYOUTS[i].id, id)) {
            return &WA_KEYBOARD_LAYOUTS[i];
        }
    }
    return NULL;
}

wa_string_array wa_get_available_codes(void) {
    wa_string_array arr = { .items = NULL, .len = WA_LANGUAGE_CODES_COUNT };
    arr.items = WA_LANGUAGE_CODES;
    return arr;
}

const wa_alphabet *wa_load_alphabet(const char *code, const char *script) {
    const char *selected_script = script;
    if (selected_script == NULL) {
        const wa_script_entry *scripts = find_scripts(code);
        if (scripts != NULL && scripts->script_count > 0) {
            selected_script = scripts->scripts[0];
        }
    }
    return find_alphabet(code, selected_script);
}

wa_string_array wa_get_scripts(const char *code) {
    const wa_script_entry *entry = find_scripts(code);
    if (entry == NULL) {
        wa_string_array empty = { .items = NULL, .len = 0 };
        return empty;
    }
    wa_string_array result = { .items = entry->scripts, .len = entry->script_count };
    return result;
}

const wa_frequency_list *wa_load_frequency_list(const char *code) {
    return find_freq_list(code);
}

// --- detection ---

typedef struct {
    uint32_t *items;
    size_t len;
    size_t cap;
} wa_u32_array;

typedef struct {
    char *data;
    size_t len;
    size_t cap;
} wa_buffer;

static void buf_init(wa_buffer *buf) {
    buf->data = NULL;
    buf->len = 0;
    buf->cap = 0;
}

static void buf_reserve(wa_buffer *buf, size_t need) {
    if (need <= buf->cap) return;
    size_t new_cap = buf->cap == 0 ? 64 : buf->cap * 2;
    if (new_cap < need) new_cap = need;
    char *next = (char *)realloc(buf->data, new_cap);
    if (next == NULL) return;
    buf->data = next;
    buf->cap = new_cap;
}

static void buf_push(wa_buffer *buf, char c) {
    buf_reserve(buf, buf->len + 1);
    if (buf->data == NULL) return;
    buf->data[buf->len++] = c;
}

static void buf_reset(wa_buffer *buf) {
    buf->len = 0;
}

static void u32_init(wa_u32_array *arr) {
    arr->items = NULL;
    arr->len = 0;
    arr->cap = 0;
}

static void u32_reserve(wa_u32_array *arr, size_t need) {
    if (need <= arr->cap) return;
    size_t new_cap = arr->cap == 0 ? 32 : arr->cap * 2;
    if (new_cap < need) new_cap = need;
    uint32_t *next = (uint32_t *)realloc(arr->items, sizeof(uint32_t) * new_cap);
    if (next == NULL) return;
    arr->items = next;
    arr->cap = new_cap;
}

static void u32_push_unique(wa_u32_array *arr, uint32_t v) {
    for (size_t i = 0; i < arr->len; i++) {
        if (arr->items[i] == v) return;
    }
    u32_reserve(arr, arr->len + 1);
    arr->items[arr->len++] = v;
}

static size_t utf8_encode(uint32_t cp, char out[5]) {
    if (cp <= 0x7F) {
        out[0] = (char)cp;
        return 1;
    } else if (cp <= 0x7FF) {
        out[0] = (char)(0xC0 | ((cp >> 6) & 0x1F));
        out[1] = (char)(0x80 | (cp & 0x3F));
        return 2;
    } else if (cp <= 0xFFFF) {
        out[0] = (char)(0xE0 | ((cp >> 12) & 0x0F));
        out[1] = (char)(0x80 | ((cp >> 6) & 0x3F));
        out[2] = (char)(0x80 | (cp & 0x3F));
        return 3;
    }
    out[0] = (char)(0xF0 | ((cp >> 18) & 0x07));
    out[1] = (char)(0x80 | ((cp >> 12) & 0x3F));
    out[2] = (char)(0x80 | ((cp >> 6) & 0x3F));
    out[3] = (char)(0x80 | (cp & 0x3F));
    return 4;
}

static uint32_t utf8_next(const char *s, size_t len, size_t *index) {
    if (*index >= len) return 0;
    unsigned char c = (unsigned char)s[*index];
    if (c < 0x80) {
        (*index)++;
        return (uint32_t)c;
    } else if ((c >> 5) == 0x6 && *index + 1 < len) {
        uint32_t cp = ((uint32_t)(c & 0x1F) << 6) |
                      (uint32_t)(s[*index + 1] & 0x3F);
        *index += 2;
        return cp;
    } else if ((c >> 4) == 0xE && *index + 2 < len) {
        uint32_t cp = ((uint32_t)(c & 0x0F) << 12) |
                      ((uint32_t)(s[*index + 1] & 0x3F) << 6) |
                      (uint32_t)(s[*index + 2] & 0x3F);
        *index += 3;
        return cp;
    } else if ((c >> 3) == 0x1E && *index + 3 < len) {
        uint32_t cp = ((uint32_t)(c & 0x07) << 18) |
                      ((uint32_t)(s[*index + 1] & 0x3F) << 12) |
                      ((uint32_t)(s[*index + 2] & 0x3F) << 6) |
                      (uint32_t)(s[*index + 3] & 0x3F);
        *index += 4;
        return cp;
    }
    (*index)++;
    return (uint32_t)c;
}

static int is_letter(uint32_t cp) {
    if (cp < 128) {
        return isalpha((int)cp);
    }
    return 1; // assume non-ASCII letters are valid
}

static void append_cp(wa_buffer *buf, uint32_t cp) {
    char tmp[5] = {0};
    size_t n = utf8_encode(cp, tmp);
    buf_reserve(buf, buf->len + n);
    for (size_t i = 0; i < n; i++) {
        buf->data[buf->len++] = tmp[i];
    }
}

static void push_token(wa_string_array *arr, wa_buffer *buf, size_t *cap_tokens) {
    if (buf->len == 0) return;
    buf_push(buf, '\0');
    // Deduplicate
    for (size_t i = 0; i < arr->len; i++) {
        if (strcmp(arr->items[i], buf->data) == 0) {
            buf->len = 0;
            return;
        }
    }
    if (arr->len >= *cap_tokens) {
        *cap_tokens = *cap_tokens ? *cap_tokens * 2 : 64;
        arr->items = (const char **)realloc(arr->items, sizeof(char *) * (*cap_tokens));
    }
    arr->items[arr->len++] = strdup(buf->data);
    buf->len = 0;
}

static int is_word_char(unsigned char c) {
    return isalnum(c) || c > 127;
}

static void tokenize_words(const char *text, wa_string_array *out_tokens) {
    wa_buffer buf;
    buf_init(&buf);
    size_t cap_tokens = 0;
    out_tokens->items = NULL;
    out_tokens->len = 0;

    const size_t len = strlen(text);
    size_t idx = 0;
    while (idx < len) {
        size_t prev = idx;
        uint32_t cp = utf8_next(text, len, &idx);
        if (cp < 128) cp = (uint32_t)tolower((int)cp);
        if (is_letter(cp)) {
            append_cp(&buf, cp);
        } else {
            push_token(out_tokens, &buf, &cap_tokens);
        }
        if (idx == prev) idx++;
    }
    push_token(out_tokens, &buf, &cap_tokens);
    free(buf.data);
}

static void free_tokens(wa_string_array *tokens) {
    if (tokens->items == NULL) return;
    for (size_t i = 0; i < tokens->len; i++) {
        free((void *)tokens->items[i]);
    }
    free(tokens->items);
    tokens->items = NULL;
    tokens->len = 0;
}

static void tokenize_bigrams(const wa_u32_array *codepoints, wa_string_array *out_tokens) {
    wa_buffer buf;
    buf_init(&buf);
    size_t cap_tokens = 0;
    out_tokens->items = NULL;
    out_tokens->len = 0;

    if (codepoints->len < 2) return;
    for (size_t i = 0; i + 1 < codepoints->len; i++) {
        buf_reset(&buf);
        append_cp(&buf, codepoints->items[i]);
        append_cp(&buf, codepoints->items[i + 1]);
        push_token(out_tokens, &buf, &cap_tokens);
    }
    free(buf.data);
}

static void collect_characters(const char *text, wa_u32_array *chars, wa_u32_array *codepoints) {
    u32_init(chars);
    u32_init(codepoints);
    size_t len = strlen(text);
    size_t idx = 0;
    while (idx < len) {
        uint32_t cp = utf8_next(text, len, &idx);
        if (cp < 128) cp = (uint32_t)tolower((int)cp);
        if (is_letter(cp)) {
            u32_push_unique(chars, cp);
            u32_reserve(codepoints, codepoints->len + 1);
            codepoints->items[codepoints->len++] = cp;
        }
    }
}

static double overlap_tokens(const wa_string_array *tokens, const wa_frequency_list *freq) {
    if (!tokens || !freq || tokens->len == 0 || freq->token_count == 0) return 0.0;
    double score = 0.0;
    for (size_t i = 0; i < tokens->len; i++) {
        const char *t = tokens->items[i];
        for (size_t r = 0; r < freq->token_count; r++) {
            if (wa_streq(t, freq->tokens[r])) {
                score += 1.0 / log2((double)r + 1.5);
                break;
            }
        }
    }
    return score;
}

static double prior_for(const wa_prior *priors, size_t prior_count, const char *lang) {
    if (priors == NULL || lang == NULL) return 0.0;
    for (size_t i = 0; i < prior_count; i++) {
        if (wa_streq(priors[i].language, lang)) {
            return priors[i].prior;
        }
    }
    return 0.0;
}

static double character_overlap(const wa_u32_array *text_chars, const wa_alphabet *alpha) {
    if (!text_chars || !alpha || text_chars->len == 0 || alpha->lowercase_len == 0) {
        return 0.0;
    }

    wa_u32_array alphabet_chars;
    u32_init(&alphabet_chars);
    for (size_t i = 0; i < alpha->lowercase_len; i++) {
        const char *ch = alpha->lowercase[i];
        size_t idx = 0;
        uint32_t cp = utf8_next(ch, strlen(ch), &idx);
        u32_push_unique(&alphabet_chars, cp);
    }

    size_t match = 0;
    size_t nonmatch = 0;
    for (size_t i = 0; i < text_chars->len; i++) {
        uint32_t cp = text_chars->items[i];
        int found = 0;
        for (size_t j = 0; j < alphabet_chars.len; j++) {
            if (alphabet_chars.items[j] == cp) {
                found = 1;
                break;
            }
        }
        if (found) match++; else nonmatch++;
    }

    if (match == 0) {
        free(alphabet_chars.items);
        return 0.0;
    }

    double coverage = (double)match / (double)text_chars->len;
    double penalty = (double)nonmatch / (double)text_chars->len;
    double alphabetCoverage = (double)match / (double)alphabet_chars.len;
    free(alphabet_chars.items);

    double score = coverage * 0.6 - penalty * 0.2 + alphabetCoverage * 0.2;
    return score < 0.0 ? 0.0 : score;
}

static double lookup_char_freq(const wa_alphabet *alpha, uint32_t cp) {
    if (!alpha || alpha->frequency_len == 0) return 0.0;
    char tmp[5] = {0};
    size_t n = utf8_encode(cp, tmp);
    tmp[n] = '\0';
    for (size_t i = 0; i < alpha->frequency_len; i++) {
        if (wa_streq(alpha->frequency[i].ch, tmp)) {
            return alpha->frequency[i].freq;
        }
    }
    return 0.0;
}

static double frequency_overlap(const wa_u32_array *text_chars, const wa_alphabet *alpha) {
    if (!text_chars || !alpha || text_chars->len == 0 || alpha->frequency_len == 0) {
        return 0.0;
    }
    double score = 0.0;
    double total = 0.0;
    for (size_t i = 0; i < text_chars->len; i++) {
        double f = lookup_char_freq(alpha, text_chars->items[i]);
        if (f > 0.0) {
            score += f;
            total += f;
        }
    }
    return total > 0.0 ? score / (total > 0.001 ? total : 0.001) : 0.0;
}

static double compute_overlap(const wa_frequency_list *freq,
                              const wa_string_array *tokens) {
    if (freq == NULL || tokens == NULL || tokens->len == 0) return 0.0;
    size_t hits = 0;
    for (size_t i = 0; i < tokens->len; i++) {
        const char *t = tokens->items[i];
        for (size_t j = 0; j < freq->token_count; j++) {
            if (wa_streq(t, freq->tokens[j])) {
                hits++;
                break;
            }
        }
    }
    if (freq->token_count == 0) return 0.0;
    return (double)hits / (double)freq->token_count;
}

static int cmp_detect_result(const void *a, const void *b) {
    const wa_detect_result *ra = (const wa_detect_result *)a;
    const wa_detect_result *rb = (const wa_detect_result *)b;
    if (ra->score < rb->score) return 1;
    if (ra->score > rb->score) return -1;
    return 0;
}

wa_detect_result_array wa_detect_languages(const char *text,
                                           const char **candidate_langs,
                                           size_t candidate_count,
                                           const wa_prior *priors,
                                           size_t prior_count,
                                           size_t topk) {
    wa_detect_result_array results = { .items = NULL, .len = 0 };
    if (text == NULL || *text == '\0') return results;

    wa_string_array word_tokens;
    tokenize_words(text, &word_tokens);
    wa_u32_array chars;
    wa_u32_array codepoints;
    collect_characters(text, &chars, &codepoints);
    wa_string_array bigram_tokens;
    tokenize_bigrams(&codepoints, &bigram_tokens);

    // If no candidates provided, use all languages with frequency lists.
    const wa_frequency_list *candidate_ptrs[WA_FREQUENCY_LISTS_COUNT];
    const wa_frequency_list **candidates = candidate_ptrs;
    size_t candidates_len = 0;
    if (candidate_count > 0) {
        for (size_t i = 0; i < candidate_count; i++) {
            const wa_frequency_list *entry = find_freq_list(candidate_langs[i]);
            if (entry) {
                candidate_ptrs[candidates_len++] = entry;
            }
        }
    } else {
        for (size_t i = 0; i < WA_FREQUENCY_LISTS_COUNT; i++) {
            candidate_ptrs[candidates_len++] = &WA_FREQUENCY_LISTS[i];
        }
    }

    wa_detect_result *tmp = (wa_detect_result *)malloc(
        sizeof(wa_detect_result) * candidates_len);
    size_t tmp_len = 0;
    for (size_t i = 0; i < candidates_len; i++) {
        const wa_frequency_list *freq = candidates[i];
        const wa_string_array *tokens =
            wa_streq(freq->mode, "bigram") ? &bigram_tokens : &word_tokens;
        double word_overlap = overlap_tokens(tokens, freq);
        if (tokens->len > 0) {
            word_overlap /= sqrt((double)tokens->len + 3.0);
        }
        double prior = prior_for(priors, prior_count, freq->language);
        double word_score = PRIOR_WEIGHT * prior + FREQ_WEIGHT * word_overlap;
        if (word_score > 0.05) {
            tmp[tmp_len].language = freq->language;
            tmp[tmp_len].score = word_score + 0.15; // boost word-based hits
            tmp_len++;
            continue;
        }

        const wa_alphabet *alpha = wa_load_alphabet(freq->language, NULL);
        if (alpha && chars.len > 0) {
            double c_overlap = character_overlap(&chars, alpha);
            double f_overlap = frequency_overlap(&chars, alpha);
            double char_score = c_overlap * 0.6 + f_overlap * 0.4;
            double final_score = PRIOR_WEIGHT * prior + CHAR_WEIGHT * char_score;
            if (final_score > 0.02) {
                tmp[tmp_len].language = freq->language;
                tmp[tmp_len].score = final_score;
                tmp_len++;
            }
        }
    }

    free_tokens(&word_tokens);
    free_tokens(&bigram_tokens);
    free(chars.items);
    free(codepoints.items);

    if (tmp_len > 1) {
        qsort(tmp, tmp_len, sizeof(wa_detect_result), cmp_detect_result);
    }
    if (topk > 0 && tmp_len > topk) {
        tmp_len = topk;
    }

    results.items = tmp;
    results.len = tmp_len;
    return results;
}

void wa_free_detect_results(wa_detect_result_array *results) {
    if (results == NULL || results->items == NULL) return;
    free(results->items);
    results->items = NULL;
    results->len = 0;
}

// --- keyboards ---

wa_string_array wa_get_available_layouts(void) {
    wa_string_array arr = { .items = NULL, .len = WA_KEYBOARD_LAYOUTS_COUNT };
    arr.items = WA_LAYOUT_IDS;
    return arr;
}

const wa_keyboard_layout *wa_load_keyboard(const char *layout_id) {
    return find_keyboard(layout_id);
}

wa_keyboard_layer wa_extract_layer(const wa_keyboard_layout *layout,
                                   const char *layer_name) {
    wa_keyboard_layer empty = { .name = NULL, .entries = NULL, .entry_count = 0 };
    if (layout == NULL || layer_name == NULL) return empty;
    for (size_t i = 0; i < layout->layer_count; i++) {
        const wa_keyboard_layer *layer = &layout->layers[i];
        if (wa_streq(layer->name, layer_name)) {
            return *layer;
        }
    }
    return empty;
}
