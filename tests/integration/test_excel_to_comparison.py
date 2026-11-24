from datetime import date
from pathlib import Path

from openpyxl import Workbook

from operations_reconciliation.adapters.excel_reader import (
    read_movement_workbook,
    read_reference_workbook,
)
from operations_reconciliation.domain.models import Classification
from operations_reconciliation.services.comparison import compare_companies
from operations_reconciliation.services.consolidation import consolidate_releases


def test_excel_sources_flow_into_consolidation_and_comparison(tmp_path: Path) -> None:
    movements_path = tmp_path / "Planilha.xlsx"
    movements = Workbook()
    movement_sheet = movements.active
    movement_sheet.append([
        "Contrato", "Data da Liberação", "Situação do Arquivo", "Quantidade", "Tipo da Carga"
    ])
    movement_sheet.append(["Ácme Ltda.", date(2026, 11, 4), "LIBERADO", 30, "Vida"])
    movement_sheet.append(["ACME LTDA", date(2026, 11, 10), "LIBERADO", 20, "Carga"])
    movement_sheet.append(["New Company", date(2026, 11, 12), "LIBERADO", 5, "Vida"])
    movement_sheet.append(["Beta Ltda.", date(2026, 11, 8), "PENDENTE", 100, "Vida"])
    movements.save(movements_path)

    reference_path = tmp_path / "Referencia.xlsx"
    reference = Workbook()
    reference_sheet = reference.active
    reference_sheet.title = "Referencia_Principal"
    for row in range(1, 5):
        reference_sheet.cell(row=row, column=1, value=f"Reference metadata {row}")
    reference_sheet.append([
        "Empresa (Contrato)",
        "Quantidade consolidada (nov/2026)",
        "Dias de liberação observados",
    ])
    reference_sheet.append(["ACME LTDA", 50, "10"])
    reference_sheet.append(["Beta Ltda.", 20, "08"])
    reference.save(reference_path)

    movement_records = read_movement_workbook(movements_path)
    loaded_reference = read_reference_workbook(reference_path)
    consolidated = consolidate_releases(movement_records, date(2026, 11, 12))
    report = compare_companies(
        loaded_reference.companies,
        consolidated,
        cutoff_date=date(2026, 11, 12),
        evaluation_date=date(2026, 11, 13),
    )

    assert loaded_reference.competence == date(2026, 11, 1)
    assert len(movement_records) == 3
    assert report.rows[0].classification == Classification.MATCHED
    assert report.rows[0].quantity_released == 50
    assert report.rows[1].classification == Classification.UNPAID
    assert report.unreferenced_companies[0].company == "New Company"
    assert report.total_quantity_released == 55
    assert report.total_referenced_quantity_released == 50
    assert report.total_unreferenced_quantity_released == 5
