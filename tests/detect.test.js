const { detectLanguages } = require('../index');

describe('detectLanguages', () => {
  test('detects Polish text', async () => {
    const langs = await detectLanguages('Żółć');
    expect(langs).toContain('pl');
  });

  test('detects English text', async () => {
    const langs = await detectLanguages('hello world');
    expect(langs).toContain('en');
  });

  test('handles mixed diacritics', async () => {
    const langs = await detectLanguages('café naïve résumé');
    expect(langs.length).toBeGreaterThan(0);
  });

  test('handles special characters', async () => {
    const langs = await detectLanguages('Łódź');
    expect(langs).toContain('pl');
  });

  test('handles empty input', async () => {
    const langs = await detectLanguages('');
    expect(langs).toEqual([]);
  });

  test('handles no letters', async () => {
    const langs = await detectLanguages('123 !@# $%^');
    expect(langs).toEqual([]);
  });

  test('handles numbers and symbols with letters', async () => {
    const langs = await detectLanguages('hello123!@#');
    expect(langs).toContain('en');
  });

  test('handles single letter', async () => {
    const langs = await detectLanguages('a');
    expect(langs.length).toBeGreaterThan(10);
  });

  test('is case insensitive', async () => {
    const langsLower = await detectLanguages('hello');
    const langsUpper = await detectLanguages('HELLO');
    const langsMixed = await detectLanguages('Hello');

    expect(new Set(langsLower)).toEqual(new Set(langsUpper));
    expect(new Set(langsLower)).toEqual(new Set(langsMixed));
  });

  test('handles null and undefined', async () => {
    const langsNull = await detectLanguages(null);
    const langsUndefined = await detectLanguages(undefined);

    expect(langsNull).toEqual([]);
    expect(langsUndefined).toEqual([]);
  });
});
