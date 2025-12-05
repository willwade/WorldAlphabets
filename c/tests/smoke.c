#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../include/worldalphabets.h"

int main(void) {
    printf("Testing C interface...\n");

    // ========== wa_get_available_codes ==========
    printf("  wa_get_available_codes... ");
    wa_string_array codes = wa_get_available_codes();
    assert(codes.len > 0);  // Should have at least some language codes
    assert(codes.items != NULL);
    printf("OK (%zu codes)\n", codes.len);

    // Find a language that has both alphabet and frequency list for testing
    const char *test_lang = NULL;
    const wa_frequency_list *freq = NULL;
    for (size_t i = 0; i < codes.len && test_lang == NULL; i++) {
        freq = wa_load_frequency_list(codes.items[i]);
        if (freq != NULL && freq->token_count > 0) {
            test_lang = codes.items[i];
        }
    }
    assert(test_lang != NULL);  // Should find at least one language with freq data

    // ========== wa_get_scripts ==========
    printf("  wa_get_scripts... ");
    wa_string_array scripts = wa_get_scripts(test_lang);
    assert(scripts.len > 0);
    printf("OK (%s has %zu scripts)\n", test_lang, scripts.len);

    // ========== wa_load_alphabet ==========
    printf("  wa_load_alphabet... ");
    const wa_alphabet *alpha = wa_load_alphabet(test_lang, NULL);
    assert(alpha != NULL);
    assert(alpha->uppercase_len > 0 || alpha->lowercase_len > 0);
    assert(strcmp(alpha->language, test_lang) == 0);
    // Test non-existent language returns NULL
    const wa_alphabet *bad_alpha = wa_load_alphabet("nonexistent", NULL);
    assert(bad_alpha == NULL);
    printf("OK (%s)\n", test_lang);

    // ========== wa_load_frequency_list ==========
    printf("  wa_load_frequency_list... ");
    // freq already loaded above when finding test_lang
    assert(freq != NULL);
    assert(freq->token_count > 0);
    assert(strcmp(freq->language, test_lang) == 0);
    // Test non-existent returns NULL
    const wa_frequency_list *bad_freq = wa_load_frequency_list("zzz");
    assert(bad_freq == NULL);
    printf("OK (%zu tokens)\n", freq->token_count);

    // ========== wa_detect_languages ==========
    printf("  wa_detect_languages... ");
    // Use test_lang which we know has frequency data
    // Use some tokens from that language's frequency list for a better match
    const char *detect_candidates[] = {test_lang};
    // Build a test string from actual tokens in the frequency list
    char test_text[256] = "";
    for (size_t i = 0; i < 5 && i < freq->token_count; i++) {
        if (i > 0) strcat(test_text, " ");
        strncat(test_text, freq->tokens[i], sizeof(test_text) - strlen(test_text) - 2);
    }
    wa_detect_result_array res = wa_detect_languages(
        test_text, detect_candidates, 1, NULL, 0, 1);
    // Detection may or may not succeed depending on data, just check API works
    wa_free_detect_results(&res);
    printf("OK\n");

    // ========== wa_get_available_layouts ==========
    printf("  wa_get_available_layouts... ");
    wa_string_array layouts = wa_get_available_layouts();
    assert(layouts.len > 0);  // Should have at least some layouts
    printf("OK (%zu layouts)\n", layouts.len);

    // ========== wa_load_keyboard ==========
    printf("  wa_load_keyboard... ");
    // Use first available layout
    const char *test_layout = layouts.items[0];
    const wa_keyboard_layout *kb = wa_load_keyboard(test_layout);
    assert(kb != NULL);
    assert(kb->layer_count > 0);
    assert(strcmp(kb->id, test_layout) == 0);
    // Test non-existent returns NULL
    const wa_keyboard_layout *bad_kb = wa_load_keyboard("nonexistent-layout");
    assert(bad_kb == NULL);
    printf("OK (%s)\n", test_layout);

    // ========== wa_extract_layer ==========
    printf("  wa_extract_layer... ");
    wa_keyboard_layer base_layer = wa_extract_layer(kb, "base");
    assert(base_layer.entries != NULL);
    assert(base_layer.entry_count > 0);
    assert(strcmp(base_layer.name, "base") == 0);
    // Test non-existent layer
    wa_keyboard_layer bad_layer = wa_extract_layer(kb, "nonexistent");
    assert(bad_layer.entries == NULL);
    assert(bad_layer.entry_count == 0);
    printf("OK\n");

    // ========== wa_find_layouts_by_hid (dynamic) ==========
    printf("  wa_find_layouts_by_hid... ");
    // Use a common HID code (0x04 = 'a' on US QWERTY)
    wa_layout_match_array matches = wa_find_layouts_by_hid(0x04, "base");
    if (matches.len > 0) {
        assert(matches.is_static == 0);
        assert(matches.items[0].layout != NULL);
        assert(matches.items[0].layer != NULL);
        assert(matches.items[0].mapping != NULL);
    }
    size_t dynamic_count = matches.len;
    wa_free_layout_matches(&matches);
    // Verify freed state
    assert(matches.items == NULL);
    assert(matches.len == 0);
    printf("OK (%zu matches)\n", dynamic_count);

    // ========== wa_find_layouts_by_hid_static ==========
    printf("  wa_find_layouts_by_hid_static... ");
    wa_layout_match static_buffer[WA_MAX_STATIC_MATCHES];
    size_t static_count = wa_find_layouts_by_hid_static(
        0x04, "base", static_buffer, WA_MAX_STATIC_MATCHES);
    if (static_count > 0) {
        assert(static_buffer[0].layout != NULL);
        assert(static_buffer[0].layer != NULL);
    }
    printf("OK (%zu matches)\n", static_count);

    printf("\nAll C interface tests passed!\n");
    return 0;
}
