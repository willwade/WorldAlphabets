// Print uppercase and lowercase letters for a language code.
const { getUppercase, getLowercase } = require('../..');

async function main() {
  const code = process.argv[2] || 'en';
  const upper = await getUppercase(code);
  const lower = await getLowercase(code);
  console.log(`${code} uppercase: ${upper.join(' ')}`);
  console.log(`${code} lowercase: ${lower.join(' ')}`);
}

main();
