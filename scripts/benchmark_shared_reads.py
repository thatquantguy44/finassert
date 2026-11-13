"""Measure policies with 1/10/50 rules sharing a column, in isolated processes.

Construction, validation timings, tracemalloc and cProfile are separate. Scalar
execution is the uncached reference; shared execution uses the ordinary check.
"""

from __future__ import annotations

import argparse
import cProfile
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import pstats
import resource
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _fingerprint(report: Any) -> str:
    return hashlib.sha256(
        json.dumps(report.to_dict(), sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def _worker(
    rows: int, count: int, domain: str, adapter: str, repeats: int, execution: str
) -> dict[str, Any]:
    import tracemalloc

    import finassert as fa
    from finassert.core import engine

    started = time.perf_counter()
    number = Decimal if domain == "decimal" else float
    value = number(1) / number(rows)
    columns = {"value": [value] * rows}
    data: Any = columns
    if adapter == "pandas":
        import pandas as pd

        data = pd.DataFrame(columns)
    tolerance = Decimal("1e-18") if domain == "decimal" else 1e-8
    rules = [
        (
            fa.non_negative(column="value"),
            fa.in_range(column="value", minimum=0, maximum=1),
            fa.weights_sum_to_one(column="value", tolerance=tolerance),
        )[index % 3]
        for index in range(count)
    ]
    construction = time.perf_counter() - started

    def evaluate() -> Any:
        if execution == "scalar" and hasattr(engine, "_check"):
            return engine._check(data, rules, share_columns=False)
        return fa.check(data, rules)

    gc.collect()
    started = time.perf_counter()
    report = evaluate()
    first = time.perf_counter() - started
    if not report.passed or len(report.results) != count:
        raise RuntimeError(f"benchmark policy failed: {report.summary()}")
    digest = _fingerprint(report)
    warm = []
    for _ in range(repeats):
        gc.collect()
        started = time.perf_counter()
        repeated = evaluate()
        warm.append(time.perf_counter() - started)
        if _fingerprint(repeated) != digest:
            raise RuntimeError("repeated report changed")
    gc.collect()
    tracemalloc.start()
    measured = evaluate()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if _fingerprint(measured) != digest:
        raise RuntimeError("memory profiling changed report")
    profile = cProfile.Profile()
    profile.enable()
    profiled = evaluate()
    profile.disable()
    if _fingerprint(profiled) != digest:
        raise RuntimeError("CPU profiling changed report")
    stats = pstats.Stats(profile).stats
    # The private uncached helper appears only once sharing is implemented.
    materializer = (
        "_extract_uncached"
        if any(key[2] == "_extract_uncached" for key in stats)
        else "extract_column"
    )
    extraction = [
        value
        for key, value in stats.items()
        if key[2] == materializer and Path(key[0]).name == "_column.py"
    ]
    functions = []
    for (filename, line, function), entry in sorted(
        stats.items(), key=lambda item: item[1][3], reverse=True
    )[:12]:
        try:
            label = str(Path(filename).relative_to(ROOT))
        except ValueError:
            label = Path(filename).name
        functions.append(
            {
                "function": f"{label}:{line}:{function}",
                "calls": entry[1],
                "self_seconds": entry[2],
                "cumulative_seconds": entry[3],
            }
        )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "rows": rows,
        "rule_count": count,
        "numeric_domain": domain,
        "adapter": adapter,
        "execution": execution,
        "columns": 1,
        "report_fingerprint": digest,
        "input_construction_seconds": construction,
        "first_validation_seconds": first,
        "warm_validation_seconds": warm,
        "warm_median_seconds": statistics.median(warm),
        "validation_peak_tracemalloc_bytes": peak,
        "process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
        "column_materializations": sum(entry[1] for entry in extraction),
        "profiled_extraction_seconds": sum(entry[3] for entry in extraction),
        "top_functions_by_cumulative_time": functions,
    }


def main() -> int:
    """Retain comparable multi-rule policy measurements and source identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[1000, 100000])
    parser.add_argument("--rule-counts", nargs="+", type=int, default=[1, 10, 50])
    parser.add_argument(
        "--adapters", nargs="+", choices=["mapping", "pandas"], default=["mapping", "pandas"]
    )
    parser.add_argument("--execution", choices=["scalar", "shared"], default="scalar")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--domain", choices=["float", "decimal"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats < 1 or any(value < 1 for value in [*args.sizes, *args.rule_counts]):
        parser.error("sizes, rule counts and repeats must be positive")
    if args.worker:
        print(
            json.dumps(
                _worker(
                    args.sizes[0],
                    args.rule_counts[0],
                    args.domain,
                    args.adapters[0],
                    args.repeats,
                    args.execution,
                ),
                allow_nan=False,
            )
        )
        return 0
    if args.output is None:
        parser.error("--output is required")
    results = []
    for rows in args.sizes:
        for count in args.rule_counts:
            for domain in ("float", "decimal"):
                fingerprints = set()
                for adapter in args.adapters:
                    command = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--worker",
                        "--sizes",
                        str(rows),
                        "--rule-counts",
                        str(count),
                        "--domain",
                        domain,
                        "--adapters",
                        adapter,
                        "--repeats",
                        str(args.repeats),
                        "--execution",
                        args.execution,
                    ]
                    worker = subprocess.run(
                        command,
                        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONHASHSEED": "0"},
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    result = json.loads(worker.stdout)
                    results.append(result)
                    fingerprints.add(result["report_fingerprint"])
                    print(
                        f"{rows:>7} {count:>2} rules {domain:<7} {adapter:<7} "
                        f"{result['warm_median_seconds']:.6f}s",
                        flush=True,
                    )
                if len(fingerprints) != 1:
                    raise RuntimeError("adapter reports differ")
    source = hashlib.sha256()
    for path in [*sorted((ROOT / "src/finassert").rglob("*.py")), Path(__file__)]:
        source.update(str(path.relative_to(ROOT)).encode())
        source.update(path.read_bytes())
    artifact = {
        "benchmark_schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        ),
        "source_sha256": source.hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "logical_cpus": os.cpu_count(),
            "pandas": importlib.metadata.version("pandas"),
        },
        "method": {
            "sizes": args.sizes,
            "rule_counts": args.rule_counts,
            "execution": args.execution,
            "warm_repeats": args.repeats,
            "fresh_process_per_case": True,
            "timings_exclude_construction": True,
            "profiling_separate_from_timings": True,
            "extraction_time_scope": (
                "cProfile cumulative time in the raw column materializer; includes list and "
                "label creation, instrumentation overhead applies"
            ),
            "rss_scope": "whole worker; tracemalloc covers validation only",
            "policy": (
                "alternating non_negative, in_range and weights_sum_to_one "
                "over one shared column; all pass"
            ),
            "seed": "deterministic formulas; PYTHONHASHSEED=0",
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Retained {len(results)} cases in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
