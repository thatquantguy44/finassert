import json
import subprocess
import sys
from pathlib import Path


def test_reference_benchmark_retains_reproducible_corpus_and_measurements(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    output = tmp_path / "baseline.json"
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/benchmark_validation.py"),
            "--sizes",
            "20",
            "--adapters",
            "mapping",
            "--repeats",
            "1",
            "--output",
            str(output),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    artifact = json.loads(output.read_text())
    assert artifact["benchmark_schema_version"] == 1
    assert artifact["method"]["fresh_process_per_case"]
    assert artifact["environment"]["python"]
    assert len(artifact["source_sha256"]) == 64
    cases = artifact["results"]
    assert len(cases) == 8
    for case in cases:
        assert case["rows"] == 20
        assert len(case["warm_validation_seconds"]) == 1
        assert case["validation_peak_tracemalloc_bytes"] > 0
        assert case["process_peak_rss_bytes"] > 0
        assert case["top_functions_by_cumulative_time"]
        assert case["outcome"] == (
            "passed" if case["case"] in {"allocation", "grouped_skew"} else "failed"
        )
