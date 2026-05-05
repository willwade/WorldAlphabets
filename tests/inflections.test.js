const {
    getAvailableInflectionLocales,
    loadInflectionData,
    loadInflectionWords,
    getInflectionSummary,
    lookupWord,
    applyRules,
    clearInflectionCache,
} = require('../index');

describe('Inflection data Node API', () => {
    test('getAvailableInflectionLocales returns an array', async () => {
        const locales = await getAvailableInflectionLocales();
        expect(Array.isArray(locales)).toBe(true);
        expect(locales).toContain('ar');
    });

    test('loadInflectionWords throws for missing locale', async () => {
        await expect(loadInflectionWords('zz')).rejects.toThrow(/not found/);
    });

    test('loadInflectionData falls back to base language', async () => {
        const data = await loadInflectionData('en-TEST');
        expect(data.words._locale).toBe('en');
        expect(data.rules._locale).toBe('en');
    });

    test('getInflectionSummary returns locale metadata', async () => {
        const summary = await getInflectionSummary('en');
        expect(summary.locale).toBe('en');
        expect(summary.wordCount).toBeGreaterThan(0);
        expect(summary.ruleCount).toBeGreaterThan(0);
        expect(summary.testCount).toBeGreaterThan(0);
        expect(summary.posTypes).toContain('verb');
        expect(summary.inflectionKeys.length).toBeGreaterThan(0);
    });

    test('lookupWord returns a result with replacement', async () => {
        clearInflectionCache();
        const result = await lookupWord('en', 'run', 'she');
        expect(result.word).toBe('run');
        expect(result.replacement).toBeTruthy();
    });

    test('applyRules transforms text', async () => {
        clearInflectionCache();
        const result = await applyRules('en', 'she run');
        expect(typeof result).toBe('string');
        expect(result.length).toBeGreaterThan(0);
    });
});
