from datetime import date

import pytest

from operations_reconciliation.domain.models import (
    Classification,
    CompanyMovement,
    ReferenceCompany,
)
from operations_reconciliation.services.comparison import compare_companies


def movement(company: str, quantity: float, key: str | None = None) -> CompanyMovement:
    return CompanyMovement(
        company_key=key or company.upper(),
        company=company,
        quantity_released=quantity,
        released_days=(5,),
        first_release=date(2026, 5, 5),
        last_release=date(2026, 5, 5),
        released_records=1,
        load_types=("Vida",),
    )


def test_classifies_equal_above_below_and_unpaid_after_deadline() -> None:
    reference = [
        ReferenceCompany("Equal", 10, "05, 10"),
        ReferenceCompany("Above", 10, "05, 10"),
        ReferenceCompany("Below", 10, "05, 10"),
        ReferenceCompany("Unpaid", 10, "05, 10"),
    ]
    movements = [movement("Equal", 10), movement("Above", 12), movement("Below", 4)]

    report = compare_companies(reference, movements, date(2026, 5, 12))
    statuses = {row.company: row.classification for row in report.rows}

    assert statuses == {
        "Equal": Classification.MATCHED,
        "Above": Classification.ABOVE,
        "Below": Classification.BELOW,
        "Unpaid": Classification.UNPAID,
    }


def test_is_waiting_on_last_scheduled_day_even_when_quantity_is_above() -> None:
    report = compare_companies(
        [ReferenceCompany("Acme", 10, "05, 10")],
        [movement("Acme", 15)],
        date(2026, 5, 10),
    )
    row = report.rows[0]
    assert row.classification == Classification.WAITING
    assert "classificação continuará Aguardando" in row.observation


def test_waits_when_future_scheduled_days_remain() -> None:
    report = compare_companies(
        [ReferenceCompany("Acme", 10, "05, 15, 25")],
        [movement("Acme", 3)],
        date(2026, 5, 10),
    )
    assert report.rows[0].classification == Classification.WAITING
    assert "15, 25" in report.rows[0].observation


def test_invalid_reference_amount_or_schedule_remains_waiting() -> None:
    report = compare_companies(
        [ReferenceCompany("No amount", None, "05"), ReferenceCompany("No days", 5, "")],
        [],
        date(2026, 5, 20),
    )
    assert all(row.classification == Classification.WAITING for row in report.rows)
    assert all("Revisar referência" in row.observation for row in report.rows)


def test_caps_scheduled_day_to_last_calendar_day_of_month() -> None:
    report = compare_companies(
        [ReferenceCompany("Acme", 10, "31")],
        [],
        date(2026, 2, 28),
    )
    row = report.rows[0]
    assert row.last_scheduled_day == date(2026, 2, 28)
    assert row.classification == Classification.WAITING


def test_splits_unreferenced_companies_and_computes_totals() -> None:
    report = compare_companies(
        [ReferenceCompany("Known", 10, "05")],
        [movement("Known", 7), movement("New", 8)],
        date(2026, 5, 10),
    )
    assert report.reference_companies == 1
    assert report.companies_with_movement == 1
    assert report.companies_without_movement == 0
    assert report.total_quantity_released == 15
    assert report.total_referenced_quantity_released == 7
    assert report.total_unreferenced_quantity_released == 8
    assert [item.company for item in report.unreferenced_companies] == ["New"]


def test_preserves_reference_companies_without_movements() -> None:
    report = compare_companies(
        [ReferenceCompany("No movement", 10, "05"), ReferenceCompany("With movement", 4, "05")],
        [movement("With movement", 4)],
        date(2026, 5, 10),
    )
    assert report.companies_without_movement == 1
    assert report.rows[0].classification == Classification.UNPAID


def test_rejects_duplicate_reference_company_after_normalization() -> None:
    reference = [ReferenceCompany("São João", 10, "05"), ReferenceCompany("SAO JOAO", 20, "10")]
    with pytest.raises(ValueError, match="duplicate company"):
        compare_companies(reference, [], date(2026, 5, 20))


def test_rejects_duplicate_movement_keys() -> None:
    movements = [movement("Acme", 2), movement("Other", 3, key="ACME")]
    with pytest.raises(ValueError, match="duplicate normalized company keys"):
        compare_companies([ReferenceCompany("Acme", 10, "05")], movements, date(2026, 5, 20))


def test_comparison_uses_explicit_evaluation_date_for_month_close() -> None:
    report = compare_companies(
        [ReferenceCompany("Acme", 10, "31")],
        [],
        date(2026, 5, 28),
        evaluation_date=date(2026, 6, 1),
    )
    assert report.rows[0].classification == Classification.UNPAID


def test_rejects_reference_company_that_normalizes_to_empty() -> None:
    with pytest.raises(ValueError, match="cannot be normalized"):
        compare_companies([ReferenceCompany("!!!", 10, "05")], [], date(2026, 5, 20))


@pytest.mark.parametrize("expected", [float("nan"), float("inf"), -1.0])
def test_non_finite_or_negative_expected_quantity_remains_waiting(expected: float) -> None:
    report = compare_companies(
        [ReferenceCompany("Acme", expected, "05")],
        [],
        date(2026, 5, 20),
    )
    assert report.rows[0].classification == Classification.WAITING
