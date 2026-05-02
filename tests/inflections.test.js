const {
    getAvailableInflectionLocales,
    loadInflectionData,
    loadInflectionWords,
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
});
