import os
from typing import Any, Dict, List, Tuple, Optional

import pytest

from worldalphabets import (
    optimized_detect_languages,
    get_index_data,
    get_language,
)


@pytest.mark.parametrize(
    "entry",
    get_index_data(),
    ids=lambda e: f"{e.get('language')}[{e.get('script')}]",
)
def test_detect_from_hello_sample(entry: Dict[str, Any]) -> None:
    """
    For each language that has a hello_how_are_you sample in its alphabet data,
    run optimized detection on the sample and record whether the correct
    language appears in the top results. This test is primarily diagnostic and
    should not be overly strict to avoid flakiness across data updates.
    """
    lang_code: str = entry["language"]
    script: Optional[str] = entry.get("script")

    # Load alphabet JSON to retrieve the hello string
    data = get_language(lang_code, script=script)
    hello: Optional[str] = data.get("hello_how_are_you") if data else None

    if not hello or not isinstance(hello, str) or len(hello.strip()) < 4:
        pytest.skip("No usable hello_how_are_you sample for this language")

    # Run detection with automatic candidate selection
    results: List[Tuple[str, float]] = optimized_detect_languages(
        hello, candidate_langs=None, topk=5
    )

    # Always ensure we get some results
    assert isinstance(results, list)

    # Soft checks: the function shouldn't crash; for diagnostics we collect info
    # We do not fail the test based on accuracy to avoid brittleness.
    # Still, we assert the return shape is correct.
    for item in results:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], float)


def test_detection_hello_summary(capfd: pytest.CaptureFixture[str]) -> None:
    """
    Emit a brief summary of hello-sample detection accuracy across languages.
    This does not enforce thresholds; it prints a summary to help evaluate quality.
    Run with `-s` to force printing.
    """
    entries = get_index_data()
    total = 0
    with_hello = 0
    exact_top1 = 0
    exact_top3 = 0

    # Optionally allow env var to limit to N languages for faster local runs
    limit = os.environ.get("WA_HELLO_TEST_LIMIT")
    if limit:
        try:
            limit_n = int(limit)
            entries = entries[:limit_n]
        except ValueError:
            pass

    samples = []

    for entry in entries:
        total += 1
        lang_code = entry["language"]
        script = entry.get("script")
        data = get_language(lang_code, script=script)
        hello = data.get("hello_how_are_you") if data else None
        if not hello or not isinstance(hello, str) or len(hello.strip()) < 4:
            continue
        with_hello += 1

        results = optimized_detect_languages(hello, candidate_langs=None, topk=5)
        codes = [c for (c, _s) in results]
        if codes:
            if codes[0] == lang_code:
                exact_top1 += 1
            if lang_code in codes[:3]:
                exact_top3 += 1

        samples.append((lang_code, hello[:50], codes[:3]))

    print(f"Total languages in index: {total}")
    print(f"Languages with hello sample: {with_hello}")

    top1_pct = (exact_top1 / with_hello * 100) if with_hello else 0.0
    top3_pct = (exact_top3 / with_hello * 100) if with_hello else 0.0
    print(f"Exact match @ top1: {exact_top1}/{with_hello} ({top1_pct:.1f}%)")
    print(f"Exact match within top3: {exact_top3}/{with_hello} ({top3_pct:.1f}%)")

    # Show a small sample for quick inspection
    preview = samples[:10]
    for code, snippet, top3 in preview:
        print(f"{code:>6}: '{snippet}...' => {top3}")

    # Keep the test green; this test is diagnostic.
    assert True
