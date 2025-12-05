const {
  getUppercase,
  getLowercase,
  getFrequency,
  getDigits,
  getAvailableCodes,
  loadAlphabet,
  loadFrequencyList,
  getIndexData,
  getLanguage,
  getScripts,
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
    expect(new Set(codes).size).toBe(codes.length);
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

  it('should get digits for a language', async () => {
    const digits = await getDigits('ar');
    expect(Array.isArray(digits)).toBe(true);
    // Arabic has native digits
    expect(digits.length).toBeGreaterThan(0);
  });

  it('should load frequency list for a language', async () => {
    const freqList = await loadFrequencyList('en');
    expect(freqList).toHaveProperty('language', 'en');
    expect(freqList).toHaveProperty('tokens');
    expect(freqList).toHaveProperty('mode');
    expect(Array.isArray(freqList.tokens)).toBe(true);
    expect(freqList.tokens.length).toBeGreaterThan(100);
  });

  it('should throw for invalid frequency list', async () => {
    await expect(loadFrequencyList('invalid-code')).rejects.toThrow();
  });

  it('should get scripts for a language', async () => {
    const scripts = await getScripts('zh');
    expect(Array.isArray(scripts)).toBe(true);
    // Chinese should have multiple scripts (Hans, Hant)
    expect(scripts.length).toBeGreaterThan(0);
  });

  it('should return empty array for unknown language scripts', async () => {
    const scripts = await getScripts('nonexistent');
    expect(scripts).toEqual([]);
  });
});
