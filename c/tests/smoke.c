#include <assert.h>
#include <stdio.h>

#include "../include/worldalphabets.h"

int main(void) {
    // Alphabet basics
    const wa_alphabet *alpha = wa_load_alphabet("fr", "Latn");
    assert(alpha != NULL);
    assert(alpha->uppercase_len > 20);

    // Frequency list
    const wa_frequency_list *freq = wa_load_frequency_list("fr");
    assert(freq != NULL);
    assert(freq->token_count > 100);

    // Detection with priors boost
    const char *candidates[] = {"fr", "en"};
    wa_prior priors[] = {{"fr", 0.6}, {"en", 0.4}};
    wa_detect_result_array res = wa_detect_languages(
        "bonjour le monde", candidates, 2, priors, 2, 2);
    assert(res.len > 0);
    assert(res.items[0].language != NULL);
    wa_free_detect_results(&res);

    // Keyboard layout
    const wa_keyboard_layout *kb = wa_load_keyboard("fr-french-standard-azerty");
    assert(kb != NULL);
    assert(kb->layer_count > 0);
    wa_keyboard_layer base_layer = wa_extract_layer(kb, "base");
    assert(base_layer.entries != NULL);
    assert(base_layer.entry_count > 10);

    // Dynamic allocation version
    wa_layout_match_array matches = wa_find_layouts_by_hid(0x64, "base");
    assert(matches.len > 0);
    assert(matches.is_static == 0);
    size_t dynamic_count = matches.len;
    wa_free_layout_matches(&matches);

    // Static buffer version (for embedded devices)
    wa_layout_match static_buffer[WA_MAX_STATIC_MATCHES];
    size_t static_count = wa_find_layouts_by_hid_static(
        0x64, "base", static_buffer, WA_MAX_STATIC_MATCHES);
    assert(static_count > 0);
    // Verify static and dynamic find same matches
    assert(static_count == dynamic_count || static_count == WA_MAX_STATIC_MATCHES);

    printf("smoke tests passed\n");
    return 0;
}
