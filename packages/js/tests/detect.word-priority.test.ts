/**
 * Test that word-based detection is prioritized over character-based fallback.
 */

import { detectLanguages } from '../src/detect';
import path from 'path';

// Set the frequency directory to the project root data directory for testing
const PROJECT_ROOT = path.resolve(__dirname, '../../..');
process.env.WORLDALPHABETS_FREQ_DIR = path.join(PROJECT_ROOT, 'data', 'freq', 'top1000');

describe('Word-based detection priority', () => {
  test('Shona word detection should rank #1', () => {
    // "vanoti vanodaro" contains Shona words at ranks 18 and 21
    const text = 'vanoti vanodaro';
    
    // Use uniform priors to test pure word-based detection
    const allLangs = ['sn', 'sw', 'jbo', 'en', 'sl', 'pt', 'es', 'fr'];
    const uniformPriors: Record<string, number> = {};
    allLangs.forEach(lang => {
      uniformPriors[lang] = 1.0 / allLangs.length;
    });
    
    const results = detectLanguages(text, allLangs, uniformPriors, 10);
    const detectedLangs = results.map(r => r[0]);
    
    expect(detectedLangs[0]).toBe('sn');
  });

  test('Spanish word detection should rank in top 3', () => {
    // "gracias por todo" contains common Spanish words
    const text = 'gracias por todo';
    
    const allLangs = ['es', 'pt', 'en', 'fr', 'it', 'ca', 'gl'];
    const uniformPriors: Record<string, number> = {};
    allLangs.forEach(lang => {
      uniformPriors[lang] = 1.0 / allLangs.length;
    });
    
    const results = detectLanguages(text, allLangs, uniformPriors, 10);
    const detectedLangs = results.map(r => r[0]);
    const esPos = detectedLangs.indexOf('es');
    
    expect(esPos).toBeGreaterThanOrEqual(0);
    expect(esPos).toBeLessThan(3);
  });

  test('French word detection should rank in top 3', () => {
    // "je ne peux pas venir" contains common French words
    const text = 'je ne peux pas venir';
    
    const allLangs = ['fr', 'en', 'es', 'pt', 'it', 'ro', 'ca'];
    const uniformPriors: Record<string, number> = {};
    allLangs.forEach(lang => {
      uniformPriors[lang] = 1.0 / allLangs.length;
    });
    
    const results = detectLanguages(text, allLangs, uniformPriors, 10);
    const detectedLangs = results.map(r => r[0]);
    const frPos = detectedLangs.indexOf('fr');
    
    expect(frPos).toBeGreaterThanOrEqual(0);
    expect(frPos).toBeLessThan(3);
  });

  test('Word-based detection should beat character-based fallback', () => {
    // Regression test: Shona has word matches, Swahili doesn't
    const text = 'vanoti vanodaro';
    
    const allLangs = ['sn', 'sw', 'jbo', 'en'];
    const uniformPriors: Record<string, number> = {};
    allLangs.forEach(lang => {
      uniformPriors[lang] = 1.0 / allLangs.length;
    });
    
    const results = detectLanguages(text, allLangs, uniformPriors, 10);
    const detectedLangs = results.map(r => r[0]);
    
    const snPos = detectedLangs.indexOf('sn');
    const swPos = detectedLangs.indexOf('sw');
    
    expect(snPos).toBeGreaterThanOrEqual(0);
    expect(swPos).toBeGreaterThanOrEqual(0);
    expect(snPos).toBeLessThan(swPos);
  });
});

