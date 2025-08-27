"""List available scripts for a language code."""
from __future__ import annotations

import sys

from worldalphabets import get_scripts


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "en"
    scripts = get_scripts(code)
    print(f"{code} scripts: {', '.join(scripts)}")


if __name__ == "__main__":
    main()
