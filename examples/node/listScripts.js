// List available scripts for a language code.
const { getScripts } = require('../..');

async function main() {
  const code = process.argv[2] || 'en';
  const scripts = await getScripts(code);
  console.log(`${code} scripts: ${scripts.join(', ')}`);
}

main();
