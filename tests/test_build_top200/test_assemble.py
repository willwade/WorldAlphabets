from scripts.build_top200.assemble import merge_sources


def test_merge_sources_dedup_and_limit() -> None:
    sources = [
        ("s1", ["a", "b", "c"]),
        ("s2", ["b", "d", "e"]),
        ("s3", ["f"]),
    ]
    merged, counts = merge_sources(sources, limit=5)
    assert merged == ["a", "b", "c", "d", "e"]
    assert counts == {"s1": 3, "s2": 2}
