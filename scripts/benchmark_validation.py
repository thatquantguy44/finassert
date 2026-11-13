"""Retain reproducible scalar validation timing, memory, and profiling baselines.

Every case runs in a fresh worker process. Input construction and imports are
excluded from validation timing; tracemalloc and cProfile use separate runs.
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
import tracemalloc
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ("allocation", "nonnegative_sparse", "nonnegative_dense", "grouped_skew")


def _corpus(size: int, case: str, domain: str) -> tuple[dict[str, list[Any]], Any]:
    import finassert as fa

    def number(value: int) -> Decimal | float:
        return Decimal(value) if domain == "decimal" else float(value)

    tolerance = Decimal("1e-18") if domain == "decimal" else 1e-8
    if case == "allocation":
        return {"weight": [number(1) / number(size)] * size}, fa.weights_sum_to_one(
            tolerance=tolerance
        )
    if case.startswith("nonnegative"):
        values = [number(-1 if case.endswith("dense") or i % 100 == 0 else 1) for i in range(size)]
        return {"value": values}, fa.non_negative(column="value", max_violations=20)
    groups = ["HEAVY"] * (size * 9 // 10) + [f"G{i % 100:03}" for i in range(size - size * 9 // 10)]
    counts = Counter(groups)
    return {
        "book": groups,
        "weight": [number(1) / number(counts[group]) for group in groups],
    }, fa.weights_sum_to_one(group_by=["book"], tolerance=tolerance, max_violations=20)


def _fingerprint(report: Any) -> str:
    text = json.dumps(report.to_dict(), sort_keys=True, allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


def _worker(size: int, case: str, domain: str, adapter: str, repeats: int) -> dict[str, Any]:
    import finassert as fa

    started = time.perf_counter()
    columns, rule = _corpus(size, case, domain)
    if adapter == "pandas":
        import pandas as pd

        data: Any = pd.DataFrame(columns)
    else:
        data = columns
    construction = time.perf_counter() - started
    gc.collect()
    started = time.perf_counter()
    report = fa.check(data, [rule])
    cold = time.perf_counter() - started
    digest = _fingerprint(report)
    expected_pass = case in {"allocation", "grouped_skew"}
    if report.passed != expected_pass or report.counts_by_outcome["error"]:
        raise RuntimeError(f"corpus invariant failed: {case}, {report.summary()}")
    warm = []
    for _ in range(repeats):
        gc.collect()
        started = time.perf_counter()
        repeated = fa.check(data, [rule])
        warm.append(time.perf_counter() - started)
        if _fingerprint(repeated) != digest:
            raise RuntimeError("repeated validation changed reference results")
    gc.collect()
    tracemalloc.start()
    memory_report = fa.check(data, [rule])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if _fingerprint(memory_report) != digest:
        raise RuntimeError("memory profiling changed results")
    profile = cProfile.Profile()
    profile.enable()
    profiled = fa.check(data, [rule])
    profile.disable()
    if _fingerprint(profiled) != digest:
        raise RuntimeError("CPU profiling changed results")
    stats = pstats.Stats(profile)
    functions = []
    for (filename, line, function), values in sorted(
        stats.stats.items(), key=lambda item: item[1][3], reverse=True
    )[:12]:
        path = Path(filename)
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = path.name
        functions.append(
            {
                "function": f"{label}:{line}:{function}",
                "calls": values[1],
                "self_seconds": values[2],
                "cumulative_seconds": values[3],
            }
        )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = report.results[0]
    return {
        "case": case,
        "adapter": adapter,
        "numeric_domain": domain,
        "rows": size,
        "columns": len(columns),
        "group_count": result.metadata.get("group_count", 1),
        "group_skew": "90% in HEAVY, remainder across up to 100 groups"
        if case == "grouped_skew"
        else None,
        "input_construction_seconds": construction,
        "first_validation_seconds": cold,
        "warm_validation_seconds": warm,
        "warm_median_seconds": statistics.median(warm),
        "validation_peak_tracemalloc_bytes": peak,
        "process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
        "outcome": result.outcome.value,
        "report_fingerprint": digest,
        "diagnostic_counts": {item.kind: item.count for item in result.diagnostics},
        "top_functions_by_cumulative_time": functions,
    }


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    """Run isolated reference cases and write one inspectable JSON artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[1000, 10000, 100000])
    parser.add_argument(
        "--adapters", nargs="+", choices=["mapping", "pandas"], default=["mapping", "pandas"]
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--case", choices=CASES, help=argparse.SUPPRESS)
    parser.add_argument("--domain", choices=["float", "decimal"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats < 1 or any(size < 1 for size in args.sizes):
        parser.error("sizes and repeats must be positive")
    if args.worker:
        print(
            json.dumps(
                _worker(args.sizes[0], args.case, args.domain, args.adapters[0], args.repeats),
                allow_nan=False,
            )
        )
        return 0
    if args.output is None:
        parser.error("--output is required")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONHASHSEED": "0"}
    results = []
    for size in args.sizes:
        for domain in ("float", "decimal"):
            for case in CASES:
                fingerprints: set[str] = set()
                for adapter in args.adapters:
                    command = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--worker",
                        "--sizes",
                        str(size),
                        "--case",
                        case,
                        "--domain",
                        domain,
                        "--adapters",
                        adapter,
                        "--repeats",
                        str(args.repeats),
                    ]
                    worker = subprocess.run(
                        command, env=environment, text=True, capture_output=True, check=True
                    )
                    result = json.loads(worker.stdout)
                    results.append(result)
                    fingerprints.add(result["report_fingerprint"])
                    print(
                        f"{size:>7} {domain:<7} {case:<20} {adapter:<7} "
                        f"{result['warm_median_seconds']:.6f}s",
                        flush=True,
                    )
                if len(fingerprints) != 1:
                    raise RuntimeError(
                        f"adapters changed reference results for {case}/{domain}/{size}"
                    )
    source = hashlib.sha256()
    for path in [*sorted((ROOT / "src/finassert").rglob("*.py")), Path(__file__)]:
        source.update(str(path.relative_to(ROOT)).encode())
        source.update(path.read_bytes())
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    artifact = {
        "benchmark_schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "revision": revision,
        "working_tree_dirty": dirty,
        "source_sha256": source.hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "packages": {name: _version(name) for name in ("finassert", "pandas", "openpyxl")},
        },
        "method": {
            "sizes": args.sizes,
            "adapters": args.adapters,
            "warm_repeats": args.repeats,
            "diagnostic_limit": 20,
            "fresh_process_per_case": True,
            "timings_exclude_input_construction": True,
            "memory_and_cpu_profile_separate_from_timings": True,
            "rss_scope": (
                "whole worker including imports and corpus; tracemalloc scope is validation only"
            ),
            "seed": "deterministic formulas and PYTHONHASHSEED=0",
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Retained {len(results)} reference cases in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
