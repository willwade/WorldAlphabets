from scripts.build_top200.licenses import render_sources_md


def test_render_sources_md_block() -> None:
    report = {"xx": {"name": "X", "source_counts": {"leipzig": 2}}}
    md = render_sources_md(report)
    assert "## xx — X" in md
    assert "leipzig: 2 entries" in md
