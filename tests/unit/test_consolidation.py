from datetime import date

import pytest

from operations_reconciliation.domain.models import ReleaseRecord
from operations_reconciliation.services.consolidation import consolidate_releases


def test_consolidates_released_records_by_normalized_company() -> None:
    records = [
        ReleaseRecord("Ácme Ltda.", date(2026, 5, 4), 10, load_type="Vida"),
        ReleaseRecord("ACME LTDA", date(2026, 5, 9), 15, load_type="Carga"),
        ReleaseRecord("Other Co", date(2026, 5, 6), 4),
    ]

    result = consolidate_releases(records, date(2026, 5, 10))

    acme = next(item for item in result if item.company_key == "ACME LTDA")
    assert acme.quantity_released == 25
    assert acme.released_days == (4, 9)
    assert acme.first_release == date(2026, 5, 4)
    assert acme.last_release == date(2026, 5, 9)
    assert acme.released_records == 2
    assert acme.load_types == ("Carga", "Vida")


def test_ignores_non_released_rows() -> None:
    records = [ReleaseRecord("Acme", date(2026, 5, 4), 10, status="PENDENTE")]
    assert consolidate_releases(records, date(2026, 5, 10)) == ()


def test_ignores_blank_nan_and_total_contracts() -> None:
    records = [
        ReleaseRecord("", date(2026, 5, 4), 10),
        ReleaseRecord("nan", date(2026, 5, 4), 10),
        ReleaseRecord("TOTAL", date(2026, 5, 4), 10),
    ]
    assert consolidate_releases(records, date(2026, 5, 10)) == ()


def test_ignores_records_outside_cutoff_month_and_future_records() -> None:
    records = [
        ReleaseRecord("Acme", date(2026, 4, 30), 10),
        ReleaseRecord("Acme", date(2026, 5, 11), 20),
        ReleaseRecord("Acme", date(2026, 5, 10), 5),
    ]
    result = consolidate_releases(records, date(2026, 5, 10))
    assert len(result) == 1
    assert result[0].quantity_released == 5


def test_rejects_contract_that_normalizes_to_empty() -> None:
    records = [ReleaseRecord("!!!", date(2026, 5, 4), 10)]
    with pytest.raises(ValueError, match="cannot be normalized"):
        consolidate_releases(records, date(2026, 5, 10))


@pytest.mark.parametrize("quantity", [float("nan"), float("inf"), -1.0])
def test_rejects_invalid_release_quantities(quantity: float) -> None:
    records = [ReleaseRecord("Acme", date(2026, 5, 4), quantity)]
    with pytest.raises(ValueError, match="finite, non-negative"):
        consolidate_releases(records, date(2026, 5, 10))
