const {
    getAvailableLayouts,
    loadKeyboard,
    getUnicode,
    extractLayers,
    generateCHeader,
    findLayoutsByKeycode,
} = require('../index');
const fs = require('fs');
const path = require('path');

describe('Keyboard Layouts Node API', () => {
    test('getAvailableLayouts returns an array of strings', async () => {
        const layouts = await getAvailableLayouts();
        expect(Array.isArray(layouts)).toBe(true);
        expect(layouts).toContain('de-german');
    });

    test('loadKeyboard returns a keyboard layout object', async () => {
        const layout = await loadKeyboard('de-german');
        expect(layout).toBeInstanceOf(Object);
        expect(layout.id).toBe('de-german');

        expect(layout.flags.rightAltIsAltGr).toBe(true);

        const q_key = layout.keys.find(k => k.vk === "VK_Q");
        expect(q_key).toBeDefined();
        expect(q_key.legends.base).toBe('q');
        expect(q_key.legends.shift).toBe('Q');

        const dead_key = layout.keys.find(k => k.dead);
        expect(dead_key).toBeDefined();
        expect(layout.dead_keys.length).toBeGreaterThan(0);
    });

    test('getUnicode returns correct code point', async () => {
        const layout = await loadKeyboard('de-german');
        const e_key = layout.keys.find(k => k.vk === "VK_E");
        expect(e_key).toBeDefined();
        expect(getUnicode(e_key, 'base')).toBe('U+0065');
    });

    test('loadKeyboard throws for non-existent layout', async () => {
        await expect(loadKeyboard('non-existent-layout')).rejects.toThrow();
    });

    test('extractLayers captures shift+AltGr legends', async () => {
        const layout = await loadKeyboard('fr-french-standard-azerty');
        const layers = extractLayers(layout, ['shift_altgr']);
        expect(layers.shift_altgr).toBeDefined();
        expect(layers.shift_altgr.Digit1).toBe('À');
    });

    test('generateCHeader outputs HID-based mappings', async () => {
        const header = await generateCHeader('fr-french-standard-azerty', {
            layers: ['base', 'shift', 'altgr', 'shift_altgr'],
            guard: false,
        });
        expect(header).toContain('keyboard_layout_t');
        expect(header).toContain('{ 0x04, "q" }');
        expect(header).toContain('{ 0x14, "a" }');
        expect(header).toContain('.layer_count = 4u');
        expect(header).toContain('.display_name = "French (Standard, AZERTY)"');
    });

    test('findLayoutsByKeycode finds IntlBackslash base legends', async () => {
        const matches = await findLayoutsByKeycode('IntlBackslash', 'base');
        const ids = matches.map(m => m.id);
        expect(ids).toContain('fr-french-standard-azerty');
        expect(matches.find(m => m.id === 'fr-french-standard-azerty').legend).toBe('<');
    });
});
