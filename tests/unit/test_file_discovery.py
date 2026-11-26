from datetime import date
import os
from pathlib import Path

import pytest

from operations_reconciliation.adapters import file_discovery
from operations_reconciliation.domain.models import ReferenceWorkbook, ReleaseRecord


def _movement(release_date: date) -> tuple[ReleaseRecord, ...]:
    return (ReleaseRecord("Acme", release_date, 10.0),)


def _set_modified(path: Path, timestamp: float) -> None:
    os.utime(path, (timestamp, timestamp))


def test_discovers_movement_with_latest_release_date_before_modification_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older_release = tmp_path / "older-release.xlsx"
    latest_release = tmp_path / "latest-release.xlsx"
    older_release.touch()
    latest_release.touch()
    _set_modified(older_release, 300)
    _set_modified(latest_release, 100)

    records = {
        older_release: _movement(date(2026, 11, 12)),
        latest_release: _movement(date(2026, 11, 20)),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_movement_workbook",
        lambda path: records[path],
    )

    result = file_discovery.discover_movement_workbook(
        tmp_path,
        date(2026, 11, 1),
    )

    assert result == latest_release


def test_uses_modification_time_only_when_latest_release_dates_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older_file = tmp_path / "older-file.xlsx"
    newer_file = tmp_path / "newer-file.xlsx"
    older_file.touch()
    newer_file.touch()
    _set_modified(older_file, 100)
    _set_modified(newer_file, 200)

    records = {
        older_file: _movement(date(2026, 11, 20)),
        newer_file: _movement(date(2026, 11, 20)),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_movement_workbook",
        lambda path: records[path],
    )

    result = file_discovery.discover_movement_workbook(
        tmp_path,
        date(2026, 11, 30),
    )

    assert result == newer_file


def test_rejects_ambiguous_movement_candidates_when_both_criteria_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.xlsx"
    second = tmp_path / "second.xlsx"
    first.touch()
    second.touch()
    _set_modified(first, 200)
    _set_modified(second, 200)

    records = {
        first: _movement(date(2026, 11, 20)),
        second: _movement(date(2026, 11, 20)),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_movement_workbook",
        lambda path: records[path],
    )

    with pytest.raises(ValueError, match="ambiguous.*first.xlsx.*second.xlsx"):
        file_discovery.discover_movement_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_ignores_other_months_empty_files_and_non_candidate_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other_month = tmp_path / "october.xlsx"
    empty = tmp_path / "empty.xls"
    hidden = tmp_path / ".hidden.xlsx"
    lock_file = tmp_path / "~$locked.xlsx"
    unsupported = tmp_path / "notes.csv"
    subdirectory = tmp_path / "nested"
    subdirectory.mkdir()
    nested_workbook = subdirectory / "movement.xlsx"

    for path in (other_month, empty, hidden, lock_file, unsupported, nested_workbook):
        if path.name not in {"nested", "movement.xlsx"}:
            path.touch()
    nested_workbook.touch()

    records = {
        other_month: _movement(date(2026, 10, 31)),
        empty: (),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_movement_workbook",
        lambda path: records[path],
    )

    with pytest.raises(FileNotFoundError, match="2026-11"):
        file_discovery.discover_movement_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_reports_invalid_movement_workbook_with_its_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corrupt = tmp_path / "corrupt.xlsx"
    corrupt.touch()

    def fail_to_read(path: Path) -> tuple[ReleaseRecord, ...]:
        raise ValueError("invalid workbook")

    monkeypatch.setattr(file_discovery, "read_movement_workbook", fail_to_read)

    with pytest.raises(ValueError, match="corrupt.xlsx.*invalid workbook"):
        file_discovery.discover_movement_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_rejects_missing_movement_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="directory does not exist"):
        file_discovery.discover_movement_workbook(
            tmp_path / "missing",
            date(2026, 11, 1),
        )


def test_rejects_a_file_as_movement_directory(tmp_path: Path) -> None:
    source_file = tmp_path / "source.xlsx"
    source_file.touch()

    with pytest.raises(ValueError, match="not a directory"):
        file_discovery.discover_movement_workbook(
            source_file,
            date(2026, 11, 1),
        )


def test_discovers_reference_with_matching_competence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = tmp_path / "reference-current.xlsx"
    previous = tmp_path / "reference-previous.xlsm"
    current.touch()
    previous.touch()

    references = {
        current: ReferenceWorkbook((), date(2026, 11, 1)),
        previous: ReferenceWorkbook((), date(2026, 10, 1)),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_reference_workbook",
        lambda path: references[path],
    )

    result = file_discovery.discover_reference_workbook(
        tmp_path,
        date(2026, 11, 30),
    )

    assert result == current


def test_rejects_multiple_reference_workbooks_for_the_same_competence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "reference-a.xlsx"
    second = tmp_path / "reference-b.xlsx"
    first.touch()
    second.touch()

    references = {
        first: ReferenceWorkbook((), date(2026, 11, 1)),
        second: ReferenceWorkbook((), date(2026, 11, 1)),
    }
    monkeypatch.setattr(
        file_discovery,
        "read_reference_workbook",
        lambda path: references[path],
    )

    with pytest.raises(ValueError, match="multiple reference workbooks.*reference-a.xlsx.*reference-b.xlsx"):
        file_discovery.discover_reference_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_rejects_when_no_reference_matches_the_competence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = tmp_path / "reference.xlsx"
    reference.touch()
    monkeypatch.setattr(
        file_discovery,
        "read_reference_workbook",
        lambda path: ReferenceWorkbook((), None),
    )

    with pytest.raises(FileNotFoundError, match="2026-11"):
        file_discovery.discover_reference_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_reports_invalid_reference_workbook_with_its_filename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corrupt = tmp_path / "broken-reference.xlsx"
    corrupt.touch()

    def fail_to_read(path: Path) -> ReferenceWorkbook:
        raise ValueError("missing required columns")

    monkeypatch.setattr(file_discovery, "read_reference_workbook", fail_to_read)

    with pytest.raises(ValueError, match="broken-reference.xlsx.*missing required columns"):
        file_discovery.discover_reference_workbook(
            tmp_path,
            date(2026, 11, 1),
        )


def test_rejects_missing_reference_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="directory does not exist"):
        file_discovery.discover_reference_workbook(
            tmp_path / "missing",
            date(2026, 11, 1),
        )


def test_rejects_a_file_as_reference_directory(tmp_path: Path) -> None:
    source_file = tmp_path / "source.xlsx"
    source_file.touch()

    with pytest.raises(ValueError, match="not a directory"):
        file_discovery.discover_reference_workbook(
            source_file,
            date(2026, 11, 1),
        )
