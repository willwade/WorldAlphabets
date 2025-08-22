"""Print uppercase and lowercase letters for a language code."""
from __future__ import annotations

import sys

from worldalphabets import load_alphabet


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "en"
    alphabet = load_alphabet(code)
    print(f"{code} uppercase: {' '.join(alphabet.uppercase)}")
    print(f"{code} lowercase: {' '.join(alphabet.lowercase)}")


if __name__ == "__main__":
    main()
