const fs = require('fs/promises');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'alphabets');

async function loadAlphabet(code) {
  const filePath = path.join(DATA_DIR, `${code}.json`);
  const content = await fs.readFile(filePath, 'utf8');
  return JSON.parse(content);
}

module.exports = { loadAlphabet };
