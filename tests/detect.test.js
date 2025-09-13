const { detectLanguages } = require('../index');

describe('language detection', () => {
  test('detectLanguages finds candidates', async () => {
    const langs = await detectLanguages('Żółć');
    expect(langs).toContain('pl');
  });
});
