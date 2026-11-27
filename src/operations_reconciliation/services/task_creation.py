"""Task creation rules for the local task-board simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from operations_reconciliation.domain.models import Classification, ComparisonReport
from operations_reconciliation.services.normalization import normalize_company


class TaskBoard(Protocol):
    """Minimal port required by the underpaid-task application service."""

    def create_task(
        self,
        title: str,
        *,
        company_key: str,
        competence: date,
    ) -> bool:
        """Return True when a task is created, or False when it already exists."""
        ...


@dataclass(frozen=True, slots=True)
class TaskBoardSimulationResult:
    """Summary of one attempt to create tasks for underpaid companies."""

    eligible_companies: int
    created_tasks: int
    skipped_existing: int
    created_titles: tuple[str, ...]


def create_underpaid_tasks(
    report: ComparisonReport,
    competence: date,
    board: TaskBoard,
) -> TaskBoardSimulationResult:
    """Create one title-only task for each reference company classified as BELOW."""
    eligible = tuple(
        row for row in report.rows if row.classification == Classification.BELOW
    )
    created_titles: list[str] = []
    skipped_existing = 0

    for row in eligible:
        company_key = normalize_company(row.company)
        if not company_key:
            raise ValueError("Cannot create a task for a company that cannot be normalized.")

        title = f"{row.company} - {competence:%Y-%m}"
        if board.create_task(
            title,
            company_key=company_key,
            competence=competence,
        ):
            created_titles.append(title)
        else:
            skipped_existing += 1

    return TaskBoardSimulationResult(
        eligible_companies=len(eligible),
        created_tasks=len(created_titles),
        skipped_existing=skipped_existing,
        created_titles=tuple(created_titles),
    )
