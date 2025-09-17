#!/usr/bin/env node
/*
 Verify browser ESM build using embedded data.
 - Imports ./index.esm.js directly
 - Iterates all languages with hello_how_are_you
 - Runs detectLanguages(text) and checks top-1 equals language code
 Exits non-zero on any mismatch.
*/

import * as esm from '../dist/index.browser.esm.mjs';
import { FREQ_RANKS } from '../dist/browser-freq.mjs';

async function main() {
  const { getAvailableCodes, getScripts, getLanguage, detectLanguages } = esm;
  const failures = [];
  let checked = 0;

  // Some languages share identical greeting phrases; allow acceptable alternatives
  const acceptable = {
    sr: ['sr', 'mk'],
    mk: ['mk', 'sr'],
    ss: ['ss', 'zu'],
    zu: ['zu', 'ss'],
  };

  // Restrict strict assertions to languages with embedded frequency data
  const langsWithFreq = Object.keys(FREQ_RANKS).sort();
  for (const lang of langsWithFreq) {
    const scripts = await getScripts(lang);
    for (const script of scripts) {
      const data = await getLanguage(lang, script);
      if (!data || !data.hello_how_are_you) continue;

      const text = data.hello_how_are_you;
      const res = await detectLanguages(text, null, {}, 1);
      const top = Array.isArray(res) && res.length > 0 ? res[0][0] : null;
      checked++;
      const allowed = acceptable[lang] || [lang];
      if (!allowed.includes(top)) {
        failures.push({ lang, script, detected: top, text });
      }
    }
  }

  if (failures.length) {
    console.error(`\n❌ ESM detection mismatches: ${failures.length} of ${checked} checked`);
    console.error(failures.slice(0, 20));
    process.exit(1);
  } else {
    console.log(`\n✅ ESM detection passed for ${checked} languages with samples.`);
  }
}

main().catch((e) => {
  console.error('Error running verify_browser_esmbuild:', e);
  process.exit(1);
});

