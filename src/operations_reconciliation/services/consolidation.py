"""Filtering and aggregation of released operational records."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from operations_reconciliation.domain.models import CompanyMovement, ReleaseRecord
from operations_reconciliation.services.normalization import normalize_company

_IGNORED_CONTRACTS = {"", "nan", "total"}


def consolidate_releases(
    records: list[ReleaseRecord] | tuple[ReleaseRecord, ...],
    cutoff_date: date,
) -> tuple[CompanyMovement, ...]:
    """Aggregate LIBERADO rows from the cutoff month's first day through the cutoff date.

    Non-released rows, empty/summary contracts, and records outside the cutoff window are
    ignored. A released row with a non-finite or negative quantity or an unusable company
    name raises ValueError rather than silently corrupting totals.
    """
    grouped: dict[str, list[ReleaseRecord]] = defaultdict(list)
    start_date = date(cutoff_date.year, cutoff_date.month, 1)

    for record in records:
        if record.status.strip().casefold() != "liberado":
            continue
        if not start_date <= record.release_date <= cutoff_date:
            continue

        company_display = record.contract.strip()
        if company_display.casefold() in _IGNORED_CONTRACTS:
            continue

        company_key = normalize_company(company_display)
        if not company_key:
            raise ValueError("A released record contains a contract that cannot be normalized.")
        if not math.isfinite(record.quantity) or record.quantity < 0:
            raise ValueError("Released quantity must be a finite, non-negative number.")

        grouped[company_key].append(record)

    movements: list[CompanyMovement] = []
    for company_key, company_records in grouped.items():
        ordered = sorted(company_records, key=lambda item: item.release_date)
        movements.append(
            CompanyMovement(
                company_key=company_key,
                company=ordered[0].contract.strip(),
                quantity_released=sum(item.quantity for item in company_records),
                released_days=tuple(sorted({item.release_date.day for item in company_records})),
                first_release=ordered[0].release_date,
                last_release=ordered[-1].release_date,
                released_records=len(company_records),
                load_types=tuple(sorted({(record.load_type or "Não informado").strip() for record in company_records})),
            )
        )

    return tuple(sorted(movements, key=lambda movement: movement.company_key))
