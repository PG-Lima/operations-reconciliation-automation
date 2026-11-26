"""Discover valid local Excel source workbooks deterministically."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from operations_reconciliation.adapters.excel_reader import (
    SUPPORTED_MOVEMENT_EXTENSIONS,
    SUPPORTED_REFERENCE_EXTENSIONS,
    read_movement_workbook,
    read_reference_workbook,
)
from operations_reconciliation.domain.models import ReferenceWorkbook, ReleaseRecord


def _validate_directory(directory: Path) -> Path:
    source = Path(directory)
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")
    if not source.is_dir():
        raise ValueError(f"Source path is not a directory: {source}")
    return source


def _candidate_files(directory: Path, extensions: set[str]) -> tuple[Path, ...]:
    return tuple(
        sorted(
            (
                path
                for path in directory.iterdir()
                if path.is_file()
                and path.suffix.casefold() in extensions
                and not path.name.startswith((".", "~$"))
                and path.stat().st_size > 0
            ),
            key=lambda path: path.name.casefold(),
        )
    )


def _competence_start(competence: date) -> date:
    return date(competence.year, competence.month, 1)


def _same_month(value: date, competence: date) -> bool:
    return value.year == competence.year and value.month == competence.month


def discover_movement_workbook(directory: Path, competence: date) -> Path:
    """Select the movement workbook with the latest release in the requested month.

    File modification time is used only when candidate workbooks share the same latest
    release date. If both criteria tie, selection is ambiguous and raises ValueError.
    Hidden files, Excel lock files, empty files, unsupported files, and subdirectories
    are ignored. A non-empty supported workbook that cannot be read stops discovery.
    """
    source_directory = _validate_directory(Path(directory))
    candidates = _candidate_files(source_directory, SUPPORTED_MOVEMENT_EXTENSIONS)
    ranked: list[tuple[date, int, Path]] = []

    for path in candidates:
        try:
            records: tuple[ReleaseRecord, ...] = read_movement_workbook(path)
        except (OSError, ValueError) as error:
            raise ValueError(f"Could not inspect movement workbook '{path.name}': {error}") from error

        release_dates = tuple(
            record.release_date
            for record in records
            if _same_month(record.release_date, competence)
        )
        if release_dates:
            ranked.append((max(release_dates), path.stat().st_mtime_ns, path))

    if not ranked:
        raise FileNotFoundError(
            f"No movement workbook with released records was found for {competence:%Y-%m} "
            f"in '{source_directory}'."
        )

    latest_release = max(item[0] for item in ranked)
    latest_release_candidates = [item for item in ranked if item[0] == latest_release]
    latest_modified = max(item[1] for item in latest_release_candidates)
    winners = sorted(
        (item[2] for item in latest_release_candidates if item[1] == latest_modified),
        key=lambda path: path.name.casefold(),
    )

    if len(winners) > 1:
        names = ", ".join(path.name for path in winners)
        raise ValueError(
            f"Ambiguous movement workbooks for {competence:%Y-%m}: {names}."
        )

    return winners[0]


def discover_reference_workbook(directory: Path, competence: date) -> Path:
    """Find the only valid reference workbook for the requested month.

    The reference reader extracts competence from the quantity column header. The exact
    first day of the requested month must match. Multiple matching workbooks are rejected
    instead of choosing by filename or modification time.
    """
    source_directory = _validate_directory(Path(directory))
    candidates = _candidate_files(source_directory, SUPPORTED_REFERENCE_EXTENSIONS)
    expected_competence = _competence_start(competence)
    matches: list[Path] = []

    for path in candidates:
        try:
            reference: ReferenceWorkbook = read_reference_workbook(path)
        except (OSError, ValueError) as error:
            raise ValueError(f"Could not inspect reference workbook '{path.name}': {error}") from error

        if reference.competence == expected_competence:
            matches.append(path)

    if not matches:
        raise FileNotFoundError(
            f"No reference workbook was found for {competence:%Y-%m} in '{source_directory}'."
        )

    if len(matches) > 1:
        names = ", ".join(path.name for path in sorted(matches, key=lambda item: item.name.casefold()))
        raise ValueError(
            f"Multiple reference workbooks were found for {competence:%Y-%m}: {names}."
        )

    return matches[0]
