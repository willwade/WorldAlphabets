/**
 * Print digits for a language code.
 */
const { getDigits } = require('../../index');

async function main() {
  const code = process.argv[2] || 'en';
  const script = process.argv[3];
  
  try {
    const digits = await getDigits(code, script);
    const label = script ? `${code}-${script}` : code;
    
    if (digits.length > 0) {
      console.log(`${label} digits: ${digits.join(' ')}`);
    } else {
      console.log(`${label}: No digits available`);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
