const {
  getUppercase,
  getLowercase,
  getFrequency,
  getAvailableCodes,
  loadAlphabet,
  getIndexData,
  getLanguage,
} = require('../index');

describe('worldalphabets', () => {
  it('should get uppercase letters for "en"', async () => {
    const uppercase = await getUppercase('en');
    expect(uppercase).toEqual(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']);
  });

  it('should get lowercase letters for "en"', async () => {
    const lowercase = await getLowercase('en');
    expect(lowercase).toEqual(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']);
  });

  it('should get letter frequency for "en"', async () => {
    const frequency = await getFrequency('en');
    expect(frequency['a']).toBeCloseTo(0.0868, 4);
    expect(frequency['z']).toBeCloseTo(0.0013, 4);
  });

  it('should get available codes', async () => {
    const codes = await getAvailableCodes();
    expect(Array.isArray(codes)).toBe(true);
    expect(codes.length).toBeGreaterThan(0);
    expect(codes).toContain('en');
    expect(codes).toContain('fr');
  });

  it('should load the whole alphabet for "en"', async () => {
    const alphabet = await loadAlphabet('en');
    expect(alphabet).toHaveProperty('uppercase');
    expect(alphabet).toHaveProperty('lowercase');
    expect(alphabet).toHaveProperty('frequency');
    expect(alphabet).toHaveProperty('alphabetical');
  });

  it('should throw an error for an invalid code', async () => {
    await expect(loadAlphabet('invalid-code')).rejects.toThrow('Alphabet data for code "invalid-code" not found.');
  });

  it('should get the index data', async () => {
    const indexData = await getIndexData();
    expect(Array.isArray(indexData)).toBe(true);
    expect(indexData.length).toBeGreaterThan(0);
  });

  it('should load alphabet for default script', async () => {
    const alphabet = await getLanguage('en');
    expect(alphabet).not.toBeNull();
    expect(alphabet.uppercase).toBeDefined();
  });

  it('should load alphabet for a specified script', async () => {
    const alphabet = await getLanguage('mr', 'Latn');
    expect(alphabet).not.toBeNull();
    expect(alphabet.script).toBe('Latn');
  });

  it('should load alphabet file by script', async () => {
    const alphabet = await loadAlphabet('mr', 'Latn');
    expect(alphabet.script).toBe('Latn');
    expect(alphabet.alphabetical).toContain('A');
  });

  it('should return null for an invalid language code', async () => {
    const langInfo = await getLanguage('invalid-code');
    expect(langInfo).toBeNull();
  });
});
