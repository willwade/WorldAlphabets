const fs = require('fs').promises;
const path = require('path');

const LAYOUTS_DIR = path.join(__dirname, 'data', 'layouts');

const DEFAULT_LAYERS = ['base', 'shift', 'caps', 'altgr', 'shift_altgr', 'ctrl', 'alt'];

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

function getUnicode(keyEntry, layer) {
    if (!keyEntry || !keyEntry.legends) {
        return null;
    }
    const char = keyEntry.legends[layer];
    if (char) {
        return `U+${char.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}`;
    }
    return null;
}

function extractLayers(layout, layers = DEFAULT_LAYERS) {
    if (!layout || !Array.isArray(layout.keys)) {
        return {};
    }

    const result = {};
    for (const layer of layers) {
        const layerEntries = {};
        for (const key of layout.keys) {
            if (!key || !key.legends) continue;
            const value = key.legends[layer];
            if (!value) continue;
            const pos = key.pos || key.vk || key.sc;
            if (pos) {
                layerEntries[String(pos)] = value;
            }
        }
        if (Object.keys(layerEntries).length > 0) {
            result[layer] = layerEntries;
        }
    }

    return result;
}

module.exports = {
    getAvailableLayouts,
    loadKeyboard,
    getUnicode,
    extractLayers,
    DEFAULT_LAYERS,
};
