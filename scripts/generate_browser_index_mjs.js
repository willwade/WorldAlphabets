#!/usr/bin/env node
/**
 * Generate an ESM mirror of index.mjs at dist/index.browser.esm.mjs
 * with adjusted import paths so it can be executed directly by Node as ESM.
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SRC = path.join(ROOT, 'index.mjs');
const DIST = path.join(ROOT, 'dist');
const OUT = path.join(DIST, 'index.browser.esm.mjs');

async function main() {
  await fsp.mkdir(DIST, { recursive: true });
  let code = await fsp.readFile(SRC, 'utf8');

  // Rewrite import paths for running from dist/
  // Use modern 'with { type: "json" }' instead of deprecated 'assert'
  code = code.replace("import indexDataJson from './data/index.json';", "import indexDataJson from '../data/index.json' with { type: 'json' };");
  code = code.replace("import charIndexJson from './data/char_index.json';", "import charIndexJson from '../data/char_index.json' with { type: 'json' };");

  // Ensure getIndexData is re-exported for the test harness
  code = code.replace(
    "export { tokenizeWords, tokenizeBigrams, tokenizeCharacters, overlap, characterOverlap };",
    "export { getIndexData, tokenizeWords, tokenizeBigrams, tokenizeCharacters, overlap, characterOverlap };"
  );
  code = code.replace("import { ALPHABETS } from './dist/browser-alphabets.mjs';", "import { ALPHABETS } from './browser-alphabets.mjs';");
  code = code.replace("import { LAYOUTS, AVAILABLE_LAYOUTS } from './dist/browser-layouts.mjs';", "import { LAYOUTS, AVAILABLE_LAYOUTS } from './browser-layouts.mjs';");
  code = code.replace("import { FREQ_RANKS } from './dist/browser-freq.mjs';", "import { FREQ_RANKS } from './browser-freq.mjs';");

  await fsp.writeFile(OUT, code);
  console.log(`\u2705 Wrote ${OUT}`);
}

if (require.main === module) {
  main().catch((err) => {
    console.error('\u274c Failed to generate index.browser.esm.mjs', err);
    process.exit(1);
  });
}
