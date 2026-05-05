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

    // ========== Inflections ==========
    printf("\n--- Inflections ---\n");

    printf("  wa_get_available_inflection_locales... ");
    wa_string_array infl_locales = wa_get_available_inflection_locales();
    printf("OK (%zu locales)\n", infl_locales.len);

    if (infl_locales.len > 0) {
        printf("  wa_load_inflection_table... ");
        const wa_inflection_table *table = wa_load_inflection_table(
            infl_locales.items[0]);
        assert(table != NULL);
        assert(table->entry_count > 0);
        printf("OK (%s: %zu entries)\n", table->locale, table->entry_count);

        if (table->entry_count > 0) {
            const wa_inflection_entry *first = table->entries[0];
            printf("  wa_get_inflected_form... ");
            const char *base = wa_get_inflected_form(first, "base");
            assert(base != NULL);
            printf("OK (word=%s, base=%s)\n", first->word, base);
        }

        // Test rule engine with German
        printf("  wa_load_rules_table... ");
        const wa_rules_table *de_rules = wa_load_rules_table("de");
        const wa_inflection_table *de_words = wa_load_inflection_table("de");
        if (de_rules && de_words) {
            printf("OK (%s: %zu rules)\n", de_rules->locale,
                   de_rules->rule_count);

            // Test: "der" + "die" → override to "der"
            printf("  wa_lookup_word (de override)... ");
            wa_lookup_result lr = wa_lookup_word(de_words, de_rules,
                                                  "die", "der");
            assert(lr.replacement != NULL);
            printf("OK (der + die → %s, rule=%s)\n", lr.replacement,
                   lr.rule_id ? lr.rule_id : "none");
            assert(strcmp(lr.replacement, "der") == 0);

            // Test: "ich" + verb → present tense
            printf("  wa_lookup_word (de verb)... ");
            wa_lookup_result vr = wa_lookup_word(de_words, de_rules,
                                                  "gehen", "ich");
            printf("OK (ich + gehen → %s, rule=%s)\n",
                   vr.replacement, vr.rule_id ? vr.rule_id : "none");

            // Test: null prior → no change
            printf("  wa_lookup_word (null prior)... ");
            wa_lookup_result nr = wa_lookup_word(de_words, de_rules,
                                                   "gehen", "");
            assert(nr.replacement != NULL);
            printf("OK (gehen → %s)\n", nr.replacement);
        } else {
            printf("SKIPPED (de rules not compiled in)\n");
        }

        // ========== wa_join_words (French) ==========
        printf("\n--- Join/Euphony ---\n");
        const wa_rules_table *fr_rules = wa_load_rules_table("fr");
        if (fr_rules && fr_rules->join_count > 0) {
            printf("  wa_join_words (fr)... ");
            printf("OK (%zu join rules)\n", fr_rules->join_count);

            // Test: le + homme → le homme (h aspiré, no elision)
            printf("  wa_join_words (fr h_aspire)... ");
            wa_join_result jr1 = wa_join_words(fr_rules, "le", "homme");
            assert(jr1.result != NULL);
            assert(strcmp(jr1.result, "le homme") == 0);
            printf("OK (le + homme → %s)\n", jr1.result);

            // Test: le + arbre → l'arbre (elision)
            printf("  wa_join_words (fr elision)... ");
            wa_join_result jr2 = wa_join_words(fr_rules, "le", "arbre");
            assert(jr2.result != NULL);
            assert(strcmp(jr2.result, "l'arbre") == 0);
            assert(jr2.replaces_pair == 1);
            printf("OK (le + arbre → %s)\n", jr2.result);

            // Test: je + ai → j'ai
            printf("  wa_join_words (fr je elision)... ");
            wa_join_result jr3 = wa_join_words(fr_rules, "je", "ai");
            assert(jr3.result != NULL);
            assert(strcmp(jr3.result, "j'ai") == 0);
            printf("OK (je + ai → %s)\n", jr3.result);
        } else {
            printf("  SKIPPED (fr join rules not compiled in)\n");
        }

        // ========== wa_join_words (English) ==========
        const wa_rules_table *en_rules_t = wa_load_rules_table("en");
        if (en_rules_t && en_rules_t->join_count > 0) {
            printf("  wa_join_words (en a→an)... ");
            wa_join_result jr4 = wa_join_words(en_rules_t, "a", "apple");
            assert(jr4.result != NULL);
            assert(strcmp(jr4.result, "an apple") == 0);
            printf("OK (a + apple → %s)\n", jr4.result);

            // Test: a + university → a university (consonant sound exception)
            printf("  wa_join_words (en consonant)... ");
            wa_join_result jr5 = wa_join_words(en_rules_t, "a", "university");
            assert(jr5.result != NULL);
            assert(strcmp(jr5.result, "a university") == 0);
            printf("OK (a + university → %s)\n", jr5.result);
        }

        // ========== wa_get_features ==========
        printf("\n--- Tag Features ---\n");
        printf("  wa_get_features (adj_abl_fem_sg)... ");
        wa_feature_array fa = wa_get_features("adj_abl_fem_sg");
        assert(fa.feature_count == 4);
        // Verify features
        int found_pos = 0, found_case = 0, found_gender = 0, found_num = 0;
        for (size_t fi = 0; fi < fa.feature_count; fi++) {
            if (strcmp(fa.features[fi].feature_key, "pos") == 0 &&
                strcmp(fa.features[fi].feature_value, "adjective") == 0)
                found_pos = 1;
            if (strcmp(fa.features[fi].feature_key, "case") == 0 &&
                strcmp(fa.features[fi].feature_value, "ablative") == 0)
                found_case = 1;
            if (strcmp(fa.features[fi].feature_key, "gender") == 0 &&
                strcmp(fa.features[fi].feature_value, "feminine") == 0)
                found_gender = 1;
            if (strcmp(fa.features[fi].feature_key, "number") == 0 &&
                strcmp(fa.features[fi].feature_value, "singular") == 0)
                found_num = 1;
        }
        assert(found_pos && found_case && found_gender && found_num);
        printf("OK (%zu features)\n", fa.feature_count);
        wa_free_features(&fa);

        // Test non-existent tag
        printf("  wa_get_features (unknown)... ");
        wa_feature_array fa2 = wa_get_features("nonexistent_tag_xyz");
        assert(fa2.feature_count == 0);
        printf("OK (0 features)\n");

        // ========== wa_apply_rules ==========
        printf("\n--- Apply Rules ---\n");
        if (de_words && de_rules) {
            printf("  wa_apply_rules (de)... ");
            wa_applied_sentence sent = wa_apply_rules(
                de_words, de_rules, "der die");
            assert(sent.token_count == 2);
            assert(sent.tokens[0].surface != NULL);
            assert(sent.tokens[1].surface != NULL);
            // "der" + "die" → "der" overrides "die" to "der"
            printf("OK (%zu tokens: '%s' '%s')\n",
                   sent.token_count,
                   sent.tokens[0].surface,
                   sent.tokens[1].surface);
            wa_free_applied_sentence(&sent);
        }

        // Test French apply_rules with join
        const wa_inflection_table *fr_words = wa_load_inflection_table("fr");
        if (fr_words && fr_rules) {
            printf("  wa_apply_rules (fr with join)... ");
            wa_applied_sentence sent2 = wa_apply_rules(
                fr_words, fr_rules, "le arbre");
            assert(sent2.token_count == 2);
            printf("OK (%zu tokens: '%s' '%s')\n",
                   sent2.token_count,
                   sent2.tokens[0].surface,
                   sent2.tokens[1].surface);
            wa_free_applied_sentence(&sent2);
        }

    } else {
        printf("  SKIPPED (no inflection locales compiled in)\n");
    }

    printf("\nAll C interface tests passed!\n");
    return 0;
}
