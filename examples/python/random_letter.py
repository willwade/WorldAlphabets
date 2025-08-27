"""Pick a random letter from a language's alphabet."""
from __future__ import annotations

import random
import sys

from worldalphabets import load_alphabet


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "en"
    script = sys.argv[2] if len(sys.argv) > 2 else None
    alphabet = load_alphabet(code, script=script)
    letters = alphabet.lowercase or alphabet.alphabetical
    print(random.choice(letters))


if __name__ == "__main__":
    main()
