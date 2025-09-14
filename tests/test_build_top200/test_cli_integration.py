from pathlib import Path
import json
import pytest

from scripts.build_top200.__main__ import main


def test_cli_build(tmp_path: Path) -> None:
    # Create sample data directory and files for testing
    sample_data_dir = Path("scripts/build_top200/sample_data")
    sample_data_dir.mkdir(exist_ok=True)

    # Create minimal sample data files for English
    (sample_data_dir / "leipzig_en.txt").write_text("1\tthe\t1000\n2\tand\t800\n3\tof\t600\n4\ta\t500\n5\tto\t400\n", encoding="utf-8")
    (sample_data_dir / "hermit_en.txt").write_text("the 1000\nand 800\nof 600\na 500\nto 400\n", encoding="utf-8")
    (sample_data_dir / "tatoeba_en.txt").write_text("The quick brown fox\nAnd the lazy dog\nOf all the things\n", encoding="utf-8")
    (sample_data_dir / "stopwords_en.txt").write_text("the\nand\nof\na\nto\n", encoding="utf-8")

    # Create minimal sample data files for Japanese
    (sample_data_dir / "tatoeba_ja.txt").write_text("これはテストです\nこんにちは世界\nありがとうございます\n", encoding="utf-8")

    try:
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
    finally:
        # Clean up sample data files
        for file in sample_data_dir.glob("*.txt"):
            file.unlink(missing_ok=True)
    en_lines = (freq_dir / "en.txt").read_text(encoding="utf-8").splitlines()
    assert len(en_lines) == 5
    ja_lines = (freq_dir / "ja.txt").read_text(encoding="utf-8").splitlines()
    assert ja_lines[0] == "# type=bigram"
    assert len(ja_lines) == 6  # header + 5 tokens
    report = json.loads((freq_dir / "BUILD_REPORT.json").read_text(encoding="utf-8"))
    assert report["languages"]["en"]["token_count"] == 5
    assert "## en — English" in (freq_dir / "SOURCES.md").read_text(encoding="utf-8")
