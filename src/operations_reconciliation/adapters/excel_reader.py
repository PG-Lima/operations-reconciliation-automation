"""Read operational movement exports and monthly reference workbooks.

The adapter intentionally converts spreadsheet rows into typed domain records. Business
rules remain in the service layer; this module is responsible for file formats, headers,
and validating values needed to construct those records.
"""

from __future__ import annotations

import math
import re
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from io import BytesIO, StringIO
from numbers import Real
from pathlib import Path
from typing import Final

import pandas as pd

from operations_reconciliation.domain.models import (
    ReferenceCompany,
    ReferenceWorkbook,
    ReleaseRecord,
)
from operations_reconciliation.services.normalization import normalize_company, normalize_text

SUPPORTED_MOVEMENT_EXTENSIONS: Final = {".xls", ".xlsx", ".xlsm"}
SUPPORTED_REFERENCE_EXTENSIONS: Final = {".xlsx", ".xlsm"}
DEFAULT_REFERENCE_SHEET: Final = "Referencia_Principal"
DEFAULT_REFERENCE_HEADER_ROW: Final = 5

_MONTH_NUMBERS: Final = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}
_IGNORED_COMPANIES: Final = {"", "nan", "total"}
_REQUIRED_MOVEMENT_COLUMNS: Final = (
    "contrato",
    "data da liberacao",
    "situacao do arquivo",
    "quantidade",
)


@dataclass(frozen=True, slots=True)
class _SourceFile:
    path: Path
    content: bytes
    extension: str


def _read_source_file(path: Path, allowed_extensions: set[str]) -> _SourceFile:
    """Read a non-empty supported file without relying on the current working directory."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Source path is not a file: {source}")

    extension = source.suffix.casefold()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"Unsupported file extension '{extension}'. Supported: {allowed}.")

    content = source.read_bytes()
    if not content:
        raise ValueError("Source file is empty.")
    return _SourceFile(path=source, content=content, extension=extension)


def _is_html_excel(content: bytes) -> bool:
    """Detect the legacy HTML table format sometimes exported with an .xls suffix."""
    prefix = content[:1000].lstrip().lower()
    return (
        prefix.startswith(b"<html")
        or prefix.startswith(b"<!doctype html")
        or b"urn:schemas-microsoft-com:office:excel" in prefix
    )


def _read_movement_dataframe(source: _SourceFile) -> pd.DataFrame:
    if _is_html_excel(source.content):
        text = source.content.decode("utf-8-sig", errors="replace")
        try:
            tables = pd.read_html(
                StringIO(text),
                flavor="lxml",
                header=0,
                keep_default_na=False,
                decimal=",",
                thousands=".",
            )
        except ValueError as error:
            raise ValueError("HTML Excel export does not contain a readable table.") from error
        if not tables:
            raise ValueError("HTML Excel export does not contain a readable table.")
        return tables[0]

    if source.extension == ".xls":
        engine = "xlrd"
    else:
        # openpyxl reads .xlsx and .xlsm data without executing workbook macros.
        engine = "openpyxl"

    try:
        return pd.read_excel(BytesIO(source.content), engine=engine)
    except (ImportError, OSError, ValueError, zipfile.BadZipFile) as error:
        raise ValueError(
            f"Could not read movement workbook ({type(error).__name__})."
        ) from error


def _column_map(columns: Iterable[object]) -> dict[str, object]:
    """Map normalized column labels and reject ambiguous duplicate labels."""
    mapping: dict[str, object] = {}
    for original in columns:
        normalized = normalize_text(original)
        if not normalized:
            continue
        if normalized in mapping:
            raise ValueError(f"Spreadsheet contains ambiguous duplicate column: {original!r}.")
        mapping[normalized] = original
    return mapping


def _missing(value: object) -> bool:
    result = pd.isna(value)
    return bool(result) if not hasattr(result, "__len__") else False


def _text_value(value: object, default: str = "") -> str:
    if _missing(value):
        return default
    return str(value).strip()


def _parse_quantity(value: object, row_number: int) -> float:
    """Parse numeric cells and Brazilian numeric strings for released movement rows."""
    if _missing(value):
        raise ValueError(f"Released movement row {row_number} has an empty quantity.")
    if isinstance(value, bool):
        raise ValueError(f"Released movement row {row_number} has an invalid quantity.")

    if isinstance(value, Real):
        quantity = float(value)
    else:
        text = str(value).strip().replace(" ", "")
        if not text:
            raise ValueError(f"Released movement row {row_number} has an empty quantity.")
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            quantity = float(text)
        except ValueError as error:
            raise ValueError(
                f"Released movement row {row_number} has an invalid quantity: {value!r}."
            ) from error

    if not math.isfinite(quantity) or quantity < 0:
        raise ValueError(
            f"Released movement row {row_number} quantity must be finite and non-negative."
        )
    return quantity


def _parse_release_date(value: object, row_number: int) -> date:
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Released movement row {row_number} has an invalid release date: {value!r}.")
    return parsed.date()


def read_movement_workbook(path: Path) -> tuple[ReleaseRecord, ...]:
    """Read .xls/.xlsx/.xlsm movement exports or HTML-Excel files saved as .xls.

    Required headers are Contract, Release Date, File Status, and Quantity (Portuguese
    source labels are accepted regardless of accents or letter case). Load Type is optional.
    Only LIBERADO rows are converted; non-released rows are ignored before value validation.
    """
    source = _read_source_file(Path(path), SUPPORTED_MOVEMENT_EXTENSIONS)
    dataframe = _read_movement_dataframe(source)
    columns = _column_map(dataframe.columns)

    missing = [name for name in _REQUIRED_MOVEMENT_COLUMNS if name not in columns]
    if missing:
        raise ValueError(
            f"Movement workbook is missing required columns: {missing}. "
            f"Found: {list(dataframe.columns)}."
        )

    rename = {columns[name]: name for name in _REQUIRED_MOVEMENT_COLUMNS}
    load_type_column = columns.get("tipo da carga")
    if load_type_column is not None:
        rename[load_type_column] = "tipo da carga"
    normalized = dataframe.rename(columns=rename)

    records: list[ReleaseRecord] = []
    for index, row in normalized.iterrows():
        status = _text_value(row["situacao do arquivo"]).upper()
        if status != "LIBERADO":
            continue

        contract = _text_value(row["contrato"])
        if contract.casefold() in _IGNORED_COMPANIES:
            continue
        if not normalize_company(contract):
            raise ValueError(
                f"Released movement row {index + 2} has a contract name that cannot be normalized."
            )

        quantity = _parse_quantity(row["quantidade"], index + 2)
        release_date = _parse_release_date(row["data da liberacao"], index + 2)
        if load_type_column is None:
            load_type = "Não informado"
        else:
            load_type = _text_value(row["tipo da carga"], "Não informado") or "Não informado"

        records.append(
            ReleaseRecord(
                contract=contract,
                release_date=release_date,
                quantity=quantity,
                status="LIBERADO",
                load_type=load_type,
            )
        )

    return tuple(records)


def _find_prefixed_column(columns: dict[str, object], prefix: str) -> object | None:
    matches = [original for normalized, original in columns.items() if normalized.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError(f"Reference workbook contains multiple columns beginning with '{prefix}'.")
    return matches[0] if matches else None


def _parse_reference_competence(column_name: object) -> date | None:
    match = re.search(r"\(([a-z]{3})/(\d{4})\)", normalize_text(column_name))
    if not match:
        return None
    month_name, year_text = match.groups()
    month_number = _MONTH_NUMBERS.get(month_name)
    if month_number is None:
        return None
    return date(int(year_text), month_number, 1)


def _optional_expected_quantity(value: object) -> float | None:
    if _missing(value):
        return None
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed)


def read_reference_workbook(
    path: Path,
    sheet_name: str = DEFAULT_REFERENCE_SHEET,
    header_row: int = DEFAULT_REFERENCE_HEADER_ROW,
) -> ReferenceWorkbook:
    """Read the monthly reference sheet and infer its competence from the quantity header.

    The header row is one-based (5 by default). Required header prefixes are Empresa,
    Quantidade consolidada, and Dias de liberação observados. Carteira is optional, as in the
    source workbook; its values are not required by the comparison domain.
    """
    if header_row < 1:
        raise ValueError("Reference header row must be a positive one-based row number.")

    source = _read_source_file(Path(path), SUPPORTED_REFERENCE_EXTENSIONS)
    try:
        dataframe = pd.read_excel(
            BytesIO(source.content),
            sheet_name=sheet_name,
            header=header_row - 1,
            engine="openpyxl",
        )
    except (ImportError, OSError, ValueError, zipfile.BadZipFile) as error:
        raise ValueError(
            f"Could not read reference sheet '{sheet_name}' ({type(error).__name__})."
        ) from error

    columns = _column_map(dataframe.columns)
    company_column = _find_prefixed_column(columns, "empresa")
    quantity_column = _find_prefixed_column(columns, "quantidade consolidada")
    days_column = _find_prefixed_column(columns, "dias de liberacao observados")

    if company_column is None or quantity_column is None or days_column is None:
        raise ValueError(
            "Reference workbook must contain Empresa, Quantidade consolidada, "
            "and Dias de liberação observados columns."
        )

    competence = _parse_reference_competence(quantity_column)
    portfolio_column = _find_prefixed_column(columns, "carteira")
    selected_columns = [company_column, quantity_column, days_column]
    if portfolio_column is not None:
        selected_columns.append(portfolio_column)

    reference_frame = dataframe.loc[:, selected_columns].copy()
    reference_frame.columns = ["empresa", "quantidade_esperada", "dias_previstos"] + (
        ["carteira"] if portfolio_column is not None else []
    )

    companies: list[ReferenceCompany] = []
    seen_keys: set[str] = set()
    for index, row in reference_frame.iterrows():
        company = _text_value(row["empresa"])
        if company.casefold() in _IGNORED_COMPANIES:
            continue

        company_key = normalize_company(company)
        if not company_key:
            raise ValueError(
                f"Reference row {index + header_row + 1} has a company name that cannot be normalized."
            )
        if company_key in seen_keys:
            raise ValueError(
                f"Reference workbook contains duplicate company after normalization: {company}."
            )
        seen_keys.add(company_key)

        expected = _optional_expected_quantity(row["quantidade_esperada"])
        scheduled_days = _text_value(row["dias_previstos"])
        companies.append(
            ReferenceCompany(
                company=company,
                expected_quantity=expected,
                scheduled_days=scheduled_days,
            )
        )

    if not companies:
        raise ValueError("Reference workbook does not contain any valid company rows.")

    return ReferenceWorkbook(companies=tuple(companies), competence=competence)
