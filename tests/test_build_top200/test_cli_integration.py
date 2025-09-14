from pathlib import Path
import json

from scripts.build_top200.__main__ import main


def test_cli_build(tmp_path: Path) -> None:
    freq_dir = tmp_path / "out"
    settings = tmp_path / "settings.yaml"
    settings.write_text("max_tokens: 5\nallowlist:\n  default: ['a','i']\n", encoding="utf-8")
    main([
        "--langs",
        "en,ja",
        "--freq-dir",
        str(freq_dir),
        "--langmap",
        "scripts/build_top200/langmap.yaml",
        "--settings",
        str(settings),
    ])
    en_lines = (freq_dir / "en.txt").read_text(encoding="utf-8").splitlines()
    assert len(en_lines) == 5
    ja_lines = (freq_dir / "ja.txt").read_text(encoding="utf-8").splitlines()
    assert ja_lines[0] == "# type=bigram"
    assert len(ja_lines) == 6  # header + 5 tokens
    report = json.loads((freq_dir / "BUILD_REPORT.json").read_text(encoding="utf-8"))
    assert report["languages"]["en"]["token_count"] == 5
    assert "## en — English" in (freq_dir / "SOURCES.md").read_text(encoding="utf-8")
