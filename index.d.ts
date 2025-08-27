export interface Alphabet {
  alphabetical: string[];
  uppercase: string[];
  lowercase: string[];
  frequency: Record<string, number>;
}

export function loadAlphabet(code: string, script?: string): Promise<Alphabet>;
export function getUppercase(code: string, script?: string): Promise<string[]>;
export function getLowercase(code: string, script?: string): Promise<string[]>;
export function getFrequency(code: string, script?: string): Promise<Record<string, number>>;
export function getAvailableCodes(): Promise<string[]>;
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

// Re-export all keyboard types and functions
export * from './keyboards';
