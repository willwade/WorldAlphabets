const {
  stripDiacritics,
  hasDiacritics,
  charactersWithDiacritics,
  getDiacriticVariants,
} = require('../index');

describe('stripDiacritics', () => {
  test('removes basic diacritics', () => {
    expect(stripDiacritics('café')).toBe('cafe');
    expect(stripDiacritics('naïve')).toBe('naive');
    expect(stripDiacritics('résumé')).toBe('resume');
  });

  test('handles special characters', () => {
    expect(stripDiacritics('Łódź')).toBe('Lodz');
    expect(stripDiacritics('Đorđe')).toBe('Dorde');
    expect(stripDiacritics('København')).toBe('Kobenhavn');
    expect(stripDiacritics('Þórr')).toBe('Torr');
    expect(stripDiacritics('Ðorðe')).toBe('Dorde');
  });

  test('handles mixed case', () => {
    expect(stripDiacritics('ÄÖÜäöü')).toBe('AOUaou');
    expect(stripDiacritics('ÇçÑñ')).toBe('CcNn');
  });

  test('handles edge cases', () => {
    expect(stripDiacritics('')).toBe('');
    expect(stripDiacritics('abc')).toBe('abc');
    expect(stripDiacritics('123')).toBe('123');
    expect(stripDiacritics('!@#')).toBe('!@#');
    expect(stripDiacritics(null)).toBe(null);
    expect(stripDiacritics(undefined)).toBe(undefined);
  });

  test('handles complex text', () => {
    const text = 'Żółć gęślą jaźń! 123 @#$';
    const expected = 'Zolc gesla jazn! 123 @#$';
    expect(stripDiacritics(text)).toBe(expected);
  });
});

describe('hasDiacritics', () => {
  test('detects characters with diacritics', () => {
    expect(hasDiacritics('é')).toBe(true);
    expect(hasDiacritics('ñ')).toBe(true);
    expect(hasDiacritics('ü')).toBe(true);
    expect(hasDiacritics('Ł')).toBe(true);
    expect(hasDiacritics('ø')).toBe(true);
  });

  test('detects characters without diacritics', () => {
    expect(hasDiacritics('e')).toBe(false);
    expect(hasDiacritics('n')).toBe(false);
    expect(hasDiacritics('u')).toBe(false);
    expect(hasDiacritics('L')).toBe(false);
    expect(hasDiacritics('o')).toBe(false);
  });

  test('handles edge cases', () => {
    expect(hasDiacritics('')).toBe(false);
    expect(hasDiacritics('1')).toBe(false);
    expect(hasDiacritics('!')).toBe(false);
    expect(hasDiacritics(null)).toBe(false);
    expect(hasDiacritics(undefined)).toBe(false);
  });

  test('handles multi-character strings', () => {
    expect(hasDiacritics('café')).toBe(true);
    expect(hasDiacritics('cafe')).toBe(false);
  });
});

describe('charactersWithDiacritics', () => {
  test('filters characters with diacritics', () => {
    const chars = ['a', 'é', 'ö', 'b', 'ñ'];
    expect(charactersWithDiacritics(chars)).toEqual(['é', 'ö', 'ñ']);
  });

  test('handles empty input', () => {
    expect(charactersWithDiacritics([])).toEqual([]);
  });

  test('handles no diacritics', () => {
    const chars = ['a', 'b', 'c'];
    expect(charactersWithDiacritics(chars)).toEqual([]);
  });

  test('handles all diacritics', () => {
    const chars = ['é', 'ñ', 'ü'];
    expect(charactersWithDiacritics(chars)).toEqual(['é', 'ñ', 'ü']);
  });

  test('handles empty strings in input', () => {
    const chars = ['a', '', 'é', ''];
    expect(charactersWithDiacritics(chars)).toEqual(['é']);
  });
});

describe('getDiacriticVariants', () => {
  test('groups Polish characters', async () => {
    const variants = await getDiacriticVariants('pl');
    expect(variants.L).toEqual(['L', 'Ł']);
    expect(variants.l).toEqual(['l', 'ł']);
    expect(variants.A).toEqual(['A', 'Ą']);
    expect(variants.a).toEqual(['a', 'ą']);
  });

  test('handles invalid language', async () => {
    await expect(getDiacriticVariants('invalid_lang')).rejects.toThrow();
  });

  test('works without explicit script', async () => {
    const variants = await getDiacriticVariants('pl');
    expect(variants).toHaveProperty('L');
    expect(variants).toHaveProperty('l');
  });
});

