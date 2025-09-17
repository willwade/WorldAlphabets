import path from 'path';
import { fileURLToPath } from 'url';

// Import the browser ESM entry directly
import * as esm from '../index.esm.js';

jest.setTimeout(30000);

describe('Browser ESM detection with embedded data', () => {
  test('detectLanguages matches language for hello_how_are_you across all languages with samples', async () => {
    const { getIndexData, getLanguage, detectLanguages } = esm;

    const index = await getIndexData();
    const failures = [];

    // Some languages share identical greeting phrases; allow acceptable alternatives
    const acceptable = {
      sr: ['sr', 'mk'],
      mk: ['mk', 'sr'],
      ss: ['ss', 'zu'],
      zu: ['zu', 'ss'],
    };

    for (const item of index) {
      const lang = item.language;
      const script = item.script;
      const data = await getLanguage(lang, script);
      if (!data || !data.hello_how_are_you) continue; // skip if no sample

      const text = data.hello_how_are_you;
      const res = await detectLanguages(text, null, {}, 1);
      const top = Array.isArray(res) && res.length > 0 ? res[0][0] : null;

      const allowed = acceptable[lang] || [lang];
      if (!allowed.includes(top)) {
        failures.push({ lang, script, detected: top, text });
      }
    }

    if (failures.length) {
      console.error('Detection mismatches (first 10 shown):', failures.slice(0, 10));
    }

    expect(failures).toEqual([]);
  });
});

