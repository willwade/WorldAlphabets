// Pick a random letter from a language's alphabet.
const { getLowercase, getUppercase } = require('../..');

async function main() {
  const code = process.argv[2] || 'en';
  const script = process.argv[3];
  let letters = await getLowercase(code, script);
  if (!letters.length) {
    letters = await getUppercase(code, script);
  }
  const pick = letters[Math.floor(Math.random() * letters.length)];
  console.log(pick);
}

main();
