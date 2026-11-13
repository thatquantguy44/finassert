import pytest

import finassert as fa
from finassert.core.models import Outcome, Severity, ValidationReport, ValidationResult
from finassert.policy import parse_policy
from finassert.reporting import build_artifact, render_artifact_html

DATA = {"weight": [0.5, -0.1, 0.6]}


def report_for(severity: str, **extra: object) -> ValidationReport:
    return fa.check(DATA, [fa.non_negative(column="weight", severity=severity, **extra)])  # type: ignore[arg-type]


def test_an_error_severity_failure_fails_the_report_as_before() -> None:
    report = report_for("error")

    assert report.counts_by_outcome["failed"] == 1
    assert report.passed is False
    assert [r.rule_id for r in report.blocking_failures] == ["arithmetic.non_negative"]
    assert report.warnings == ()


@pytest.mark.parametrize("severity", ["warning", "info"])
def test_lower_severity_failures_are_warnings_that_do_not_fail_the_report(severity: str) -> None:
    report = report_for(severity)

    (result,) = report.results
    assert result.outcome is Outcome.FAILED  # the finding itself is unchanged
    assert result.warning and not result.blocking
    assert report.passed is True
    assert report.warnings == (result,) and report.blocking_failures == ()
    assert report.failures == (result,)  # still listed as a failure


def test_a_check_that_could_not_run_always_fails_the_report() -> None:
    report = fa.check({"other": [1]}, [fa.non_negative(column="weight", severity="info")])

    (result,) = report.results
    assert result.outcome is Outcome.ERROR
    assert result.blocking and not result.warning
    assert report.passed is False


def test_blocks_honours_a_stricter_threshold() -> None:
    (warning,) = report_for("warning").results
    (note,) = report_for("info").results

    assert not warning.blocks() and not note.blocks()
    assert warning.blocks(Severity.WARNING) and not note.blocks(Severity.WARNING)
    assert warning.blocks(Severity.INFO) and note.blocks(Severity.INFO)


def test_mixed_severities_pass_only_when_every_error_check_passes() -> None:
    warn_only = [
        fa.non_negative(column="weight", severity="warning"),
        fa.weights_sum_to_one(severity="error"),  # the weights do add up to 1
    ]
    one_error = [
        fa.non_negative(column="weight", severity="warning"),
        fa.non_negative(column="weight", severity="error"),
    ]

    assert fa.check(DATA, warn_only).passed is True
    assert fa.check(DATA, one_error).passed is False


def test_the_summary_and_dictionary_report_warnings() -> None:
    report = report_for("warning")

    assert report.summary().startswith("finassert PASS (1 warning): 0 passed, 1 failed")
    assert "- [warning] arithmetic.non_negative:" in report.summary()
    payload = report.to_dict()
    assert payload["passed"] is True
    assert (payload["blocking_failures"], payload["warnings"]) == (0, 1)
    assert payload["results"][0]["blocking"] is False
    assert report_for("error").summary().startswith("finassert FAIL:")
    assert report_for("error").to_dict()["results"][0]["blocking"] is True


def test_an_empty_report_and_passing_report_have_no_warnings() -> None:
    assert ValidationReport().passed and ValidationReport().warnings == ()
    result = ValidationResult("x.y", "X", Outcome.PASSED, Severity.WARNING, "ok")
    assert not result.warning and not result.blocking


def test_severity_ranks_order_error_above_warning_above_info() -> None:
    assert Severity.ERROR.rank > Severity.WARNING.rank > Severity.INFO.rank


def html_for(severity: str) -> str:
    policy = parse_policy(
        {
            "version": 1,
            "name": "P",
            "rules": [
                {"rule": "non_negative", "column": "weight", "severity": severity},
                {"rule": "weights_sum_to_one", "tolerance": 1},
            ],
        }
    )
    return render_artifact_html(build_artifact(policy.check(DATA), policy=policy))


def test_the_html_report_marks_warnings_without_calling_the_run_failed() -> None:
    page = html_for("warning")

    assert "<strong>Passed with warnings</strong>" in page
    assert 'class="banner warning"' in page
    assert '<span class="pill warning">Warning: 1</span>' in page
    assert 'class="card warning"' in page
    assert "which is set to warn" in page
    assert 'class="banner failed"' not in page


def test_the_html_report_still_fails_for_error_severity() -> None:
    page = html_for("error")

    assert "<strong>Failed</strong>" in page
    assert 'class="card failed"' in page and "Warning: " not in page


def test_exit_codes_follow_the_threshold() -> None:
    from finassert.cli import EXIT_ERROR, EXIT_FAILED, EXIT_PASSED, exit_code

    warned = report_for("warning")
    assert exit_code(warned) == EXIT_PASSED
    assert exit_code(warned, "warning") == EXIT_FAILED
    assert exit_code(warned, Severity.INFO) == EXIT_FAILED
    assert exit_code(report_for("error")) == EXIT_FAILED
    broken = fa.check({"x": [1]}, [fa.non_negative(column="weight", severity="info")])
    assert exit_code(broken) == EXIT_ERROR
    with pytest.raises(ValueError):
        exit_code(warned, "fatal")
