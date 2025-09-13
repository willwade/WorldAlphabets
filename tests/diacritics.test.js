const {
  stripDiacritics,
  hasDiacritics,
  charactersWithDiacritics,
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
});

