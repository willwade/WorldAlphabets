export interface Alphabet {
  alphabetical: string[];
  uppercase: string[];
  lowercase: string[];
  frequency: Record<string, number>;
}

export function loadAlphabet(code: string): Promise<Alphabet>;
export function getUppercase(code: string): Promise<string[]>;
export function getLowercase(code: string): Promise<string[]>;
export function getFrequency(code: string): Promise<Record<string, number>>;
export function getAvailableCodes(): Promise<string[]>;

// Re-export all keyboard types and functions
export * from './keyboards';
