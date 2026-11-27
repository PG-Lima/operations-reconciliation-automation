"""Command-line interface for local reconciliation runs."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from operations_reconciliation.application.reconciliation import run_reconciliation


def _parse_competence(value: str) -> date:
    """Parse a monthly competence in the strict YYYY-MM format."""
    if len(value) != 7 or value[4] != "-":
        raise argparse.ArgumentTypeError("Competence must use YYYY-MM.")

    try:
        return date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise argparse.ArgumentTypeError("Competence must use a valid YYYY-MM month.") from error


def _parse_date(value: str) -> date:
    """Parse a calendar date in the strict YYYY-MM-DD format."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Dates must use YYYY-MM-DD.") from error

    if parsed.isoformat() != value:
        raise argparse.ArgumentTypeError("Dates must use YYYY-MM-DD.")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="operations-reconciliation",
        description="Run a local operational reconciliation and generate an Excel report.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    reconcile = subparsers.add_parser(
        "reconcile",
        help="Reconcile movement and reference workbooks for one competence.",
    )
    reconcile.add_argument(
        "--movement-dir",
        type=Path,
        required=True,
        help="Directory containing movement workbooks.",
    )
    reconcile.add_argument(
        "--reference-dir",
        type=Path,
        required=True,
        help="Directory containing the monthly reference workbook.",
    )
    reconcile.add_argument(
        "--competence",
        type=_parse_competence,
        required=True,
        metavar="YYYY-MM",
        help="Monthly competence to reconcile.",
    )
    reconcile.add_argument(
        "--cutoff-date",
        type=_parse_date,
        required=True,
        metavar="YYYY-MM-DD",
        help="Last release date included in the comparison.",
    )
    reconcile.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination .xlsx file for the reconciliation report.",
    )
    reconcile.add_argument(
        "--evaluation-date",
        type=_parse_date,
        metavar="YYYY-MM-DD",
        help="Date used to evaluate classifications (defaults to the cutoff date).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_reconciliation(
            movement_directory=args.movement_dir,
            reference_directory=args.reference_dir,
            competence=args.competence,
            cutoff_date=args.cutoff_date,
            output_path=args.output,
            evaluation_date=args.evaluation_date,
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("Reconciliation completed successfully.")
    print(f"Movement workbook: {result.movement_workbook}")
    print(f"Reference workbook: {result.reference_workbook}")
    print(f"Report: {result.output_workbook}")
    return 0
