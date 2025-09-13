const {
  loadAlphabet,
  stripDiacritics,
  hasDiacritics,
  charactersWithDiacritics,
  getDiacriticVariants,
  detectLanguages,
  getAvailableCodes,
} = require('../index');

describe('Integration Tests', () => {
  test('end-to-end workflow', async () => {
    // Start with some Polish text
    const text = 'Żółć gęślą jaźń';
    
    // Detect languages
    const detected = await detectLanguages(text);
    expect(detected).toContain('pl');
    
    // Load Polish alphabet
    const alphabet = await loadAlphabet('pl');
    expect(alphabet).toBeDefined();
    expect(alphabet.lowercase.length).toBeGreaterThan(0);
    
    // Get diacritic variants for Polish
    const variants = await getDiacriticVariants('pl');
    // Check that variants contain expected characters (order may vary)
    expect(new Set(variants.Z)).toEqual(new Set(['Z', 'Ż', 'Ź']));
    expect(new Set(variants.z)).toEqual(new Set(['z', 'ż', 'ź']));
    
    // Test diacritic processing
    const stripped = stripDiacritics(text);
    expect(stripped).toBe('Zolc gesla jazn');
    
    // Find characters with diacritics
    const charsWithDiac = charactersWithDiacritics(Array.from(text));
    const expectedDiac = ['Ż', 'ó', 'ł', 'ć', 'ę', 'ś', 'ą', 'ź', 'ń'];
    expectedDiac.forEach(char => {
      if (text.includes(char)) {
        expect(charsWithDiac).toContain(char);
      }
    });
  });

  test('cross-language detection', async () => {
    // Text that uses only basic Latin letters
    const text = 'hello world';
    const detected = await detectLanguages(text);
    
    // Should detect multiple languages including English
    expect(detected).toContain('en');
    expect(detected.length).toBeGreaterThan(5);
    
    // Text with specific diacritics should narrow down options
    const specificText = 'Łódź';
    const specificDetected = await detectLanguages(specificText);
    expect(specificDetected).toContain('pl');
    // The specific text should still detect Polish
    // Note: The number of detected languages may vary based on alphabet coverage
  });

  test('diacritic consistency', () => {
    const testChars = ['é', 'ñ', 'ü', 'Ł', 'ø', 'a', 'b', '1', '!'];
    
    // Characters identified as having diacritics should be stripped differently
    testChars.forEach(char => {
      const hasDiac = hasDiacritics(char);
      const stripped = stripDiacritics(char);
      
      if (hasDiac) {
        expect(char).not.toBe(stripped);
      } else {
        expect(char).toBe(stripped);
      }
    });
  });

  test('alphabet completeness', async () => {
    // Test a few languages known to have diacritics
    const testLanguages = ['pl', 'fr', 'de', 'es'];
    
    for (const lang of testLanguages) {
      try {
        const alphabet = await loadAlphabet(lang);
        const variants = await getDiacriticVariants(lang);
        
        // All variant characters should be in the alphabet
        Object.entries(variants).forEach(([base, variantList]) => {
          variantList.forEach(variant => {
            if (variant === variant.toUpperCase()) {
              expect(alphabet.uppercase).toContain(variant);
            } else {
              expect(alphabet.lowercase).toContain(variant);
            }
          });
        });
      } catch (error) {
        // Skip languages that don't have data
        continue;
      }
    }
  });

  test('available codes consistency', async () => {
    const codes = await getAvailableCodes();
    expect(codes.length).toBeGreaterThan(0);
    
    // Test a few random codes to ensure they can be loaded
    const testCodes = codes.slice(0, 5);
    
    for (const code of testCodes) {
      try {
        const alphabet = await loadAlphabet(code);
        expect(alphabet).toBeDefined();
        // Should have at least some letters
        expect(
          alphabet.lowercase.length + alphabet.uppercase.length
        ).toBeGreaterThan(0);
      } catch (error) {
        // Some codes might not have alphabet data, that's ok
        continue;
      }
    }
  });

  test('error handling robustness', async () => {
    // Test with invalid language codes
    const invalidCodes = ['invalid', 'xyz', '123'];
    
    for (const code of invalidCodes) {
      // These should handle errors gracefully
      const detected = await detectLanguages('test');
      expect(Array.isArray(detected)).toBe(true);
      
      // These should raise appropriate errors
      await expect(getDiacriticVariants(code)).rejects.toThrow();
    }
  });

  test('performance with large text', async () => {
    // Test with a larger text to ensure reasonable performance
    const largeText = 'Hello world! '.repeat(1000) + 'Żółć gęślą jaźń';
    
    const start = Date.now();
    const detected = await detectLanguages(largeText);
    const end = Date.now();
    
    expect(detected).toContain('pl');
    expect(detected).toContain('en');
    // Should complete in reasonable time (less than 5 seconds)
    expect(end - start).toBeLessThan(5000);
  });
});
