"""Count languages by script type using the index."""
from __future__ import annotations

from collections import Counter

from worldalphabets import get_index_data


def main() -> None:
    index = get_index_data()
    counts = Counter(item["script-type"] for item in index)
    for script, count in counts.most_common():
        print(f"{script}: {count}")


if __name__ == "__main__":
    main()
