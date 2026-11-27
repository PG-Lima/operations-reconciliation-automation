from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from operations_reconciliation import cli


def _arguments(tmp_path: Path) -> list[str]:
    return [
        "reconcile",
        "--movement-dir",
        str(tmp_path / "movements"),
        "--reference-dir",
        str(tmp_path / "references"),
        "--competence",
        "2026-11",
        "--cutoff-date",
        "2026-11-12",
        "--output",
        str(tmp_path / "output" / "report.xlsx"),
    ]


def _result(tmp_path: Path, task_board_result=None):
    return SimpleNamespace(
        movement_workbook=tmp_path / "movements" / "movement.xlsx",
        reference_workbook=tmp_path / "references" / "reference.xlsx",
        output_workbook=tmp_path / "output" / "report.xlsx",
        task_board_result=task_board_result,
    )


def test_parses_valid_competence() -> None:
    assert cli._parse_competence("2026-11") == date(2026, 11, 1)


@pytest.mark.parametrize("value", ["2026-1", "2026/11", "2026-13"])
def test_rejects_invalid_competence(value: str) -> None:
    with pytest.raises(cli.argparse.ArgumentTypeError, match="Competence"):
        cli._parse_competence(value)


def test_parses_valid_iso_date() -> None:
    assert cli._parse_date("2026-11-12") == date(2026, 11, 12)


@pytest.mark.parametrize("value", ["12/11/2026", "2026-02-30", "2026-1-2", "20261112"])
def test_rejects_invalid_iso_date(value: str) -> None:
    with pytest.raises(cli.argparse.ArgumentTypeError, match="YYYY-MM-DD"):
        cli._parse_date(value)


def test_main_runs_reconciliation_and_prints_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = _result(tmp_path)
    run = Mock(return_value=result)
    monkeypatch.setattr(cli, "run_reconciliation", run)
    arguments = _arguments(tmp_path) + ["--evaluation-date", "2026-11-13"]

    exit_code = cli.main(arguments)

    assert exit_code == 0
    run.assert_called_once_with(
        movement_directory=tmp_path / "movements",
        reference_directory=tmp_path / "references",
        competence=date(2026, 11, 1),
        cutoff_date=date(2026, 11, 12),
        output_path=tmp_path / "output" / "report.xlsx",
        evaluation_date=date(2026, 11, 13),
        task_board_path=None,
    )
    output = capsys.readouterr().out
    assert "Reconciliation completed successfully." in output
    assert str(result.movement_workbook) in output
    assert str(result.reference_workbook) in output
    assert str(result.output_workbook) in output
    assert "task-board simulation" not in output


def test_main_defaults_evaluation_date_and_task_board_to_none(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = Mock(return_value=_result(tmp_path))
    monkeypatch.setattr(cli, "run_reconciliation", run)

    assert cli.main(_arguments(tmp_path)) == 0
    assert run.call_args.kwargs["evaluation_date"] is None
    assert run.call_args.kwargs["task_board_path"] is None


def test_main_passes_optional_task_board_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_result = SimpleNamespace(
        eligible_companies=3,
        created_tasks=2,
        skipped_existing=1,
    )
    result = _result(tmp_path, task_result)
    run = Mock(return_value=result)
    monkeypatch.setattr(cli, "run_reconciliation", run)
    task_path = tmp_path / "task-board.json"

    assert cli.main(_arguments(tmp_path) + ["--task-board", str(task_path)]) == 0

    assert run.call_args.kwargs["task_board_path"] == task_path
    output = capsys.readouterr().out
    assert "Local task-board simulation:" in output
    assert "Eligible companies: 3" in output
    assert "Created tasks: 2" in output
    assert "Skipped existing tasks: 1" in output


@pytest.mark.parametrize(
    "error",
    [ValueError("invalid input"), OSError("cannot read source")],
)
def test_main_reports_application_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
) -> None:
    run = Mock(side_effect=error)
    monkeypatch.setattr(cli, "run_reconciliation", run)

    exit_code = cli.main(_arguments(tmp_path))

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"Error: {error}" in captured.err
    assert captured.out == ""


def test_main_requires_a_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main([])

    assert error.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_main_rejects_invalid_date_before_running_application(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run = Mock()
    monkeypatch.setattr(cli, "run_reconciliation", run)
    arguments = _arguments(tmp_path)
    arguments[arguments.index("2026-11-12")] = "12/11/2026"

    with pytest.raises(SystemExit) as error:
        cli.main(arguments)

    assert error.value.code == 2
    assert "Dates must use YYYY-MM-DD" in capsys.readouterr().err
    run.assert_not_called()
