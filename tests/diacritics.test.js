const {
  stripDiacritics,
  hasDiacritics,
  charactersWithDiacritics,
  getDiacriticVariants,
} = require('../index');

describe('diacritic helpers', () => {
  test('stripDiacritics removes marks', () => {
    expect(stripDiacritics('café')).toBe('cafe');
  });

  test('hasDiacritics detects marks', () => {
    expect(hasDiacritics('é')).toBe(true);
    expect(hasDiacritics('e')).toBe(false);
  });

  test('charactersWithDiacritics filters', () => {
    expect(charactersWithDiacritics(['a', 'é', 'ö', 'b'])).toEqual(['é', 'ö']);
  });

  test('getDiacriticVariants groups characters', async () => {
    const variants = await getDiacriticVariants('pl');
    expect(variants.L).toEqual(['L', 'Ł']);
    expect(variants.l).toEqual(['l', 'ł']);
  });
});

