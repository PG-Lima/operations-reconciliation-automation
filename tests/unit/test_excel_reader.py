from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook

from operations_reconciliation.adapters.excel_reader import (
    _column_map,
    read_movement_workbook,
    read_reference_workbook,
)


def _write_movements(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    frame = pd.DataFrame(rows, columns=columns)
    frame.to_excel(path, index=False)


def _movement_row(
    *,
    company: object = "Ácme Ltda.",
    release_date: object = "04/11/2026",
    status: object = "LIBERADO",
    quantity: object = "1.234,50",
    load_type: object = "VIDA",
) -> dict[str, object]:
    return {
        "Contrato": company,
        "Data da Liberação": release_date,
        "Situação do Arquivo": status,
        "Quantidade": quantity,
        "Tipo da Carga": load_type,
    }


def _write_reference(
    path: Path,
    rows: list[list[object]],
    headers: list[str] | None = None,
    sheet_name: str = "Referencia_Principal",
) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    for row in range(1, 5):
        sheet.cell(row=row, column=1, value=f"Reference information {row}")
    sheet.append(headers or [
        "Empresa (Contrato)",
        "Quantidade consolidada (nov/2026)",
        "Dias de liberação observados",
        "Carteira",
    ])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_reads_xlsx_movement_rows_and_parses_brazilian_quantities(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(
        path,
        [
            _movement_row(quantity="1.234,50"),
            _movement_row(company="Ignored Co", status="PENDENTE", quantity="not-a-number", release_date="invalid"),
            _movement_row(company="TOTAL", quantity=999),
            _movement_row(company=None, quantity=999),
        ],
    )

    result = read_movement_workbook(path)

    assert len(result) == 1
    assert result[0].contract == "Ácme Ltda."
    assert result[0].release_date == date(2026, 11, 4)
    assert result[0].quantity == 1234.5
    assert result[0].load_type == "VIDA"
    assert result[0].status == "LIBERADO"


def test_reads_xlsm_using_openpyxl_without_executing_macros(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsm"
    _write_movements(path, [_movement_row(quantity=12.5)])

    result = read_movement_workbook(path)

    assert result[0].quantity == 12.5


def test_reads_binary_xls_using_xlrd_engine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xls"
    path.write_bytes(b"legacy xls placeholder")
    expected = pd.DataFrame([_movement_row(quantity=5)])
    calls: list[str] = []

    def fake_read_excel(source: object, *, engine: str) -> pd.DataFrame:
        calls.append(engine)
        return expected

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    result = read_movement_workbook(path)

    assert calls == ["xlrd"]
    assert result[0].quantity == 5


@pytest.mark.parametrize(
    "prefix",
    [b"<html><body>", b"<!DOCTYPE html><html><body>", b"<html xmlns:x=\"urn:schemas-microsoft-com:office:excel\">"]
)
def test_reads_html_excel_export_saved_as_xls(tmp_path: Path, prefix: bytes) -> None:
    path = tmp_path / "Planilha.xls"
    html = (
        prefix
        + b"<table><tr><th>Contrato</th><th>Data da Liberacao</th>"
        + b"<th>Situacao do Arquivo</th><th>Quantidade</th></tr>"
        + b"<tr><td>Acme</td><td>04/11/2026</td><td>LIBERADO</td><td>12,5</td></tr></table>"
        + b"</body></html>"
    )
    path.write_bytes(html)

    result = read_movement_workbook(path)

    assert result[0].contract == "Acme"
    assert result[0].release_date == date(2026, 11, 4)
    assert result[0].quantity == 12.5
    assert result[0].load_type == "Não informado"


def test_returns_empty_tuple_when_workbook_has_no_released_rows(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [_movement_row(status="PENDENTE")])

    assert read_movement_workbook(path) == ()


def test_uses_default_load_type_when_optional_column_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(
        path,
        [{
            "Contrato": "Acme",
            "Data da Liberação": "04/11/2026",
            "Situação do Arquivo": "LIBERADO",
            "Quantidade": 10,
        }],
    )

    result = read_movement_workbook(path)

    assert result[0].load_type == "Não informado"


def test_uses_default_load_type_when_optional_cell_is_blank(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [_movement_row(load_type=None)])

    result = read_movement_workbook(path)

    assert result[0].load_type == "Não informado"


def test_rejects_missing_movement_columns(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [{"Contrato": "Acme", "Quantidade": 10}])

    with pytest.raises(ValueError, match="missing required columns"):
        read_movement_workbook(path)


def test_rejects_ambiguous_duplicate_normalized_movement_columns(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(
        path,
        [["Acme", "04/11/2026", "LIBERADO", 10, 11]],
        columns=[
            "Contrato", "Data da Liberação", "Situação do Arquivo", "Quantidade", " QUANTIDADE "
        ],
    )

    with pytest.raises(ValueError, match="ambiguous duplicate column"):
        read_movement_workbook(path)


@pytest.mark.parametrize("quantity", [None, "", "abc", -1, float("inf"), True])
def test_rejects_invalid_released_quantities(tmp_path: Path, quantity: object) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [_movement_row(quantity=quantity)])

    with pytest.raises(ValueError, match="quantity"):
        read_movement_workbook(path)


def test_rejects_invalid_release_date(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [_movement_row(release_date="not a date")])

    with pytest.raises(ValueError, match="invalid release date"):
        read_movement_workbook(path)


def test_rejects_contract_that_cannot_be_normalized(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xlsx"
    _write_movements(path, [_movement_row(company="!!!")])

    with pytest.raises(ValueError, match="cannot be normalized"):
        read_movement_workbook(path)


def test_rejects_html_excel_without_a_readable_table(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xls"
    path.write_text("<!doctype html><html><body>no data table</body></html>", encoding="utf-8")

    with pytest.raises(ValueError, match="does not contain a readable table"):
        read_movement_workbook(path)


def test_rejects_missing_source_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        read_movement_workbook(tmp_path / "missing.xlsx")


def test_rejects_directory_as_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a file"):
        read_movement_workbook(tmp_path)


def test_rejects_empty_source_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.xlsx"
    path.write_bytes(b"")

    with pytest.raises(ValueError, match="empty"):
        read_movement_workbook(path)


def test_rejects_unsupported_movement_extension(tmp_path: Path) -> None:
    path = tmp_path / "movements.csv"
    path.write_text("company,quantity\nAcme,10", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        read_movement_workbook(path)


def test_rejects_corrupted_xlsx_workbook(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.xlsx"
    path.write_bytes(b"not an excel workbook")

    with pytest.raises(ValueError, match="Could not read movement workbook"):
        read_movement_workbook(path)


def test_reads_reference_workbook_and_extracts_competence(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(
        path,
        [
            ["Ácme Ltda.", 100, "05, 10, 15", "Corporate"],
            ["Beta Ltda.", "invalid", None, "Retail"],
            ["Gamma Ltda.", None, "20", "Retail"],
            ["TOTAL", 100, "31", ""],
            [None, 20, "20", ""],
        ],
    )

    result = read_reference_workbook(path)

    assert result.competence == date(2026, 11, 1)
    assert len(result.companies) == 3
    assert result.companies[0].company == "Ácme Ltda."
    assert result.companies[0].expected_quantity == 100.0
    assert result.companies[0].scheduled_days == "05, 10, 15"
    assert result.companies[1].expected_quantity is None
    assert result.companies[1].scheduled_days == ""
    assert result.companies[2].expected_quantity is None


def test_reads_reference_without_optional_portfolio_column(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(
        path,
        [["Acme", 10, "10, 20"]],
        headers=[
            "Empresa (Contrato)",
            "Quantidade consolidada (out/2026)",
            "Dias de liberação observados",
        ],
    )

    result = read_reference_workbook(path)

    assert result.competence == date(2026, 10, 1)
    assert len(result.companies) == 1
    assert result.companies[0].company == "Acme"


def test_reference_competence_is_none_when_header_has_no_month(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(
        path,
        [["Acme", 10, "10"]],
        headers=["Empresa", "Quantidade consolidada", "Dias de liberação observados"],
    )

    assert read_reference_workbook(path).competence is None


def test_reference_competence_is_none_for_unknown_month_abbreviation(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(
        path,
        [["Acme", 10, "10"]],
        headers=["Empresa", "Quantidade consolidada (xyz/2026)", "Dias de liberação observados"],
    )

    assert read_reference_workbook(path).competence is None


def test_rejects_non_positive_reference_header_row(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["Acme", 10, "10"]])

    with pytest.raises(ValueError, match="positive one-based"):
        read_reference_workbook(path, header_row=0)


def test_rejects_missing_reference_columns(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["Acme", 10]], headers=["Empresa", "Quantidade consolidada (nov/2026)"])

    with pytest.raises(ValueError, match="must contain Empresa"):
        read_reference_workbook(path)


def test_rejects_ambiguous_reference_prefix_columns(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(
        path,
        [["Acme", 10, 10, 10]],
        headers=[
            "Empresa (Contrato)", "Quantidade consolidada (nov/2026)",
            "Dias de liberação observados", "Carteira principal",
        ],
    )
    # A second column sharing the same required prefix is ambiguous.
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Referencia_Principal"
    for row in range(1, 5):
        sheet.cell(row=row, column=1, value=f"Info {row}")
    sheet.append([
        "Empresa (Contrato)", "Quantidade consolidada (nov/2026)",
        "Quantidade consolidada ajustada", "Dias de liberação observados",
    ])
    sheet.append(["Acme", 10, 10, "10"])
    workbook.save(path)

    with pytest.raises(ValueError, match="multiple columns beginning with 'quantidade consolidada'"):
        read_reference_workbook(path)


def test_rejects_duplicate_companies_after_normalization(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["Ácme Ltda.", 10, "10", ""], ["ACME LTDA", 20, "20", ""]])

    with pytest.raises(ValueError, match="duplicate company after normalization"):
        read_reference_workbook(path)


def test_rejects_reference_company_that_cannot_be_normalized(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["!!!", 10, "10", ""]])

    with pytest.raises(ValueError, match="cannot be normalized"):
        read_reference_workbook(path)


def test_rejects_reference_with_no_valid_company_rows(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["TOTAL", 10, "10", ""], [None, 20, "20", ""]])

    with pytest.raises(ValueError, match="does not contain any valid company rows"):
        read_reference_workbook(path)


def test_rejects_reference_with_unknown_sheet(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, [["Acme", 10, "10", ""]])

    with pytest.raises(ValueError, match="Could not read reference sheet"):
        read_reference_workbook(path, sheet_name="Missing")


def test_rejects_unsupported_reference_extension(tmp_path: Path) -> None:
    path = tmp_path / "reference.xls"
    path.write_bytes(b"not supported")

    with pytest.raises(ValueError, match="Unsupported file extension"):
        read_reference_workbook(path)


def test_rejects_corrupted_reference_workbook(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    path.write_bytes(b"not an xlsx")

    with pytest.raises(ValueError, match="Could not read reference sheet"):
        read_reference_workbook(path)


def test_column_map_ignores_blank_headers() -> None:
    assert _column_map(["Contrato", "   "]) == {"contrato": "Contrato"}


def test_read_html_excel_empty_table_list_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "Planilha.xls"
    path.write_text("<html><body>placeholder</body></html>", encoding="utf-8")
    monkeypatch.setattr(pd, "read_html", lambda *args, **kwargs: [])

    with pytest.raises(ValueError, match="does not contain a readable table"):
        read_movement_workbook(path)


def test_html_movement_rejects_empty_quantity_string(tmp_path: Path) -> None:
    path = tmp_path / "Planilha.xls"
    path.write_text(
        "<html><table><tr><th>Contrato</th><th>Data da Liberacao</th>"
        "<th>Situacao do Arquivo</th><th>Quantidade</th></tr>"
        "<tr><td>Acme</td><td>04/11/2026</td><td>LIBERADO</td><td></td></tr>"
        "</table></html>",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="empty quantity"):
        read_movement_workbook(path)
