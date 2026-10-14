"""Noninteractive command-line interface.

Exit codes:

* ``0`` every check passed or was skipped, or failed only at a severity below
  ``--fail-on`` (by default, ``warning`` and ``info`` checks do not fail the run);
* ``1`` at least one check failed at or above the ``--fail-on`` severity;
* ``2`` at least one check could not run (wins over ``1``);
* ``3`` the command line or policy is invalid;
* ``4`` an input file could not be read or a report could not be written.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn, TextIO

from finassert._files import write_atomic
from finassert._version import __version__
from finassert._xlsx import SheetError
from finassert.core.exceptions import InvalidDataError, PolicyError
from finassert.core.models import Severity, ValidationReport
from finassert.loaders import INPUT_FORMATS, column_names, input_format_for, load_input
from finassert.policy import (
    POLICY_FORMATS,
    default_catalog,
    get_template,
    load_policy,
    policy_templates,
)
from finassert.policy.issues import closest
from finassert.policy.suggest import TemplateFit, fit_template, suggest_templates
from finassert.reporting import artifact_to_json, build_artifact, render_artifact_html

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_ERROR = 2
EXIT_USAGE = 3
EXIT_IO = 4


class _UsageError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return its exit code."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    try:
        if arguments.command == "rules":
            return _rules(json_output=arguments.json, stream=sys.stdout)
        if arguments.command == "templates":
            return _templates(stream=sys.stdout)
        if arguments.command == "init":
            return _init(arguments)
        if arguments.command == "suggest":
            return _suggest(arguments)
        return _check(arguments)
    except KeyboardInterrupt:
        print("finassert: interrupted; no report was written.", file=sys.stderr)
        return 130


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="finassert",
        description="Check financial data files against a validation policy.",
        epilog=(
            "Exit codes: 0 passed, 1 a check failed, 2 a check could not run, "
            "3 invalid command or policy, 4 file could not be read or written."
        ),
    )
    parser.add_argument("--version", action="version", version=f"finassert {__version__}")
    commands = parser.add_subparsers(dest="command", parser_class=_ArgumentParser)

    check = commands.add_parser(
        "check",
        help="validate a data file against a policy",
        description="Validate a CSV or JSON data file against a YAML or JSON policy.",
    )
    check.add_argument("--config", required=True, metavar="POLICY", help="policy file")
    check.add_argument("--input", required=True, metavar="FILE", help="data file to check")
    check.add_argument(
        "--format",
        choices=INPUT_FORMATS,
        help="input format; inferred from the file extension when omitted",
    )
    check.add_argument(
        "--policy-format",
        choices=POLICY_FORMATS,
        help="policy format; inferred from the file extension when omitted",
    )
    check.add_argument(
        "--sheet",
        metavar="NAME",
        help="worksheet to check in an Excel workbook; required if it has several sheets",
    )
    check.add_argument("--output", metavar="FILE", help="write the JSON report here")
    check.add_argument("--html", metavar="FILE", help="write a readable HTML report here")
    check.add_argument(
        "--fail-on",
        choices=[item.value for item in Severity],
        default=Severity.ERROR.value,
        metavar="SEVERITY",
        help=(
            "lowest severity of a failed check that fails the run: error (the default, so "
            "'warning' and 'info' checks only warn), warning, or info"
        ),
    )
    check.add_argument("--quiet", action="store_true", help="do not print the summary")

    rules = commands.add_parser(
        "rules",
        help="list the checks a policy can use",
        description="Describe every rule a policy may name, in plain language.",
    )
    rules.add_argument("--json", action="store_true", help="print the catalog as JSON")

    commands.add_parser(
        "templates",
        help="list starter policies",
        description="List the starter policies 'finassert init' can write.",
    )

    init = commands.add_parser(
        "init",
        help="write a starter policy from a template",
        description="Write a starter policy, with its assumptions, for you to adapt.",
    )
    init.add_argument("--template", required=True, metavar="NAME", help="template to start from")
    init.add_argument(
        "--output", default="policy.yml", metavar="FILE", help="where to write it (policy.yml)"
    )
    init.add_argument("--force", action="store_true", help="replace an existing file")

    suggest = commands.add_parser(
        "suggest",
        help="find the template that fits a data file and match its columns",
        description=(
            "Read a data file's column names, rank the starter policies by how well their "
            "columns match, and optionally write the best fit with your column names filled "
            "in. The matches are proposals for you to confirm: nothing is applied silently."
        ),
    )
    suggest.add_argument("--input", required=True, metavar="FILE", help="data file to read")
    suggest.add_argument("--format", choices=INPUT_FORMATS, help="input format")
    suggest.add_argument("--sheet", metavar="NAME", help="worksheet in an Excel workbook")
    suggest.add_argument("--template", metavar="NAME", help="match this template only")
    suggest.add_argument(
        "--output", metavar="FILE", help="write the best-fitting policy here, columns filled in"
    )
    suggest.add_argument("--force", action="store_true", help="replace an existing file")
    suggest.add_argument("--json", action="store_true", help="print the suggestions as JSON")
    return parser


def _check(arguments: argparse.Namespace) -> int:
    outputs = [Path(item) for item in (arguments.output, arguments.html) if item]
    if len({path.resolve() for path in outputs}) != len(outputs):
        return _fail(EXIT_USAGE, "--output and --html must name different files.")
    if any(path.resolve() == Path(arguments.input).resolve() for path in outputs):
        return _fail(EXIT_USAGE, "a report path must not be the input file.")

    try:
        policy = load_policy(arguments.config, format=arguments.policy_format)
    except PolicyError as exc:
        lines = "\n".join(f"  - {issue}" for issue in exc.issues)
        return _fail(EXIT_USAGE, f"the policy {arguments.config!r} is not valid:\n{lines}")
    except OSError as exc:
        return _fail(EXIT_USAGE, f"cannot read policy {arguments.config!r}: {_reason(exc)}")

    try:
        data = load_input(arguments.input, format=arguments.format, sheet=arguments.sheet)
    except SheetError as exc:
        hint = "; pass one with --sheet NAME" if arguments.sheet is None and exc.sheets else ""
        return _fail(EXIT_USAGE, f"{arguments.input!r}: {exc}{hint}.")
    except InvalidDataError as exc:
        return _fail(EXIT_IO, f"cannot read input {arguments.input!r}: {exc}")
    except OSError as exc:
        return _fail(EXIT_IO, f"cannot read input {arguments.input!r}: {_reason(exc)}")

    report = policy.check(data)
    input_format = arguments.format or input_format_for(Path(arguments.input))
    artifact = build_artifact(
        report,
        policy=policy,
        input_locator=arguments.input,
        input_format=input_format,
        input_sheet=arguments.sheet,
        generated_at=_generated_at(),
    )

    fail_on = Severity(arguments.fail_on)
    code = exit_code(report, fail_on)
    if not arguments.quiet:
        print(report.summary())
        if code == EXIT_FAILED and report.passed:
            print(f"Failing because --fail-on {fail_on.value} counts these warnings as failures.")
    try:
        if arguments.output:
            write_atomic(Path(arguments.output), artifact_to_json(artifact) + "\n")
            if not arguments.quiet:
                print(f"JSON report written to {arguments.output}")
        if arguments.html:
            write_atomic(Path(arguments.html), render_artifact_html(artifact))
            if not arguments.quiet:
                print(f"HTML report written to {arguments.html}")
    except OSError as exc:
        return _fail(EXIT_IO, f"cannot write report: {_reason(exc)}")
    return code


def exit_code(report: ValidationReport, fail_on: Severity | str = Severity.ERROR) -> int:
    """Return the documented exit code for ``report``.

    A check that could not run always gives ``2``. A failed check gives ``1`` when
    its severity is at least ``fail_on``; failures below it are warnings.
    """
    threshold = Severity(fail_on)
    if report.counts_by_outcome["error"]:
        return EXIT_ERROR
    if any(result.blocks(threshold) for result in report.results):
        return EXIT_FAILED
    return EXIT_PASSED


def _rules(*, json_output: bool, stream: TextIO) -> int:
    catalog = default_catalog()
    if json_output:
        print(json.dumps(catalog.to_dict(), indent=2, sort_keys=True), file=stream)
        return EXIT_PASSED
    for spec in catalog.specs():
        print(f"{spec.title}", file=stream)
        print(f"  rule: {spec.name}   (id {spec.rule_id})", file=stream)
        print(f"  {spec.summary}", file=stream)
        print(f"  Why it matters: {spec.rationale}", file=stream)
        print(f"  Do not use when: {spec.inappropriate_when}", file=stream)
        print("  Settings:", file=stream)
        for parameter in spec.parameters:
            if parameter.required:
                note = "required"
            elif parameter.default is None:
                note = "optional"
            else:
                note = f"default {parameter.default}"
            if parameter.choices:
                note += f"; one of {', '.join(parameter.choices)}"
            print(f"    {parameter.name} ({note}): {parameter.description}", file=stream)
        print(file=stream)
    return EXIT_PASSED


def _templates(*, stream: TextIO) -> int:
    for template in policy_templates():
        print(f"{template.name}: {template.title}", file=stream)
        print(f"  {template.summary}", file=stream)
    print("\nWrite one with: finassert init --template NAME", file=stream)
    return EXIT_PASSED


def _init(arguments: argparse.Namespace) -> int:
    try:
        template = get_template(arguments.template)
    except KeyError:
        names = [template.name for template in policy_templates()]
        hint = closest(arguments.template, names)
        suggestion = f" Did you mean {hint!r}?" if hint else ""
        return _fail(
            EXIT_USAGE,
            f"unknown template {arguments.template!r}; available: {', '.join(names)}.{suggestion}",
        )
    path = Path(arguments.output)
    if path.exists() and not arguments.force:
        return _fail(
            EXIT_USAGE, f"{arguments.output!r} already exists; pass --force to replace it."
        )
    try:
        write_atomic(path, template.to_yaml())
    except OSError as exc:
        return _fail(EXIT_IO, f"cannot write {arguments.output!r}: {_reason(exc)}")
    print(f"Wrote {arguments.output} from the '{template.name}' template.")
    print("Before relying on it:")
    for line in template.adapt:
        print(f"  - {line}")
    print("  - Check the assumptions listed in the file hold for your data.")
    return EXIT_PASSED


def _suggest(arguments: argparse.Namespace) -> int:
    path = Path(arguments.output) if arguments.output else None
    if path is not None and path.exists() and not arguments.force:
        return _fail(
            EXIT_USAGE, f"{arguments.output!r} already exists; pass --force to replace it."
        )
    try:
        data = load_input(arguments.input, format=arguments.format, sheet=arguments.sheet)
    except SheetError as exc:
        hint = "; pass one with --sheet NAME" if arguments.sheet is None and exc.sheets else ""
        return _fail(EXIT_USAGE, f"{arguments.input!r}: {exc}{hint}.")
    except InvalidDataError as exc:
        return _fail(EXIT_IO, f"cannot read input {arguments.input!r}: {exc}")
    except OSError as exc:
        return _fail(EXIT_IO, f"cannot read input {arguments.input!r}: {_reason(exc)}")
    columns = column_names(data)

    fits: tuple[TemplateFit, ...]
    if arguments.template:
        try:
            fits = (fit_template(get_template(arguments.template), columns),)
        except KeyError:
            names = [template.name for template in policy_templates()]
            near = closest(arguments.template, names)
            suggestion = f" Did you mean {near!r}?" if near else ""
            return _fail(
                EXIT_USAGE,
                f"unknown template {arguments.template!r}; available: "
                f"{', '.join(names)}.{suggestion}",
            )
    else:
        fits = suggest_templates(columns)

    if arguments.json:
        print(json.dumps({"columns": columns, "suggestions": [fit.to_dict() for fit in fits]}))
    else:
        _print_suggestions(arguments.input, columns, fits)
    if path is None:
        return EXIT_PASSED
    if not fits:
        return _fail(EXIT_USAGE, "no template fits this file, so nothing was written.")
    best = fits[0]
    try:
        write_atomic(path, best.adapted().to_yaml())
    except OSError as exc:
        return _fail(EXIT_IO, f"cannot write {arguments.output!r}: {_reason(exc)}")
    print(f"\nWrote {arguments.output} from the '{best.template.name}' template.")
    print("Before relying on it:")
    for line in best.adapted().adapt:
        print(f"  - {line}")
    print("  - Check the assumptions listed in the file hold for your data.")
    return EXIT_PASSED


def _print_suggestions(name: str, columns: list[str], fits: tuple[TemplateFit, ...]) -> None:
    print(f"{name}: {len(columns)} column(s): {', '.join(columns)}")
    if not fits:
        print("\nNo starter policy fits these columns. See 'finassert templates', or write")
        print("a policy yourself with 'finassert rules' as a guide.")
        return
    for position, fit in enumerate(fits, start=1):
        print(f"\n{position}. {fit.template.name}: {fit.template.title}")
        print(
            f"   {len(fit.matched)} of {len(fit.matches)} columns matched. {fit.template.summary}"
        )
        for match in fit.matches:
            print(f"   - {match.sentence}")
    print("\nThese are proposals: confirm each match before relying on it.")
    print("Write the best fit with: finassert suggest --input FILE --output policy.yml")


def _generated_at() -> datetime:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), UTC)
    return datetime.now(UTC)


def _reason(exc: OSError) -> str:
    return exc.strerror or str(exc)


def _fail(code: int, message: str) -> int:
    print(f"finassert: {message}", file=sys.stderr)
    return code
