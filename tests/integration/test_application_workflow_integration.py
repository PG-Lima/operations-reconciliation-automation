"""End-to-end test for the workbook-to-report and optional task-board workflow."""

from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook

from operations_reconciliation.adapters.local_task_board import LocalTaskBoard
from operations_reconciliation.application.reconciliation import run_reconciliation
from operations_reconciliation.domain.models import Classification


def test_runs_complete_workbook_to_report_and_task_board_workflow(tmp_path: Path) -> None:
    movement_directory = tmp_path / "movements"
    reference_directory = tmp_path / "references"
    movement_directory.mkdir()
    reference_directory.mkdir()

    movement_file = movement_directory / "Movimentacoes.xlsx"
    movement_workbook = Workbook()
    movement_sheet = movement_workbook.active
    movement_sheet.append(
        [
            "Contrato",
            "Data da Liberação",
            "Situação do Arquivo",
            "Quantidade",
            "Tipo da Carga",
        ]
    )
    movement_sheet.append(["Ácme Ltda.", date(2026, 11, 4), "LIBERADO", 30, "Vida"])
    movement_sheet.append(["ACME LTDA", date(2026, 11, 10), "LIBERADO", 20, "Carga"])
    movement_sheet.append(["New Company", date(2026, 11, 12), "LIBERADO", 5, "Vida"])
    movement_sheet.append(["Gamma Ltda.", date(2026, 11, 7), "LIBERADO", 5, "Vida"])
    movement_sheet.append(["Beta Ltda.", date(2026, 11, 8), "PENDENTE", 100, "Vida"])
    movement_workbook.save(movement_file)

    reference_file = reference_directory / "Referencia.xlsx"
    reference_workbook = Workbook()
    reference_sheet = reference_workbook.active
    reference_sheet.title = "Referencia_Principal"

    for row in range(1, 5):
        reference_sheet.cell(row=row, column=1, value=f"Reference metadata {row}")

    reference_sheet.append(
        [
            "Empresa (Contrato)",
            "Quantidade consolidada (nov/2026)",
            "Dias de liberação observados",
        ]
    )
    reference_sheet.append(["ACME LTDA", 50, "10"])
    reference_sheet.append(["Beta Ltda.", 20, "08"])
    reference_sheet.append(["Gamma Ltda.", 20, "08"])
    reference_workbook.save(reference_file)

    original_movement = movement_file.read_bytes()
    original_reference = reference_file.read_bytes()
    output_file = tmp_path / "reports" / "reconciliation.xlsx"
    task_board_path = tmp_path / "state" / "task-board.json"

    result = run_reconciliation(
        movement_directory=movement_directory,
        reference_directory=reference_directory,
        competence=date(2026, 11, 1),
        cutoff_date=date(2026, 11, 12),
        output_path=output_file,
        evaluation_date=date(2026, 11, 13),
        task_board_path=task_board_path,
    )

    assert result.movement_workbook == movement_file
    assert result.reference_workbook == reference_file
    assert result.output_workbook == output_file
    assert output_file.is_file()

    classifications = {row.company: row.classification for row in result.report.rows}
    assert classifications == {
        "ACME LTDA": Classification.MATCHED,
        "Beta Ltda.": Classification.UNPAID,
        "Gamma Ltda.": Classification.BELOW,
    }

    assert result.report.rows[0].quantity_released == 50
    assert len(result.report.unreferenced_companies) == 1
    assert result.report.unreferenced_companies[0].company == "New Company"
    assert result.report.total_quantity_released == 60
    assert result.report.total_referenced_quantity_released == 55
    assert result.report.total_unreferenced_quantity_released == 5

    task_result = result.task_board_result
    assert task_result is not None
    assert task_result.eligible_companies == 1
    assert task_result.created_tasks == 1
    assert task_result.skipped_existing == 0
    assert task_result.created_titles == ("Gamma Ltda. - 2026-11",)
    assert LocalTaskBoard(task_board_path).list_titles() == ("Gamma Ltda. - 2026-11",)

    repeated_result = run_reconciliation(
        movement_directory=movement_directory,
        reference_directory=reference_directory,
        competence=date(2026, 11, 1),
        cutoff_date=date(2026, 11, 12),
        output_path=output_file,
        evaluation_date=date(2026, 11, 13),
        task_board_path=task_board_path,
    )
    assert repeated_result.task_board_result is not None
    assert repeated_result.task_board_result.created_tasks == 0
    assert repeated_result.task_board_result.skipped_existing == 1
    assert LocalTaskBoard(task_board_path).list_titles() == ("Gamma Ltda. - 2026-11",)

    assert movement_file.read_bytes() == original_movement
    assert reference_file.read_bytes() == original_reference

    generated_workbook = load_workbook(output_file, read_only=True, data_only=True)
    try:
        assert generated_workbook.sheetnames == [
            "Resumo",
            "Aguardando",
            "Menor",
            "Igual",
            "Maior",
            "Não pagou",
            "Novas empresas",
        ]
        assert generated_workbook["Igual"]["A2"].value == "ACME LTDA"
        assert generated_workbook["Não pagou"]["A2"].value == "Beta Ltda."
        assert generated_workbook["Menor"]["A2"].value == "Gamma Ltda."
        assert generated_workbook["Novas empresas"]["A2"].value == "New Company"
    finally:
        generated_workbook.close()
