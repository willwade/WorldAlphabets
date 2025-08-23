"""Print the base layer of a keyboard layout as a Markdown table."""
from worldalphabets import load_keyboard

LAYOUT_ROWS = [
    [
        "Backquote",
        "Digit1",
        "Digit2",
        "Digit3",
        "Digit4",
        "Digit5",
        "Digit6",
        "Digit7",
        "Digit8",
        "Digit9",
        "Digit0",
        "Minus",
        "Equal",
    ],
    [
        "KeyQ",
        "KeyW",
        "KeyE",
        "KeyR",
        "KeyT",
        "KeyY",
        "KeyU",
        "KeyI",
        "KeyO",
        "KeyP",
        "BracketLeft",
        "BracketRight",
    ],
    [
        "KeyA",
        "KeyS",
        "KeyD",
        "KeyF",
        "KeyG",
        "KeyH",
        "KeyJ",
        "KeyK",
        "KeyL",
        "Semicolon",
        "Quote",
        "Backslash",
    ],
    [
        "KeyZ",
        "KeyX",
        "KeyC",
        "KeyV",
        "KeyB",
        "KeyN",
        "KeyM",
        "Comma",
        "Period",
        "Slash",
    ],
    ["Space"],
]

ROW_OFFSETS = [0, 1, 1, 2, 5]


def layout_to_markdown(
    layout_id: str, layer: str = "base", *, offset: bool = False
) -> str:
    """Return the layout's ``layer`` as a Markdown table.

    If ``offset`` is true, rows are indented to roughly mirror a physical keyboard.
    """
    layout = load_keyboard(layout_id)
    key_by_pos = {k.pos: k for k in layout.keys}

    def legend(pos: str) -> str:
        key = key_by_pos.get(pos)
        if not key:
            return ""
        value = getattr(key.legends, layer)
        if value == " ":
            return "␠"
        return value or ""

    offsets = ROW_OFFSETS if offset else [0] * len(LAYOUT_ROWS)
    cols = max(len(row) + off for row, off in zip(LAYOUT_ROWS, offsets))

    header = ["" for _ in range(offsets[0])]
    header += [legend(p) for p in LAYOUT_ROWS[0]]
    header += ["" for _ in range(cols - len(header))]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + " --- |" * cols,
    ]
    for row, off in zip(LAYOUT_ROWS[1:], offsets[1:]):
        line = ["" for _ in range(off)]
        line += [legend(p) for p in row]
        line += ["" for _ in range(cols - len(line))]
        lines.append("| " + " | ".join(line) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout_id", nargs="?", default="en-united-kingdom")
    parser.add_argument(
        "--offset", action="store_true", help="offset rows to mimic a keyboard"
    )
    args = parser.parse_args()
    print(layout_to_markdown(args.layout_id, offset=args.offset))
