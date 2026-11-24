"""Typed domain objects for release reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Classification(StrEnum):
    """Business classification assigned after the scheduled deadline."""

    WAITING = "Aguardando"
    BELOW = "Menor"
    MATCHED = "Igual"
    ABOVE = "Maior"
    UNPAID = "Não pagou"
    UNREFERENCED = "Sem referência"


@dataclass(frozen=True, slots=True)
class ReferenceCompany:
    """Expected monthly quantity and scheduled release days for one company."""

    company: str
    expected_quantity: float | None
    scheduled_days: str


@dataclass(frozen=True, slots=True)
class ReferenceWorkbook:
    """Validated companies and the optional competence parsed from a reference workbook."""

    companies: tuple[ReferenceCompany, ...]
    competence: date | None


@dataclass(frozen=True, slots=True)
class ReleaseRecord:
    """One row from an operational movement export."""

    contract: str
    release_date: date
    quantity: float
    status: str = "LIBERADO"
    load_type: str = "Não informado"


@dataclass(frozen=True, slots=True)
class CompanyMovement:
    """Aggregated releases for one normalized company key."""

    company_key: str
    company: str
    quantity_released: float
    released_days: tuple[int, ...]
    first_release: date
    last_release: date
    released_records: int
    load_types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompanyComparison:
    """Comparison result for a company present in the monthly reference."""

    company: str
    expected_quantity: float | None
    quantity_released: float
    quantity_missing: float
    quantity_excess: float
    scheduled_days: tuple[int, ...]
    last_scheduled_day: date | None
    released_days: tuple[int, ...]
    first_release: date | None
    last_release: date | None
    released_records: int
    load_types: tuple[str, ...]
    classification: Classification
    observation: str


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    """Complete comparison output, including companies absent from the reference."""

    rows: tuple[CompanyComparison, ...]
    unreferenced_companies: tuple[CompanyMovement, ...]
    reference_companies: int
    companies_with_movement: int
    companies_without_movement: int
    total_quantity_released: float
    total_referenced_quantity_released: float
    total_unreferenced_quantity_released: float
