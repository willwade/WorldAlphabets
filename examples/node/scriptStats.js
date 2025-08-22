// Count languages by script type.
const { getIndexData } = require('../..');

async function main() {
  const index = await getIndexData();
  const counts = index.reduce((acc, item) => {
    const type = item['script-type'];
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});
  for (const [type, count] of Object.entries(counts)) {
    console.log(`${type}: ${count}`);
  }
}

main();
