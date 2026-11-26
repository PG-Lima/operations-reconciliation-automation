"""Write comparison reports to a local Excel workbook."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from operations_reconciliation.domain.models import (
    Classification,
    CompanyComparison,
    CompanyMovement,
    ComparisonReport,
)

_REPORT_HEADERS = (
    "Empresa",
    "Quantidade esperada",
    "Quantidade liberada",
    "Quantidade faltante",
    "Quantidade excedente",
    "Dias previstos",
    "Último dia previsto",
    "Dias liberados",
    "Primeira liberação",
    "Última liberação",
    "Registros liberados",
    "Tipos de carga",
    "Observação",
)

_NEW_COMPANY_HEADERS = (
    "Empresa",
    "Quantidade liberada",
    "Dias liberados",
    "Primeira liberação",
    "Última liberação",
    "Registros liberados",
    "Tipos de carga",
)

_CLASSIFICATION_SHEETS = (
    ("Aguardando", Classification.WAITING),
    ("Menor", Classification.BELOW),
    ("Igual", Classification.MATCHED),
    ("Maior", Classification.ABOVE),
    ("Não pagou", Classification.UNPAID),
)

_HEADER_FILL = PatternFill(fill_type="solid", fgColor="243B53")
_HEADER_FONT = Font(color="FFFFFF", bold=True)


def _format_header(worksheet) -> None:
    for cell in worksheet[1]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.row_dimensions[1].height = 30


def _fit_columns(worksheet, minimum: int = 12, maximum: int = 48) -> None:
    for column in worksheet.columns:
        cells = tuple(column)
        longest = max(len(str(cell.value)) for cell in cells if cell.value is not None)
        width = min(max(longest + 2, minimum), maximum)
        worksheet.column_dimensions[get_column_letter(cells[0].column)].width = width


def _joined(values: tuple[object, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _comparison_values(row: CompanyComparison) -> tuple[object, ...]:
    return (
        row.company,
        row.expected_quantity,
        row.quantity_released,
        row.quantity_missing,
        row.quantity_excess,
        _joined(row.scheduled_days),
        row.last_scheduled_day,
        _joined(row.released_days),
        row.first_release,
        row.last_release,
        row.released_records,
        _joined(row.load_types),
        row.observation,
    )


def _movement_values(movement: CompanyMovement) -> tuple[object, ...]:
    return (
        movement.company,
        movement.quantity_released,
        _joined(movement.released_days),
        movement.first_release,
        movement.last_release,
        movement.released_records,
        _joined(movement.load_types),
    )


def _write_comparison_sheet(
    workbook: Workbook,
    title: str,
    rows: tuple[CompanyComparison, ...],
) -> None:
    worksheet = workbook.create_sheet(title=title)
    worksheet.append(_REPORT_HEADERS)
    for row in rows:
        worksheet.append(_comparison_values(row))

    _format_header(worksheet)
    for row in worksheet.iter_rows(min_row=2):
        for cell in row[1:5]:
            cell.number_format = '#,##0.00'
        for cell in (row[6], row[8], row[9]):
            cell.number_format = "dd/mm/yyyy"
        row[12].alignment = Alignment(wrap_text=True, vertical="top")
    _fit_columns(worksheet)


def _write_new_companies_sheet(
    workbook: Workbook,
    movements: tuple[CompanyMovement, ...],
) -> None:
    worksheet = workbook.create_sheet(title="Novas empresas")
    worksheet.append(_NEW_COMPANY_HEADERS)
    for movement in movements:
        worksheet.append(_movement_values(movement))

    _format_header(worksheet)
    for row in worksheet.iter_rows(min_row=2):
        row[1].number_format = '#,##0.00'
        row[3].number_format = "dd/mm/yyyy"
        row[4].number_format = "dd/mm/yyyy"
    _fit_columns(worksheet)


def _write_summary_sheet(workbook: Workbook, report: ComparisonReport) -> None:
    worksheet = workbook.active
    worksheet.title = "Resumo"
    worksheet.append(("Indicador", "Valor"))

    counts = Counter(row.classification for row in report.rows)
    metrics: tuple[tuple[str, int | float], ...] = (
        ("Empresas na referência", report.reference_companies),
        ("Empresas com movimentação", report.companies_with_movement),
        ("Empresas sem movimentação", report.companies_without_movement),
        ("Total liberado", report.total_quantity_released),
        ("Total liberado — referenciadas", report.total_referenced_quantity_released),
        ("Total liberado — novas empresas", report.total_unreferenced_quantity_released),
        ("Novas empresas", len(report.unreferenced_companies)),
        *(
            (f"Classificação — {classification.value}", counts.get(classification, 0))
            for _, classification in _CLASSIFICATION_SHEETS
        ),
    )
    for label, value in metrics:
        worksheet.append((label, value))

    _format_header(worksheet)
    worksheet.column_dimensions["A"].width = 42
    worksheet.column_dimensions["B"].width = 20
    for row in worksheet.iter_rows(min_row=2, min_col=2, max_col=2):
        if isinstance(row[0].value, float):
            row[0].number_format = '#,##0.00'


def write_comparison_report(report: ComparisonReport, output_path: Path) -> Path:
    """Write a seven-sheet Excel report and return its local output path.

    The report adapter only serializes an already-computed ComparisonReport. It does not
    recalculate business classifications or modify any input workbook.
    """
    destination = Path(output_path)
    if destination.suffix.casefold() != ".xlsx":
        raise ValueError("Output path must use the .xlsx extension.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    _write_summary_sheet(workbook, report)

    for sheet_name, classification in _CLASSIFICATION_SHEETS:
        selected_rows = tuple(
            row for row in report.rows if row.classification == classification
        )
        _write_comparison_sheet(workbook, sheet_name, selected_rows)

    _write_new_companies_sheet(workbook, report.unreferenced_companies)
    workbook.save(destination)
    workbook.close()
    return destination
