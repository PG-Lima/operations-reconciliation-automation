import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest

from operations_reconciliation.adapters import local_task_board


def test_missing_board_starts_empty_and_creates_parent_directories(tmp_path: Path) -> None:
    storage = tmp_path / "nested" / "board.json"
    board = local_task_board.LocalTaskBoard(storage)

    assert board.list_titles() == ()
    assert board.create_task(
        "Ácme Ltda. - 2026-11",
        company_key="ACME LTDA",
        competence=date(2026, 11, 1),
    )
    assert board.list_titles() == ("Ácme Ltda. - 2026-11",)

    payload = json.loads(storage.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": 1,
        "tasks": [
            {
                "title": "Ácme Ltda. - 2026-11",
                "identity": {
                    "company_key": "ACME LTDA",
                    "competence": "2026-11",
                },
            }
        ],
    }


def test_existing_identity_is_skipped_even_when_title_differs(tmp_path: Path) -> None:
    board = local_task_board.LocalTaskBoard(tmp_path / "board.json")
    assert board.create_task(
        "ACME Ltda. - 2026-11",
        company_key="ACME LTDA",
        competence=date(2026, 11, 1),
    )

    assert not board.create_task(
        "Acme Ltda. - November 2026",
        company_key="ACME LTDA",
        competence=date(2026, 11, 30),
    )
    assert board.list_titles() == ("ACME Ltda. - 2026-11",)


def test_same_company_can_have_a_task_in_a_different_competence(tmp_path: Path) -> None:
    board = local_task_board.LocalTaskBoard(tmp_path / "board.json")
    board.create_task("ACME - 2026-10", company_key="ACME", competence=date(2026, 10, 1))

    assert board.create_task(
        "ACME - 2026-11",
        company_key="ACME",
        competence=date(2026, 11, 1),
    )
    assert board.list_titles() == ("ACME - 2026-10", "ACME - 2026-11")


def test_rejects_non_json_storage_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"\.json"):
        local_task_board.LocalTaskBoard(tmp_path / "board.txt")


@pytest.mark.parametrize(
    ("title", "company_key", "competence", "message"),
    [
        (" ", "ACME", date(2026, 11, 1), "title"),
        ("ACME", " ", date(2026, 11, 1), "company key"),
        ("ACME", "ACME", "2026-11", "competence"),
    ],
)
def test_rejects_invalid_task_fields(
    tmp_path: Path,
    title: str,
    company_key: str,
    competence: object,
    message: str,
) -> None:
    board = local_task_board.LocalTaskBoard(tmp_path / "board.json")
    with pytest.raises(ValueError, match=message):
        board.create_task(
            title,
            company_key=company_key,
            competence=competence,  # type: ignore[arg-type]
        )


def test_reports_invalid_json(tmp_path: Path) -> None:
    storage = tmp_path / "board.json"
    storage.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not read simulated task board"):
        local_task_board.LocalTaskBoard(storage).list_titles()


@pytest.mark.parametrize("content", [b"\\xff", None])
def test_reports_unreadable_board_files(tmp_path: Path, content: bytes | None) -> None:
    storage = tmp_path / "board.json"
    if content is None:
        storage.mkdir()
    else:
        storage.write_bytes(content)

    with pytest.raises(ValueError, match="Could not read simulated task board"):
        local_task_board.LocalTaskBoard(storage).list_titles()


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"schema_version": 2, "tasks": []},
        {"schema_version": 1, "tasks": {}},
    ],
)
def test_rejects_invalid_board_schema(tmp_path: Path, payload: object) -> None:
    storage = tmp_path / "board.json"
    storage.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="schema|tasks list"):
        local_task_board.LocalTaskBoard(storage).list_titles()


@pytest.mark.parametrize(
    "task",
    [
        "not-an-object",
        {"title": "", "identity": {"company_key": "ACME", "competence": "2026-11"}},
        {"title": None, "identity": {"company_key": "ACME", "competence": "2026-11"}},
        {"title": "ACME - 2026-11", "identity": None},
        {"title": "ACME - 2026-11", "identity": {"company_key": "", "competence": "2026-11"}},
        {"title": "ACME - 2026-11", "identity": {"company_key": None, "competence": "2026-11"}},
        {"title": "ACME - 2026-11", "identity": {"company_key": "ACME", "competence": None}},
        {"title": "ACME - 2026-11", "identity": {"company_key": "ACME", "competence": "2026-1"}},
        {"title": "ACME - 2026-11", "identity": {"company_key": "ACME", "competence": "2026/11"}},
        {"title": "ACME - 2026-11", "identity": {"company_key": "ACME", "competence": "2026-13"}},
    ],
)
def test_rejects_invalid_stored_tasks(tmp_path: Path, task: object) -> None:
    storage = tmp_path / "board.json"
    storage.write_text(
        json.dumps({"schema_version": 1, "tasks": [task]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Simulated task"):
        local_task_board.LocalTaskBoard(storage).list_titles()


def test_rejects_duplicate_identities_in_stored_board(tmp_path: Path) -> None:
    identity = {"company_key": "ACME", "competence": "2026-11"}
    storage = tmp_path / "board.json"
    storage.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [
                    {"title": "ACME - 2026-11", "identity": identity},
                    {"title": "ACME Ltda. - 2026-11", "identity": identity},
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate task identities"):
        local_task_board.LocalTaskBoard(storage).list_titles()


def test_cleans_temporary_file_when_atomic_replace_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    storage = tmp_path / "board.json"
    board = local_task_board.LocalTaskBoard(storage)
    replace = Mock(side_effect=OSError("disk error"))
    monkeypatch.setattr(local_task_board.os, "replace", replace)

    with pytest.raises(OSError, match="disk error"):
        board.create_task(
            "ACME - 2026-11",
            company_key="ACME",
            competence=date(2026, 11, 1),
        )

    replace.assert_called_once()
    assert not storage.exists()
    assert tuple(tmp_path.glob(".board.json.*.tmp")) == ()

def test_rejects_non_string_task_fields(tmp_path: Path) -> None:
    board = local_task_board.LocalTaskBoard(tmp_path / "board.json")

    with pytest.raises(ValueError, match="title"):
        board.create_task(
            None,  # type: ignore[arg-type]
            company_key="ACME",
            competence=date(2026, 11, 1),
        )
    with pytest.raises(ValueError, match="company key"):
        board.create_task(
            "ACME - 2026-11",
            company_key=None,  # type: ignore[arg-type]
            competence=date(2026, 11, 1),
        )


def test_cleans_up_when_temporary_file_cannot_be_created(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    create_temporary = Mock(side_effect=OSError("temporary storage unavailable"))
    monkeypatch.setattr(local_task_board.tempfile, "NamedTemporaryFile", create_temporary)
    board = local_task_board.LocalTaskBoard(tmp_path / "board.json")

    with pytest.raises(OSError, match="temporary storage unavailable"):
        board.create_task(
            "ACME - 2026-11",
            company_key="ACME",
            competence=date(2026, 11, 1),
        )

    create_temporary.assert_called_once()
    assert tuple(tmp_path.iterdir()) == ()
