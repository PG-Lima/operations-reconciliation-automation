"""Reference-to-movement comparison rules."""

from __future__ import annotations

import calendar
import math
from datetime import date

from operations_reconciliation.domain.models import (
    Classification,
    CompanyComparison,
    CompanyMovement,
    ComparisonReport,
    ReferenceCompany,
)
from operations_reconciliation.services.normalization import (
    normalize_company,
    parse_scheduled_days,
)

_FLOAT_TOLERANCE = 1e-9


def _validate_reference(reference: list[ReferenceCompany] | tuple[ReferenceCompany, ...]) -> dict[str, ReferenceCompany]:
    indexed: dict[str, ReferenceCompany] = {}
    for company in reference:
        key = normalize_company(company.company)
        if not key:
            raise ValueError("Reference contains a company name that cannot be normalized.")
        if key in indexed:
            raise ValueError(f"Reference contains duplicate company after normalization: {company.company}")
        indexed[key] = company
    return indexed


def _effective_scheduled_days(days: tuple[int, ...], year: int, month: int) -> tuple[int, ...]:
    last_calendar_day = calendar.monthrange(year, month)[1]
    return tuple(sorted({min(day, last_calendar_day) for day in days}))


def _classify(
    expected: float | None,
    released: float,
    last_deadline: date | None,
    evaluation_date: date,
    future_days: tuple[int, ...],
) -> tuple[Classification, str]:
    if (expected is None or not math.isfinite(expected) or expected < 0 or last_deadline is None):
        return (
            Classification.WAITING,
            "Revisar referência: quantidade esperada ou dias previstos ausentes/inválidos.",
        )

    if evaluation_date <= last_deadline:
        if future_days:
            note = "Ainda há dia(s) previsto(s) por ocorrer: " + ", ".join(
                f"{day:02d}" for day in future_days
            )
        else:
            note = "Último dia previsto é hoje; a comparação será feita a partir do próximo dia."

        if released > expected:
            note += (
                f" A quantidade já está {released - expected:g} acima da referência, "
                "mas a classificação continuará Aguardando até o dia seguinte "
                "ao último dia previsto; depois será classificada como Maior."
            )
        return Classification.WAITING, note

    if abs(released - expected) < _FLOAT_TOLERANCE:
        return Classification.MATCHED, "Quantidade liberada igual à referência."
    if released > expected:
        return (
            Classification.ABOVE,
            "Quantidade acima da referência; registrar para a próxima referência mensal, sem alterar a atual.",
        )
    if released == 0:
        return (
            Classification.UNPAID,
            "Prazo encerrado e nenhuma liberação encontrada na competência.",
        )
    return Classification.BELOW, "Prazo encerrado e quantidade liberada abaixo da referência."


def compare_companies(
    reference: list[ReferenceCompany] | tuple[ReferenceCompany, ...],
    movements: list[CompanyMovement] | tuple[CompanyMovement, ...],
    cutoff_date: date,
    evaluation_date: date | None = None,
) -> ComparisonReport:
    """Compare all reference companies and keep unmatched movements separately."""
    evaluation = evaluation_date or cutoff_date
    indexed_reference = _validate_reference(reference)
    indexed_movements = {movement.company_key: movement for movement in movements}
    if len(indexed_movements) != len(movements):
        raise ValueError("Movement data contains duplicate normalized company keys.")

    rows: list[CompanyComparison] = []
    for key, company in indexed_reference.items():
        movement = indexed_movements.get(key)
        expected = company.expected_quantity
        released = movement.quantity_released if movement else 0.0
        scheduled_days = parse_scheduled_days(company.scheduled_days)
        effective_days = _effective_scheduled_days(scheduled_days, cutoff_date.year, cutoff_date.month)
        last_deadline = (
            date(cutoff_date.year, cutoff_date.month, max(effective_days))
            if effective_days else None
        )
        future_days = tuple(
            day for day in effective_days
            if date(cutoff_date.year, cutoff_date.month, day) > evaluation
        )
        classification, observation = _classify(
            expected, released, last_deadline, evaluation, future_days
        )
        rows.append(
            CompanyComparison(
                company=company.company,
                expected_quantity=expected,
                quantity_released=released,
                quantity_missing=max((expected or 0.0) - released, 0.0),
                quantity_excess=max(released - (expected or 0.0), 0.0),
                scheduled_days=scheduled_days,
                last_scheduled_day=last_deadline,
                released_days=movement.released_days if movement else (),
                first_release=movement.first_release if movement else None,
                last_release=movement.last_release if movement else None,
                released_records=movement.released_records if movement else 0,
                load_types=movement.load_types if movement else (),
                classification=classification,
                observation=observation,
            )
        )

    unreferenced = tuple(
        movement for movement in movements if movement.company_key not in indexed_reference
    )
    companies_with_movement = sum(row.released_records > 0 for row in rows)
    referenced_movements = [movement for key, movement in indexed_movements.items() if key in indexed_reference]

    return ComparisonReport(
        rows=tuple(rows),
        unreferenced_companies=unreferenced,
        reference_companies=len(indexed_reference),
        companies_with_movement=companies_with_movement,
        companies_without_movement=len(indexed_reference) - companies_with_movement,
        total_quantity_released=sum(movement.quantity_released for movement in movements),
        total_referenced_quantity_released=sum(
            movement.quantity_released for movement in referenced_movements
        ),
        total_unreferenced_quantity_released=sum(
            movement.quantity_released for movement in unreferenced
        ),
    )
