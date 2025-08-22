// Pick a random letter from a language's alphabet.
const { getLowercase, getUppercase } = require('../..');

async function main() {
  const code = process.argv[2] || 'en';
  let letters = await getLowercase(code);
  if (!letters.length) {
    letters = await getUppercase(code);
  }
  const pick = letters[Math.floor(Math.random() * letters.length)];
  console.log(pick);
}

main();
