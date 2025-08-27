// Print uppercase and lowercase letters for a language code and script.
const { getUppercase, getLowercase } = require('../..');

async function main() {
  const code = process.argv[2] || 'en';
  const script = process.argv[3];
  const upper = await getUppercase(code, script);
  const lower = await getLowercase(code, script);
  const label = script ? `${code}-${script}` : code;
  console.log(`${label} uppercase: ${upper.join(' ')}`);
  console.log(`${label} lowercase: ${lower.join(' ')}`);
}

main();
