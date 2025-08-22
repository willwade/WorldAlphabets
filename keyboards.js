const fs = require('fs').promises;
const path = require('path');

const LAYOUTS_DIR = path.join(__dirname, 'data', 'layouts');

async function getAvailableLayouts() {
    try {
        const files = await fs.readdir(LAYOUTS_DIR);
        return files
            .filter(file => file.endsWith('.json'))
            .map(file => file.replace('.json', ''));
    } catch (error) {
        // If the directory doesn't exist, return an empty array
        if (error.code === 'ENOENT') {
            return [];
        }
        throw error;
    }
}

async function loadKeyboard(layoutId) {
    const filePath = path.join(LAYOUTS_DIR, `${layoutId}.json`);
    try {
        const data = await fs.readFile(filePath, 'utf-8');
        return JSON.parse(data);
    } catch (error) {
        if (error.code === 'ENOENT') {
            throw new Error(`Keyboard layout '${layoutId}' not found.`);
        }
        throw error;
    }
}

module.exports = {
    getAvailableLayouts,
    loadKeyboard
};
