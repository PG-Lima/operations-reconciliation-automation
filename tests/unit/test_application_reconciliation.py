from datetime import date
from unittest.mock import Mock

import pytest

from operations_reconciliation.application import reconciliation
from operations_reconciliation.domain.models import (
    ComparisonReport,
    ReferenceWorkbook,
)


def _install_pipeline_mocks(monkeypatch, tmp_path):
    movement_file = tmp_path / "movement.xlsx"
    reference_file = tmp_path / "reference.xlsx"
    output_file = tmp_path / "report.xlsx"

    records = (object(),)
    reference = ReferenceWorkbook(
        companies=(),
        competence=date(2026, 11, 1),
    )
    movements = (object(),)
    report = ComparisonReport(
        rows=(),
        unreferenced_companies=(),
        reference_companies=0,
        companies_with_movement=0,
        companies_without_movement=0,
        total_quantity_released=0.0,
        total_referenced_quantity_released=0.0,
        total_unreferenced_quantity_released=0.0,
    )

    mocks = {
        "discover_movement": Mock(return_value=movement_file),
        "discover_reference": Mock(return_value=reference_file),
        "read_movement": Mock(return_value=records),
        "read_reference": Mock(return_value=reference),
        "consolidate": Mock(return_value=movements),
        "compare": Mock(return_value=report),
        "write": Mock(return_value=output_file),
    }

    monkeypatch.setattr(
        reconciliation,
        "discover_movement_workbook",
        mocks["discover_movement"],
    )
    monkeypatch.setattr(
        reconciliation,
        "discover_reference_workbook",
        mocks["discover_reference"],
    )
    monkeypatch.setattr(
        reconciliation,
        "read_movement_workbook",
        mocks["read_movement"],
    )
    monkeypatch.setattr(
        reconciliation,
        "read_reference_workbook",
        mocks["read_reference"],
    )
    monkeypatch.setattr(
        reconciliation,
        "consolidate_releases",
        mocks["consolidate"],
    )
    monkeypatch.setattr(
        reconciliation,
        "compare_companies",
        mocks["compare"],
    )
    monkeypatch.setattr(
        reconciliation,
        "write_comparison_report",
        mocks["write"],
    )

    return {
        "mocks": mocks,
        "movement_file": movement_file,
        "reference_file": reference_file,
        "output_file": output_file,
        "records": records,
        "reference": reference,
        "movements": movements,
        "report": report,
    }


@pytest.mark.parametrize(
    "evaluation_date",
    [None, date(2026, 11, 20)],
)
def test_runs_complete_reconciliation_pipeline(
    monkeypatch,
    tmp_path,
    evaluation_date,
):
    context = _install_pipeline_mocks(monkeypatch, tmp_path)
    competence = date(2026, 11, 1)
    cutoff_date = date(2026, 11, 15)
    effective_evaluation = evaluation_date or cutoff_date
    output_path = tmp_path / "output" / "report.xlsx"

    result = reconciliation.run_reconciliation(
        tmp_path / "movements",
        tmp_path / "references",
        competence,
        cutoff_date,
        output_path,
        evaluation_date=evaluation_date,
    )

    mocks = context["mocks"]

    mocks["discover_movement"].assert_called_once_with(
        tmp_path / "movements",
        competence,
    )
    mocks["discover_reference"].assert_called_once_with(
        tmp_path / "references",
        competence,
    )
    mocks["read_movement"].assert_called_once_with(
        context["movement_file"],
    )
    mocks["read_reference"].assert_called_once_with(
        context["reference_file"],
    )
    mocks["consolidate"].assert_called_once_with(
        context["records"],
        cutoff_date,
    )
    mocks["compare"].assert_called_once_with(
        context["reference"].companies,
        context["movements"],
        cutoff_date,
        effective_evaluation,
    )
    mocks["write"].assert_called_once_with(
        context["report"],
        output_path,
    )

    assert result.movement_workbook == context["movement_file"]
    assert result.reference_workbook == context["reference_file"]
    assert result.report is context["report"]
    assert result.output_workbook == context["output_file"]


def test_rejects_cutoff_outside_competence_before_discovery(
    monkeypatch,
    tmp_path,
):
    discover = Mock()
    monkeypatch.setattr(
        reconciliation,
        "discover_movement_workbook",
        discover,
    )

    with pytest.raises(ValueError, match="Cutoff date must belong"):
        reconciliation.run_reconciliation(
            tmp_path / "movements",
            tmp_path / "references",
            date(2026, 11, 1),
            date(2026, 12, 1),
            tmp_path / "report.xlsx",
        )

    discover.assert_not_called()


def test_rejects_evaluation_before_cutoff_before_discovery(
    monkeypatch,
    tmp_path,
):
    discover = Mock()
    monkeypatch.setattr(
        reconciliation,
        "discover_movement_workbook",
        discover,
    )

    with pytest.raises(ValueError, match="Evaluation date cannot precede"):
        reconciliation.run_reconciliation(
            tmp_path / "movements",
            tmp_path / "references",
            date(2026, 11, 1),
            date(2026, 11, 15),
            tmp_path / "report.xlsx",
            evaluation_date=date(2026, 11, 14),
        )

    discover.assert_not_called()


@pytest.mark.parametrize(
    "input_name",
    ["movement_file", "reference_file"],
)
def test_rejects_output_path_that_would_overwrite_an_input(
    monkeypatch,
    tmp_path,
    input_name,
):
    context = _install_pipeline_mocks(monkeypatch, tmp_path)
    output_path = context[input_name]

    with pytest.raises(ValueError, match="must not overwrite"):
        reconciliation.run_reconciliation(
            tmp_path / "movements",
            tmp_path / "references",
            date(2026, 11, 1),
            date(2026, 11, 15),
            output_path,
        )

    context["mocks"]["read_movement"].assert_not_called()
    context["mocks"]["read_reference"].assert_not_called()
    context["mocks"]["write"].assert_not_called()
