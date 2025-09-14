import fs from 'fs';
import path from 'path';

export const PRIOR_WEIGHT = Number(process.env.WA_FREQ_PRIOR_WEIGHT ?? 0.65);
export const FREQ_WEIGHT = Number(process.env.WA_FREQ_OVERLAP_WEIGHT ?? 0.35);

const DEFAULT_FREQ_DIR =
  process.env.WORLDALPHABETS_FREQ_DIR ??
  path.resolve(__dirname, '..', '..', '..', 'data', 'freq', 'top200');

type RankData = { mode: 'word' | 'bigram'; ranks: Map<string, number> };
const cache = new Map<string, RankData>();

function loadRankData(lang: string, dir: string): RankData {
  const key = `${dir}:${lang}`;
  if (cache.has(key)) return cache.get(key)!;
  try {
    const lines = fs
      .readFileSync(path.join(dir, `${lang}.txt`), 'utf8')
      .split(/\r?\n/)
      .filter(Boolean);
    let mode: 'word' | 'bigram' = 'word';
    if (lines[0]?.startsWith('#')) {
      const header = lines.shift()!;
      if (header.includes('bigram')) mode = 'bigram';
    }
    const ranks = new Map<string, number>();
    lines.forEach((tok, i) => {
      if (!ranks.has(tok)) ranks.set(tok, i + 1);
    });
    const data = { mode, ranks };
    cache.set(key, data);
    return data;
  } catch {
    const data = { mode: 'word' as const, ranks: new Map() };
    cache.set(key, data);
    return data;
  }
}

function tokenizeWords(text: string): Set<string> {
  return new Set(
    (text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) ?? [])
  );
}

function tokenizeBigrams(text: string): Set<string> {
  const letters = Array.from(text.normalize('NFKC').toLowerCase()).filter((ch) =>
    /\p{L}/u.test(ch)
  );
  const bigrams = new Set<string>();
  for (let i = 0; i < letters.length - 1; i++) {
    bigrams.add(letters[i] + letters[i + 1]);
  }
  return bigrams;
}

function overlap(tokens: Iterable<string>, ranks: Map<string, number>): number {
  let score = 0;
  for (const t of tokens) {
    const r = ranks.get(t);
    if (r) score += 1 / Math.log2(r + 1.5);
  }
  return score;
}

export function detectLanguages(
  text: string,
  candidateLangs: string[],
  priors: Record<string, number> = {},
  topk = 3
): Array<[string, number]> {
  const dir = process.env.WORLDALPHABETS_FREQ_DIR ?? DEFAULT_FREQ_DIR;
  const wordTokens = tokenizeWords(text);
  const bigramTokens = tokenizeBigrams(text);
  const results: Array<[string, number]> = [];

  for (const lang of candidateLangs) {
    const data = loadRankData(lang, dir);
    const tokens = data.mode === 'bigram' ? bigramTokens : wordTokens;
    let ov = 0;
    if (data.ranks.size > 0 && tokens.size > 0) {
      ov = overlap(tokens, data.ranks);
      ov /= Math.sqrt(tokens.size + 3);
    }
    const score = PRIOR_WEIGHT * (priors[lang] ?? 0) + FREQ_WEIGHT * ov;
    if (score > 0.05) results.push([lang, score]);
  }

  results.sort((a, b) => b[1] - a[1]);
  return results.slice(0, topk);
}
