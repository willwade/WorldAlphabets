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

def layout_to_markdown(layout_id: str, layer: str = "base") -> str:
    """Return the layout's ``layer`` as a Markdown table."""
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

    header = [legend(p) for p in LAYOUT_ROWS[0]]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + " --- |" * len(header),
    ]
    for row in LAYOUT_ROWS[1:]:
        line = [legend(p) for p in row]
        lines.append("| " + " | ".join(line) + " |")
    return "\n".join(lines)

if __name__ == "__main__":
    print(layout_to_markdown("en-united-kingdom"))
