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
export function getIndexData(): Promise<object[]>;
export function getLanguage(langCode: string, script?: string): Promise<Alphabet | null>;

// Re-export all keyboard types and functions
export * from './keyboards';
