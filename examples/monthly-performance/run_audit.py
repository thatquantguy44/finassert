"""Run the P-05 workbook through the Python API and assert the expected outcome."""

from __future__ import annotations

import argparse
from pathlib import Path

from finassert.loaders import load_input
from finassert.policy import load_policy

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=ROOT / "monthly-performance-audit.xlsx")
    parser.add_argument("--policy", type=Path, default=ROOT / "policy.yml")
    parser.add_argument("--expect", choices=("failed", "passed"), default="failed")
    arguments = parser.parse_args()

    data = load_input(
        arguments.workbook,
        format="xlsx",
        sheet="Audit input",
        header_row=5,
        max_row=17,
    )
    report = load_policy(arguments.policy).check(data)
    (result,) = report.results
    print(report.summary())
    print(f"Outcome: {result.outcome.value}")
    if isinstance(result.observed, dict) and "comparison_count" in result.observed:
        print(f"Reference comparisons: {result.observed['comparison_count']}")
    if result.outcome.value == "failed":
        examples = result.diagnostics[1].observations if len(result.diagnostics) > 1 else ()
        if examples and isinstance(examples[0], dict):
            example = examples[0]
            print(
                "First discrepancy: "
                f"{example['source_row']} {example['field']} expected "
                f"{example['expected']} observed {example['observed']}."
            )
    return 0 if result.outcome.value == arguments.expect else 1


if __name__ == "__main__":
    raise SystemExit(main())
