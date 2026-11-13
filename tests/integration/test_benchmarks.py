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


def test_shared_read_benchmark_measures_policy_reads_and_preserves_reports(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    artifacts = {}
    for execution in ("scalar", "shared"):
        output = tmp_path / f"{execution}.json"
        result = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/benchmark_shared_reads.py"),
                "--sizes",
                "20",
                "--rule-counts",
                "1",
                "10",
                "50",
                "--adapters",
                "mapping",
                "--repeats",
                "1",
                "--execution",
                execution,
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
        assert artifact["method"]["profiling_separate_from_timings"]
        assert len(artifact["results"]) == 6
        for case in artifact["results"]:
            assert case["column_materializations"] == (
                case["rule_count"] if execution == "scalar" else 1
            )
            assert case["profiled_extraction_seconds"] > 0
            assert case["validation_peak_tracemalloc_bytes"] > 0
        artifacts[execution] = artifact
    assert [case["report_fingerprint"] for case in artifacts["scalar"]["results"]] == [
        case["report_fingerprint"] for case in artifacts["shared"]["results"]
    ]
