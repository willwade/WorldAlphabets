#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../include/worldalphabets.h"

int main(void) {
    printf("Testing C interface...\n");

    // ========== wa_get_available_codes ==========
    printf("  wa_get_available_codes... ");
    wa_string_array codes = wa_get_available_codes();
    assert(codes.len > 10);  // Should have many language codes
    assert(codes.items != NULL);
    // Check for known language codes
    int found_fr = 0, found_en = 0;
    for (size_t i = 0; i < codes.len; i++) {
        if (strcmp(codes.items[i], "fr") == 0) found_fr = 1;
        if (strcmp(codes.items[i], "en") == 0) found_en = 1;
    }
    assert(found_fr && found_en);
    printf("OK (%zu codes)\n", codes.len);

    // ========== wa_get_scripts ==========
    printf("  wa_get_scripts... ");
    wa_string_array scripts = wa_get_scripts("zh");  // Chinese has multiple
    assert(scripts.len > 0);
    printf("OK (zh has %zu scripts)\n", scripts.len);

    // ========== wa_load_alphabet ==========
    printf("  wa_load_alphabet... ");
    const wa_alphabet *alpha = wa_load_alphabet("fr", "Latn");
    assert(alpha != NULL);
    assert(alpha->uppercase_len > 20);
    assert(alpha->lowercase_len > 20);
    assert(alpha->frequency_len > 0);
    assert(strcmp(alpha->language, "fr") == 0);
    // Test non-existent language returns NULL
    const wa_alphabet *bad_alpha = wa_load_alphabet("nonexistent", NULL);
    assert(bad_alpha == NULL);
    printf("OK\n");

    // ========== wa_load_frequency_list ==========
    printf("  wa_load_frequency_list... ");
    const wa_frequency_list *freq = wa_load_frequency_list("fr");
    assert(freq != NULL);
    assert(freq->token_count > 100);
    assert(strcmp(freq->language, "fr") == 0);
    // Test non-existent returns NULL
    const wa_frequency_list *bad_freq = wa_load_frequency_list("zzz");
    assert(bad_freq == NULL);
    printf("OK (%zu tokens)\n", freq->token_count);

    // ========== wa_detect_languages ==========
    printf("  wa_detect_languages... ");
    const char *candidates[] = {"fr", "en", "de"};
    wa_prior priors[] = {{"fr", 0.4}, {"en", 0.3}, {"de", 0.3}};
    wa_detect_result_array res = wa_detect_languages(
        "bonjour le monde comment allez-vous", candidates, 3, priors, 3, 2);
    assert(res.len > 0);
    assert(res.items[0].language != NULL);
    // French should be detected for French text
    assert(strcmp(res.items[0].language, "fr") == 0);
    wa_free_detect_results(&res);
    // Test with no priors
    wa_detect_result_array res2 = wa_detect_languages(
        "hello world", candidates, 3, NULL, 0, 1);
    assert(res2.len > 0);
    wa_free_detect_results(&res2);
    printf("OK\n");

    // ========== wa_get_available_layouts ==========
    printf("  wa_get_available_layouts... ");
    wa_string_array layouts = wa_get_available_layouts();
    assert(layouts.len > 50);  // Should have many layouts
    int found_azerty = 0, found_qwertz = 0;
    for (size_t i = 0; i < layouts.len; i++) {
        if (strstr(layouts.items[i], "azerty")) found_azerty = 1;
        if (strstr(layouts.items[i], "qwertz")) found_qwertz = 1;
    }
    assert(found_azerty && found_qwertz);
    printf("OK (%zu layouts)\n", layouts.len);

    // ========== wa_load_keyboard ==========
    printf("  wa_load_keyboard... ");
    const wa_keyboard_layout *kb = wa_load_keyboard("fr-french-standard-azerty");
    assert(kb != NULL);
    assert(kb->layer_count > 0);
    assert(strcmp(kb->id, "fr-french-standard-azerty") == 0);
    // Test non-existent returns NULL
    const wa_keyboard_layout *bad_kb = wa_load_keyboard("nonexistent-layout");
    assert(bad_kb == NULL);
    printf("OK\n");

    // ========== wa_extract_layer ==========
    printf("  wa_extract_layer... ");
    wa_keyboard_layer base_layer = wa_extract_layer(kb, "base");
    assert(base_layer.entries != NULL);
    assert(base_layer.entry_count > 10);
    assert(strcmp(base_layer.name, "base") == 0);
    wa_keyboard_layer shift_layer = wa_extract_layer(kb, "shift");
    assert(shift_layer.entries != NULL);
    // Test non-existent layer
    wa_keyboard_layer bad_layer = wa_extract_layer(kb, "nonexistent");
    assert(bad_layer.entries == NULL);
    assert(bad_layer.entry_count == 0);
    printf("OK\n");

    // ========== wa_find_layouts_by_hid (dynamic) ==========
    printf("  wa_find_layouts_by_hid... ");
    wa_layout_match_array matches = wa_find_layouts_by_hid(0x64, "base");
    assert(matches.len > 0);
    assert(matches.is_static == 0);
    // Verify match structure
    assert(matches.items[0].layout != NULL);
    assert(matches.items[0].layer != NULL);
    assert(matches.items[0].mapping != NULL);
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
        0x64, "base", static_buffer, WA_MAX_STATIC_MATCHES);
    assert(static_count > 0);
    // Verify match structure
    assert(static_buffer[0].layout != NULL);
    assert(static_buffer[0].layer != NULL);
    // Verify static and dynamic find same number of matches
    assert(static_count == dynamic_count || static_count == WA_MAX_STATIC_MATCHES);
    // Test with small buffer (should truncate)
    wa_layout_match small_buffer[2];
    size_t small_count = wa_find_layouts_by_hid_static(
        0x64, "base", small_buffer, 2);
    assert(small_count <= 2);
    printf("OK (%zu matches)\n", static_count);

    printf("\nAll C interface tests passed!\n");
    return 0;
}
