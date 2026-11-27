"""Coordinate the complete local reconciliation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from operations_reconciliation.adapters.excel_reader import (
    read_movement_workbook,
    read_reference_workbook,
)
from operations_reconciliation.adapters.excel_report import write_comparison_report
from operations_reconciliation.adapters.file_discovery import (
    discover_movement_workbook,
    discover_reference_workbook,
)
from operations_reconciliation.adapters.local_task_board import LocalTaskBoard
from operations_reconciliation.domain.models import ComparisonReport
from operations_reconciliation.services.comparison import compare_companies
from operations_reconciliation.services.consolidation import consolidate_releases
from operations_reconciliation.services.task_creation import (
    TaskBoardSimulationResult,
    create_underpaid_tasks,
)


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Artifacts and report produced by one reconciliation execution."""

    movement_workbook: Path
    reference_workbook: Path
    report: ComparisonReport
    output_workbook: Path
    task_board_result: TaskBoardSimulationResult | None = None


def run_reconciliation(
    movement_directory: Path,
    reference_directory: Path,
    competence: date,
    cutoff_date: date,
    output_path: Path,
    *,
    evaluation_date: date | None = None,
    task_board_path: Path | None = None,
) -> ReconciliationResult:
    """Discover inputs, reconcile their data, and write local outputs.

    When task_board_path is supplied, underpaid companies are processed by the
    persistent local task-board simulator after the Excel report is generated.
    """
    if (cutoff_date.year, cutoff_date.month) != (competence.year, competence.month):
        raise ValueError("Cutoff date must belong to the requested competence.")

    evaluation = cutoff_date if evaluation_date is None else evaluation_date
    if evaluation < cutoff_date:
        raise ValueError("Evaluation date cannot precede the cutoff date.")

    movement_file = discover_movement_workbook(movement_directory, competence)
    reference_file = discover_reference_workbook(reference_directory, competence)

    destination = Path(output_path)
    if destination.resolve() in {movement_file.resolve(), reference_file.resolve()}:
        raise ValueError("Output path must not overwrite an input workbook.")

    movement_records = read_movement_workbook(movement_file)
    reference = read_reference_workbook(reference_file)
    movements = consolidate_releases(movement_records, cutoff_date)

    report = compare_companies(
        reference.companies,
        movements,
        cutoff_date,
        evaluation,
    )
    output_workbook = write_comparison_report(report, destination)

    task_board_result = None
    if task_board_path is not None:
        board = LocalTaskBoard(task_board_path)
        task_board_result = create_underpaid_tasks(report, competence, board)

    return ReconciliationResult(
        movement_workbook=movement_file,
        reference_workbook=reference_file,
        report=report,
        output_workbook=output_workbook,
        task_board_result=task_board_result,
    )
