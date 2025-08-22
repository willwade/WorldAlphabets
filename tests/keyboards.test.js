const { getAvailableLayouts, loadKeyboard } = require('../index');
const fs = require('fs');
const path = require('path');

// Helper function to ensure data is built before running tests
function ensureDataExists() {
    const germanLayoutPath = path.join(__dirname, '..', 'src', 'worldalphabets', 'data', 'layouts', 'de-DE-qwertz.json');
    if (!fs.existsSync(germanLayoutPath)) {
        // A bit of a hack, but it makes the JS tests runnable on their own.
        // This assumes that the python environment is set up and the build script is runnable.
        const { spawnSync } = require('child_process');
        console.log("Running build script to generate test data...");
        const result = spawnSync('uv', ['run', 'wa-build-layouts', '--only', 'de-DE-qwertz'], { stdio: 'inherit' });
        if (result.status !== 0) {
            throw new Error("Failed to build test data.");
        }
    }
    // Also need to copy data for the JS loader
    const dataDir = path.join(__dirname, '..', 'data', 'layouts');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }
    fs.copyFileSync(germanLayoutPath, path.join(dataDir, 'de-DE-qwertz.json'));
}

describe('Keyboard Layouts Node API', () => {
    beforeAll(() => {
        ensureDataExists();
    });

    test('getAvailableLayouts returns an array of strings', async () => {
        const layouts = await getAvailableLayouts();
        expect(Array.isArray(layouts)).toBe(true);
        expect(layouts).toContain('de-DE-qwertz');
    });

    test('loadKeyboard returns a keyboard layout object', async () => {
        const layout = await loadKeyboard('de-DE-qwertz');
        expect(layout).toBeInstanceOf(Object);
        expect(layout.id).toBe('de-DE-qwertz');

        // Check flags
        expect(layout.flags.rightAltIsAltGr).toBe(true);

        // Check a specific key (Q)
        const q_key = layout.keys.find(k => k.vk === "VK_Q");
        expect(q_key).toBeDefined();
        expect(q_key.legends.base).toBe('q');
        expect(q_key.legends.shift).toBe('Q');
        expect(q_key.legends.altgr).toBe('@');

        // Check a dead key
        const dead_key = layout.keys.find(k => k.dead);
        expect(dead_key).toBeDefined();
        expect(layout.dead_keys.length).toBeGreaterThan(0);
    });

    test('loadKeyboard throws for non-existent layout', async () => {
        await expect(loadKeyboard('non-existent-layout')).rejects.toThrow();
    });
});
