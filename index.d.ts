export interface Alphabet {
  alphabetical: string[];
  uppercase: string[];
  lowercase: string[];
  frequency: Record<string, number>;
  digits?: string[];
}

export interface FrequencyList {
  language: string;
  tokens: string[];
  mode: 'word' | 'bigram';
}

export type InflectionWordEntry = Record<string, unknown> & {
  types: string[];
  base?: string;
  priority?: number;
  antonyms?: string[];
  examples?: unknown[];
  inflections: Record<string, unknown>;
};

export type InflectionWords = Record<string, unknown | InflectionWordEntry> & {
  _type: 'words';
  _locale: string;
  _version: string;
};

export type InflectionRules = Record<string, unknown> & {
  _type: 'rules';
  _locale: string;
  _version: string;
  rules: unknown[];
  tests?: unknown[];
  substitutions?: Record<string, unknown>;
  inflection_locations?: Record<string, unknown>;
};

export interface InflectionData {
  words: InflectionWords;
  rules: InflectionRules;
}

export interface LocaleSummary {
  locale: string;
  wordCount: number;
  ruleCount: number;
  testCount: number;
  posTypes: string[];
  inflectionKeys: string[];
}

export interface LookupResult {
  word: string;
  replacement: string | null;
  rule_id: string | null;
  rule_type: string | null;
  inflection: string | null;
  condense_items: number[] | null;
}

export function loadAlphabet(code: string, script?: string): Promise<Alphabet>;
export function getUppercase(code: string, script?: string): Promise<string[]>;
export function getLowercase(code: string, script?: string): Promise<string[]>;
export function getFrequency(code: string, script?: string): Promise<Record<string, number>>;
export function getDigits(code: string, script?: string): Promise<string[]>;
export function getAvailableCodes(): Promise<string[]>;
export function loadFrequencyList(code: string): Promise<FrequencyList>;
export function getAvailableInflectionLocales(): Promise<string[]>;
export function loadInflectionWords(locale: string): Promise<InflectionWords>;
export function loadInflectionRules(locale: string): Promise<InflectionRules>;
export function loadInflectionData(locale: string): Promise<InflectionData>;
export function getWordForms(
  locale: string,
  word: string
): Promise<InflectionWordEntry | null>;
export function inflectWord(
  locale: string,
  word: string,
  inflection: string
): Promise<string | null>;
export function getInflectionSummary(locale: string): Promise<LocaleSummary>;
export function lookupWord(
  locale: string,
  word: string,
  priorWords?: string
): Promise<LookupResult>;
export function applyRules(locale: string, text: string): Promise<string>;
export function clearInflectionCache(): void;
export interface IndexEntry {
  language: string;
  'language-name': string;
  'frequency-avail': boolean;
  'script-type': string;
  direction: string;
  scripts?: string[];
  keyboards?: string[];
}
export function getIndexData(): Promise<IndexEntry[]>;
export function getLanguage(langCode: string, script?: string): Promise<Alphabet | null>;
export function getScripts(langCode: string): Promise<string[]>;

export function stripDiacritics(text: string): string;
export function hasDiacritics(char: string): boolean;
export function charactersWithDiacritics(chars: string[]): string[];
export function getDiacriticVariants(
  code: string,
  script?: string
): Promise<Record<string, string[]>>;
// Language detection
export function detectLanguages(
  text: string,
  candidateLangs: string[] | null,
  priors?: Record<string, number>,
  topk?: number
): Array<[string, number]>;

// Script utilities (ESM)
export function detectDominantScript(text: string): string | null;

// Re-export all keyboard types and functions
export * from './keyboards';
