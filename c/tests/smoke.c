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
    wa_keyboard_layer base = wa_extract_layer(kb, "base");
    assert(base.entries != NULL);
    assert(base.entry_count > 10);
    printf("smoke tests passed\n");
    return 0;
}
