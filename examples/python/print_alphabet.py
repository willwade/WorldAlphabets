"""Print uppercase and lowercase letters for a language code."""
from __future__ import annotations

import sys

from worldalphabets import load_alphabet


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "en"
    script = sys.argv[2] if len(sys.argv) > 2 else None
    alphabet = load_alphabet(code, script=script)
    label = f"{code}-{script}" if script else code
    print(f"{label} uppercase: {' '.join(alphabet.uppercase)}")
    print(f"{label} lowercase: {' '.join(alphabet.lowercase)}")


if __name__ == "__main__":
    main()
