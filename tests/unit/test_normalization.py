from operations_reconciliation.services.normalization import (
    normalize_company,
    normalize_text,
    parse_scheduled_days,
)


def test_normalize_text_removes_accents_and_collapses_whitespace() -> None:
    assert normalize_text("  SÃO   João  ") == "sao joao"


def test_normalize_company_ignores_punctuation_and_case() -> None:
    assert normalize_company("ACME Serviços S/A") == "ACME SERVICOS S A"


def test_normalize_company_returns_empty_for_punctuation_only_name() -> None:
    assert normalize_company("--- !!!") == ""


def test_parse_scheduled_days_deduplicates_and_sorts() -> None:
    assert parse_scheduled_days("05, 10 / 05 e 20") == (5, 10, 20)


def test_parse_scheduled_days_ignores_out_of_range_values() -> None:
    assert parse_scheduled_days("0, 32, 31, 01") == (1, 31)


def test_parse_scheduled_days_handles_empty_values() -> None:
    assert parse_scheduled_days("") == ()
