const {
    getAvailableInflectionLocales,
    loadInflectionData,
    loadInflectionWords,
    getInflectionSummary,
    lookupWord,
    applyRules,
    clearInflectionCache,
    getFeatures,
    loadTagMap,
    SentenceBuffer,
    createBuffer,
} = require('../index');

describe('Inflection data Node API', () => {
    test('getAvailableInflectionLocales returns an array', async () => {
        const locales = await getAvailableInflectionLocales();
        expect(Array.isArray(locales)).toBe(true);
        expect(locales).toContain('ar');
    });

    test('loadInflectionWords throws for missing locale', async () => {
        await expect(loadInflectionWords('zz')).rejects.toThrow(/not found/);
    });

    test('loadInflectionData falls back to base language', async () => {
        const data = await loadInflectionData('en-TEST');
        expect(data.words._locale).toBe('en');
        expect(data.rules._locale).toBe('en');
    });

    test('getInflectionSummary returns locale metadata', async () => {
        const summary = await getInflectionSummary('en');
        expect(summary.locale).toBe('en');
        expect(summary.wordCount).toBeGreaterThan(0);
        expect(summary.ruleCount).toBeGreaterThan(0);
        expect(summary.testCount).toBeGreaterThan(0);
        expect(summary.posTypes).toContain('verb');
        expect(summary.inflectionKeys.length).toBeGreaterThan(0);
    });

    test('lookupWord returns a result with replacement', async () => {
        clearInflectionCache();
        const result = await lookupWord('en', 'run', 'she');
        expect(result.word).toBe('run');
        expect(result.replacement).toBeTruthy();
    });

    test('applyRules transforms text', async () => {
        clearInflectionCache();
        const result = await applyRules('en', 'she run');
        expect(typeof result).toBe('string');
        expect(result.length).toBeGreaterThan(0);
    });

    test('getFeatures maps German verb tag', async () => {
        const features = await getFeatures('v_ind_pl_1_prs');
        expect(features).toBeTruthy();
        expect(features.pos).toBe('verb');
        expect(features.mood).toBe('indicative');
        expect(features.number).toBe('plural');
        expect(features.person).toBe('1');
        expect(features.tense).toBe('present');
    });

    test('getFeatures maps English plural', async () => {
        const features = await getFeatures('plural');
        expect(features).toBeTruthy();
        expect(features.number).toBe('plural');
    });

    test('getFeatures maps past participle', async () => {
        const features = await getFeatures('past_participle');
        expect(features).toBeTruthy();
        expect(features.verbform).toBe('participle');
        expect(features.tense).toBe('past');
    });

    test('getFeatures returns null for unknown tag', async () => {
        const features = await getFeatures('xyz_unknown_123');
        expect(features).toBeNull();
    });

    test('loadTagMap returns large dict', async () => {
        const tagMap = await loadTagMap();
        expect(typeof tagMap).toBe('object');
        expect(Object.keys(tagMap).length).toBeGreaterThan(7000);
        expect(tagMap['v_ind_pl_1_prs']).toBeTruthy();
        expect(tagMap['v_ind_pl_1_prs'].features).toBeTruthy();
    });

    test('getFeatures maps Arabic dual adjective', async () => {
        const features = await getFeatures('adj_du_fem_def_acc');
        expect(features).toBeTruthy();
        expect(features.pos).toBe('adjective');
        expect(features.number).toBe('dual');
        expect(features.gender).toBe('feminine');
        expect(features.definiteness).toBe('definite');
        expect(features.case).toBe('accusative');
    });

    test('getFeatures maps variant suffix', async () => {
        const features = await getFeatures('adj_acc_fem_sg_2');
        expect(features).toBeTruthy();
        expect(features.pos).toBe('adjective');
        expect(features.variant).toBe('2');
    });
});

describe('SentenceBuffer', () => {
    test('createBuffer returns empty buffer', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        expect(buf.length).toBe(0);
        expect(buf.tokens).toEqual([]);
    });

    test('push and render', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        const snap = buf.push('she');
        expect(buf.length).toBe(1);
        expect(snap.text).toBe('she');
        expect(snap.tokens.length).toBe(1);
        expect(snap.tokens[0].base).toBe('she');
        expect(snap.tokens[0].surface).toBe('she');
    });

    test('push inflects verb after pronoun', async () => {
        clearInflectionCache();
        const buf = await createBuffer('de');
        buf.push('ich');
        const snap = buf.push('haben');
        const verbToken = snap.tokens[snap.tokens.length - 1];
        expect(verbToken.base).toBe('haben');
        expect(verbToken.surface).toBe('habe');
        expect(verbToken.rule_id).toBeTruthy();
    });

    test('update triggers reactive re-inflection', async () => {
        clearInflectionCache();
        const buf = await createBuffer('de');
        buf.push('ich');
        buf.push('haben');
        expect(buf.renderTokens()[1].surface).toBe('habe');
        const snap = buf.update(0, 'er');
        expect(snap.tokens[snap.tokens.length - 1].surface).toBe('hat');
    });

    test('remove token', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('I');
        buf.push('run');
        const snap = buf.remove(0);
        expect(buf.length).toBe(1);
        expect(snap.text).toBe('run');
    });

    test('insert token at position', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        buf.push('run');
        const snap = buf.insert(1, 'not');
        expect(snap.tokens.length).toBe(3);
    });

    test('clear buffer', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        buf.push('run');
        buf.clear();
        expect(buf.length).toBe(0);
        expect(buf.render()).toBe('');
    });

    test('tokenAt and bounds checking', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        buf.push('run');
        expect(buf.tokenAt(0)).toBe('she');
        expect(buf.tokenAt(1)).toBe('run');
        expect(() => buf.tokenAt(5)).toThrow(/out of range/);
    });

    test('renderSnapshot diffs on add', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        const snap = buf.push('she');
        expect(snap.diffs.length).toBe(1);
        expect(snap.diffs[0].kind).toBe('add');
        expect(snap.diffs[0].new_surface).toBe('she');
    });

    test('renderSnapshot diffs on change', async () => {
        clearInflectionCache();
        const buf = await createBuffer('de');
        buf.push('ich');
        buf.push('haben');
        const snap = buf.update(0, 'er');
        const changeDiffs = snap.diffs.filter(d => d.kind === 'change');
        expect(changeDiffs.length).toBeGreaterThan(0);
    });

    test('renderSnapshot diffs on remove', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        buf.push('run');
        const snap = buf.remove(1);
        const removeDiffs = snap.diffs.filter(d => d.kind === 'remove');
        expect(removeDiffs.length).toBeGreaterThan(0);
    });

    test('French join applied via buffer', async () => {
        clearInflectionCache();
        const buf = await createBuffer('fr');
        buf.push('le');
        const snap = buf.push('ami');
        expect(snap.text).toContain("l'ami");
        const joinTokens = snap.tokens.filter(t => t.join_applied);
        expect(joinTokens.length).toBe(1);
    });

    test('German sentence inflection', async () => {
        clearInflectionCache();
        const buf = await createBuffer('de');
        buf.push('ich');
        const snap = buf.push('haben');
        expect(snap.text).toBe('ich habe');
    });

    test('Spanish no inflection still works', async () => {
        clearInflectionCache();
        const buf = await createBuffer('es');
        buf.push('yo');
        const snap = buf.push('hablar');
        expect(snap.text).toBe('yo hablar');
    });

    test('unknown word passes through', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        const snap = buf.push('xyz123');
        expect(snap.text).toBe('xyz123');
        expect(snap.tokens[0].surface).toBe('xyz123');
    });

    test('renderTokens method', async () => {
        clearInflectionCache();
        const buf = await createBuffer('de');
        buf.push('ich');
        buf.push('haben');
        const tokens = buf.renderTokens();
        expect(tokens.length).toBe(2);
        expect(tokens[0].surface).toBe('ich');
        expect(tokens[1].surface).toBe('habe');
    });

    test('multiple pushes accumulate', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        buf.push('run');
        const snap = buf.push('fast');
        expect(snap.tokens.length).toBe(3);
    });

    test('update out of range throws', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        expect(() => buf.update(5, 'I')).toThrow(/out of range/);
    });

    test('remove out of range throws', async () => {
        clearInflectionCache();
        const buf = await createBuffer('en');
        buf.push('she');
        expect(() => buf.remove(5)).toThrow(/out of range/);
    });
});
