import { detectLanguages } from '../src/detect';
import path from 'path';
import fs from 'fs';
import os from 'os';

describe('detectLanguages with frequency data', () => {
  test('gracias por todo -> es > pt', () => {
    const res = detectLanguages('gracias por todo', ['es', 'pt'], {
      es: 0.6,
      pt: 0.4,
    });
    expect(res[0][0]).toBe('es');
    expect(res[1][0]).toBe('pt');
  });

  test('je ne peux pas venir -> fr > en', () => {
    const res = detectLanguages('je ne peux pas venir', ['fr', 'en'], {
      fr: 0.6,
      en: 0.4,
    });
    expect(res[0][0]).toBe('fr');
    expect(res[1][0]).toBe('en');
  });

  test('今日は忙しい -> ja > zh', () => {
    const res = detectLanguages('今日は忙しい', ['ja', 'zh'], {
      ja: 0.6,
      zh: 0.4,
    });
    expect(res[0][0]).toBe('ja');
    expect(res[1][0]).toBe('zh');
  });

  test('o dia está lindo -> pt > es', () => {
    const res = detectLanguages('o dia está lindo', ['pt', 'es'], {
      pt: 0.6,
      es: 0.4,
    });
    expect(res[0][0]).toBe('pt');
    expect(res[1][0]).toBe('es');
  });

  test('empty string returns empty', () => {
    expect(detectLanguages('', ['en', 'es'])).toEqual([]);
  });

  test('missing file falls back to prior', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'freq'));
    process.env.WORLDALPHABETS_FREQ_DIR = dir;
    const res = detectLanguages('hello', ['en'], { en: 1 });
    delete process.env.WORLDALPHABETS_FREQ_DIR;
    expect(res[0][0]).toBe('en');
  });

  test('env override', () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'freq'));
    fs.writeFileSync(path.join(dir, 'es.txt'), 'override');
    process.env.WORLDALPHABETS_FREQ_DIR = dir;
    const res = detectLanguages('override', ['es', 'en']);
    delete process.env.WORLDALPHABETS_FREQ_DIR;
    expect(res[0][0]).toBe('es');
  });
});
