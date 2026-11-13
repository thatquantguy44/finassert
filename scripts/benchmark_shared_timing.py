"""Resolve timing variability with alternating scalar/shared pairs in each worker.

Uses the same policy as benchmark_shared_reads.py. Each adapter/domain runs in a
fresh process, with both modes warmed and alternating order over identical data.
Wall and process CPU times are recorded separately, without instrumentation.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _worker(adapter: str, domain: str, repeats: int) -> dict[str, Any]:
    import finassert as fa
    from finassert.core.engine import _check

    number = Decimal if domain == "decimal" else float
    data: Any = {"value": [number(1) / number(100000)] * 100000}
    if adapter == "pandas":
        import pandas as pd

        data = pd.DataFrame(data)
    tolerance = Decimal("1e-18") if domain == "decimal" else 1e-8
    rules = [
        (
            fa.non_negative(column="value"),
            fa.in_range(column="value", minimum=0, maximum=1),
            fa.weights_sum_to_one(column="value", tolerance=tolerance),
        )[i % 3]
        for i in range(50)
    ]
    expected = None
    samples = []
    for pair in range(-1, repeats):
        for mode in ("scalar", "shared") if pair % 2 == 0 else ("shared", "scalar"):
            gc.collect()
            wall = time.perf_counter()
            cpu = time.process_time()
            report = _check(data, rules, share_columns=mode == "shared")
            cpu = time.process_time() - cpu
            wall = time.perf_counter() - wall
            digest = hashlib.sha256(
                json.dumps(report.to_dict(), sort_keys=True, allow_nan=False).encode()
            ).hexdigest()
            if expected is None:
                expected = digest
            if not report.passed or digest != expected:
                raise RuntimeError("paired timing report changed")
            if pair >= 0:
                samples.append(
                    {"pair": pair + 1, "execution": mode, "wall_seconds": wall, "cpu_seconds": cpu}
                )
    return {
        "rows": 100000,
        "rule_count": 50,
        "adapter": adapter,
        "numeric_domain": domain,
        "report_fingerprint": expected,
        "samples": samples,
    }


def main() -> int:
    """Retain alternating within-process timing pairs and exact source identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--adapter", choices=["mapping", "pandas"], help=argparse.SUPPRESS)
    parser.add_argument("--domain", choices=["float", "decimal"], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    if args.worker:
        print(json.dumps(_worker(args.adapter, args.domain, args.repeats)))
        return 0
    if args.output is None:
        parser.error("--output is required")
    results = []
    for domain in ("float", "decimal"):
        for adapter in ("mapping", "pandas"):
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--domain",
                domain,
                "--adapter",
                adapter,
                "--repeats",
                str(args.repeats),
            ]
            result = json.loads(
                subprocess.check_output(
                    command,
                    env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONHASHSEED": "0"},
                    text=True,
                )
            )
            results.append(result)
            print(domain, adapter, "paired timings retained", flush=True)
    source = hashlib.sha256()
    for path in [
        *sorted((ROOT / "src/finassert").rglob("*.py")),
        ROOT / "scripts/benchmark_shared_reads.py",
        Path(__file__),
    ]:
        source.update(str(path.relative_to(ROOT)).encode())
        source.update(path.read_bytes())
    artifact = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_sha256": source.hexdigest(),
        "method": {
            "warmup_pairs": 1,
            "timed_pairs": args.repeats,
            "order": "alternating scalar/shared within each worker",
            "fresh_process_per_adapter_domain": True,
            "timings_exclude_construction_gc_serialization": True,
            "cpu_time": "process_time; excludes time not scheduled on CPU",
            "profiling": "none",
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
