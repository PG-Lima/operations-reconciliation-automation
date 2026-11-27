from datetime import date
from unittest.mock import Mock

import pytest

from operations_reconciliation.domain.models import (
    Classification,
    CompanyComparison,
    ComparisonReport,
)
from operations_reconciliation.services.task_creation import create_underpaid_tasks


def _row(company: str, classification: Classification) -> CompanyComparison:
    return CompanyComparison(
        company=company,
        expected_quantity=100.0,
        quantity_released=50.0,
        quantity_missing=50.0,
        quantity_excess=0.0,
        scheduled_days=(8,),
        last_scheduled_day=date(2026, 11, 8),
        released_days=(4,),
        first_release=date(2026, 11, 4),
        last_release=date(2026, 11, 4),
        released_records=1,
        load_types=("Carga",),
        classification=classification,
        observation="Test",
    )


def _report(rows: tuple[CompanyComparison, ...]) -> ComparisonReport:
    return ComparisonReport(
        rows=rows,
        unreferenced_companies=(),
        reference_companies=len(rows),
        companies_with_movement=len(rows),
        companies_without_movement=0,
        total_quantity_released=0.0,
        total_referenced_quantity_released=0.0,
        total_unreferenced_quantity_released=0.0,
    )


def test_creates_tasks_only_for_below_companies() -> None:
    board = Mock()
    board.create_task.side_effect = [True, False]
    report = _report(
        (
            _row("Ácme Ltda.", Classification.BELOW),
            _row("Beta Ltda.", Classification.MATCHED),
            _row("Gamma Ltda.", Classification.BELOW),
            _row("Delta Ltda.", Classification.UNPAID),
        )
    )

    result = create_underpaid_tasks(report, date(2026, 11, 1), board)

    assert result.eligible_companies == 2
    assert result.created_tasks == 1
    assert result.skipped_existing == 1
    assert result.created_titles == ("Ácme Ltda. - 2026-11",)
    assert board.create_task.call_args_list[0].kwargs == {
        "company_key": "ACME LTDA",
        "competence": date(2026, 11, 1),
    }
    assert board.create_task.call_args_list[1].kwargs == {
        "company_key": "GAMMA LTDA",
        "competence": date(2026, 11, 1),
    }


def test_returns_empty_result_when_no_company_is_below() -> None:
    board = Mock()
    report = _report(
        (
            _row("ACME", Classification.MATCHED),
            _row("Beta", Classification.UNPAID),
        )
    )

    result = create_underpaid_tasks(report, date(2026, 11, 1), board)

    assert result.eligible_companies == 0
    assert result.created_tasks == 0
    assert result.skipped_existing == 0
    assert result.created_titles == ()
    board.create_task.assert_not_called()


def test_rejects_below_company_that_cannot_be_normalized() -> None:
    board = Mock()
    report = _report((_row("!!!", Classification.BELOW),))

    with pytest.raises(ValueError, match="cannot be normalized"):
        create_underpaid_tasks(report, date(2026, 11, 1), board)

    board.create_task.assert_not_called()
