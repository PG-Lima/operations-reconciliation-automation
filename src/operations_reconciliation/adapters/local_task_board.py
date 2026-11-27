"""Persistent local simulation of a title-only task board."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


class LocalTaskBoard:
    """Store simulated tasks in a local JSON file with an internal deduplication key.

    The only task field exposed by this adapter is its title. Company and competence
    are retained as private simulator metadata so retries can detect existing tasks.
    """

    def __init__(self, storage_path: Path) -> None:
        self._path = Path(storage_path)
        if self._path.suffix.casefold() != ".json":
            raise ValueError("Task board storage path must use the .json extension.")

    def list_titles(self) -> tuple[str, ...]:
        """Return the visible titles stored in the simulated board."""
        return tuple(task["title"] for task in self._read_tasks())

    def create_task(
        self,
        title: str,
        *,
        company_key: str,
        competence: date,
    ) -> bool:
        """Create a title-only task unless its company/competence key already exists."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Task title must not be empty.")
        if not isinstance(company_key, str) or not company_key.strip():
            raise ValueError("Task company key must not be empty.")
        if not isinstance(competence, date):
            raise ValueError("Task competence must be a date.")

        competence_key = competence.strftime("%Y-%m")
        tasks = self._read_tasks()
        if any(
            task["identity"]["company_key"] == company_key
            and task["identity"]["competence"] == competence_key
            for task in tasks
        ):
            return False

        tasks.append(
            {
                "title": title.strip(),
                "identity": {
                    "company_key": company_key,
                    "competence": competence_key,
                },
            }
        )
        self._write_tasks(tasks)
        return True

    def _read_tasks(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Could not read simulated task board '{self._path}': {error}"
            ) from error

        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError("Simulated task board has an unsupported or invalid schema.")

        tasks = payload.get("tasks")
        if not isinstance(tasks, list):
            raise ValueError("Simulated task board must contain a tasks list.")

        seen: set[tuple[str, str]] = set()
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                raise ValueError(f"Simulated task {index} must be an object.")

            title = task.get("title")
            identity = task.get("identity")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Simulated task {index} has an invalid title.")
            if not isinstance(identity, dict):
                raise ValueError(f"Simulated task {index} has an invalid identity.")

            company_key = identity.get("company_key")
            competence = identity.get("competence")
            if (
                not isinstance(company_key, str)
                or not company_key.strip()
                or not isinstance(competence, str)
                or len(competence) != 7
                or competence[4] != "-"
            ):
                raise ValueError(f"Simulated task {index} has an invalid identity.")

            try:
                date.fromisoformat(f"{competence}-01")
            except ValueError as error:
                raise ValueError(
                    f"Simulated task {index} has an invalid competence."
                ) from error
            key = (company_key, competence)
            if key in seen:
                raise ValueError("Simulated task board contains duplicate task identities.")
            seen.add(key)

        return tasks

    def _write_tasks(self, tasks: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": 1, "tasks": tasks}
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(payload, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())

            os.replace(temporary_path, self._path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
