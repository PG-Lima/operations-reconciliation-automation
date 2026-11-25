from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

from operations_reconciliation.adapters.excel_report import write_comparison_report
from operations_reconciliation.domain.models import (
    Classification,
    CompanyComparison,
    CompanyMovement,
    ComparisonReport,
)


def _comparison(
    company: str,
    classification: Classification,
    quantity_released: float,
) -> CompanyComparison:
    expected = 100.0
    return CompanyComparison(
        company=company,
        expected_quantity=expected,
        quantity_released=quantity_released,
        quantity_missing=max(expected - quantity_released, 0.0),
        quantity_excess=max(quantity_released - expected, 0.0),
        scheduled_days=(5, 10),
        last_scheduled_day=date(2026, 11, 10),
        released_days=(4, 9) if quantity_released else (),
        first_release=date(2026, 11, 4) if quantity_released else None,
        last_release=date(2026, 11, 9) if quantity_released else None,
        released_records=2 if quantity_released else 0,
        load_types=("Carga", "Vida") if quantity_released else (),
        classification=classification,
        observation=f"Observation for {company}.",
    )


def _new_company() -> CompanyMovement:
    return CompanyMovement(
        company_key="NEW COMPANY",
        company="New Company",
        quantity_released=25.0,
        released_days=(12,),
        first_release=date(2026, 11, 12),
        last_release=date(2026, 11, 12),
        released_records=1,
        load_types=("Vida",),
    )


def _report() -> ComparisonReport:
    rows = (
        _comparison("Waiting Co", Classification.WAITING, 50.0),
        _comparison("Below Co", Classification.BELOW, 70.0),
        _comparison("Matched Co", Classification.MATCHED, 100.0),
        _comparison("Above Co", Classification.ABOVE, 120.0),
        _comparison("Unpaid Co", Classification.UNPAID, 0.0),
    )
    return ComparisonReport(
        rows=rows,
        unreferenced_companies=(_new_company(),),
        reference_companies=5,
        companies_with_movement=4,
        companies_without_movement=1,
        total_quantity_released=365.0,
        total_referenced_quantity_released=340.0,
        total_unreferenced_quantity_released=25.0,
    )


def test_writes_report_with_the_seven_expected_worksheets(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "comparison.xlsx"

    result = write_comparison_report(_report(), output_path)

    assert result == output_path
    assert output_path.is_file()

    workbook = load_workbook(output_path, read_only=True)
    assert workbook.sheetnames == [
        "Resumo",
        "Aguardando",
        "Menor",
        "Igual",
        "Maior",
        "Não pagou",
        "Novas empresas",
    ]
    workbook.close()


def test_summary_contains_company_counts_quantities_and_classifications(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.xlsx"
    write_comparison_report(_report(), output_path)

    workbook = load_workbook(output_path, data_only=True, read_only=True)
    summary = workbook["Resumo"]
    values = {row[0]: row[1] for row in summary.iter_rows(min_row=2, values_only=True)}

    assert values["Empresas na referência"] == 5
    assert values["Empresas com movimentação"] == 4
    assert values["Empresas sem movimentação"] == 1
    assert values["Total liberado"] == 365.0
    assert values["Total liberado — referenciadas"] == 340.0
    assert values["Total liberado — novas empresas"] == 25.0
    assert values["Novas empresas"] == 1
    assert values["Classificação — Aguardando"] == 1
    assert values["Classificação — Menor"] == 1
    assert values["Classificação — Igual"] == 1
    assert values["Classificação — Maior"] == 1
    assert values["Classificação — Não pagou"] == 1
    workbook.close()


@pytest.mark.parametrize(
    ("sheet_name", "expected_company"),
    [
        ("Aguardando", "Waiting Co"),
        ("Menor", "Below Co"),
        ("Igual", "Matched Co"),
        ("Maior", "Above Co"),
        ("Não pagou", "Unpaid Co"),
    ],
)
def test_classification_worksheets_only_contain_their_own_companies(
    tmp_path: Path,
    sheet_name: str,
    expected_company: str,
) -> None:
    output_path = tmp_path / "comparison.xlsx"
    write_comparison_report(_report(), output_path)

    workbook = load_workbook(output_path, data_only=True, read_only=True)
    worksheet = workbook[sheet_name]
    rows = list(worksheet.iter_rows(values_only=True))

    assert rows[0][0] == "Empresa"
    assert [row[0] for row in rows[1:]] == [expected_company]
    workbook.close()


def test_new_companies_worksheet_contains_unreferenced_movements(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.xlsx"
    write_comparison_report(_report(), output_path)

    workbook = load_workbook(output_path, data_only=True, read_only=True)
    worksheet = workbook["Novas empresas"]
    rows = list(worksheet.iter_rows(values_only=True))

    assert rows[0] == (
        "Empresa",
        "Quantidade liberada",
        "Dias liberados",
        "Primeira liberação",
        "Última liberação",
        "Registros liberados",
        "Tipos de carga",
    )
    assert rows[1][0] == "New Company"
    assert rows[1][1] == 25.0
    assert rows[1][2] == "12"
    assert rows[1][5] == 1
    assert rows[1][6] == "Vida"
    workbook.close()


def test_rejects_output_paths_that_are_not_xlsx(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"\.xlsx"):
        write_comparison_report(_report(), tmp_path / "comparison.csv")
