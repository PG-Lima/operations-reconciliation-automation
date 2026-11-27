# Architecture — Operations Reconciliation Automation

This project is an independent, layered Python application for reconciling operational movements against a reference schedule. The original script is used only as a behavioral reference. Employer-specific paths, corporate workbooks, credentials, board identifiers, and external service configurations are not part of this public implementation.

## Overview

The local execution is coordinated by `application/reconciliation.py` through the `run_reconciliation()` function. It receives the movement and reference directories, the competence, the cutoff date, and the output report path. The evaluation date is optional.

The current workflow follows these steps:

1. Validate the relationship between the competence, cutoff date, and evaluation date.
2. Discover the matching movement and reference workbooks.
3. Read and validate the selected files.
4. Consolidate released movements.
5. Compare the results with the reference and apply domain classifications.
6. Generate the Excel report at the supplied destination.
7. Return a `ReconciliationResult` containing the selected file paths, comparison result, and report path.

## Application layers

- **Domain (`domain/`):** immutable typed models representing reconciliation data and results.
- **Services (`services/`):** normalization, movement consolidation, and comparison rules. These rules do not depend on Excel files or external services.
- **Adapters (`adapters/`):** Excel workbook reading and validation, local file discovery, and Excel report generation.
- **Application (`application/`):** coordinates adapters and services to execute the complete local reconciliation workflow.
- **CLI:** a command-line interface has not been implemented yet. Demo and guided execution commands remain planned.

## Excel input adapter

The `adapters/excel_reader.py` module converts source files into typed domain models.

The movement reader accepts `.xls`, `.xlsx`, and `.xlsm` files. It also recognizes HTML-based Excel exports by inspecting their content, including files saved with the `.xls` extension.

The reference reader expects the `Referencia_Principal` worksheet and uses row 5 as the default header row. Headers are identified by normalized names or by the prefixes defined in the data contract.

The domain layer does not depend on Pandas and does not need to know workbook filenames, worksheet names, or spreadsheet presentation details.

## Excel report output adapter

The `adapters/excel_report.py` module serializes an already-computed `ComparisonReport` into an `.xlsx` file at the local path supplied by the caller.

The report contains seven worksheets: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou`, and `Novas empresas`.

The adapter creates the destination directory when needed. It does not recalculate classifications, modify input workbooks, or access external services.

## Excel file discovery

The `adapters/file_discovery.py` module scans only the supplied local directory and does not recurse into subdirectories.

Hidden files, Excel temporary files, empty files, and unsupported extensions are ignored. A non-empty candidate workbook that fails validation stops discovery and reports the filename.

For movement workbooks, only released records whose release date belongs to the requested competence are considered. Selection prioritizes the latest release date; file modification time is used only as a tie-breaker. If the criteria are still tied, discovery fails as ambiguous.

For the reference workbook, the competence extracted from the header must match the requested competence, and exactly one matching file must exist.

Discovery receives explicitly supplied local paths and dates. It does not search OneDrive, SharePoint, or other remote services, and it does not move, rename, or modify files.

## Single-run orchestration

The `run_reconciliation()` function coordinates the workflow described in this document. When omitted, the evaluation date defaults to the cutoff date.

The application rejects:
- A cutoff date whose competence does not match the requested competence.
- An evaluation date earlier than the cutoff date.
- An output path that would overwrite either selected input workbook.

On completion, the function returns a `ReconciliationResult` containing the selected workbooks, the comparison report, and the output file path.

## Current implementation boundaries

Execution is local and depends on the directories and dates supplied by the caller. The project does not authenticate with remote services, directly access Microsoft 365 or Monday.com environments, or create tasks on external boards.

The application does not schedule runs, implement monthly closing, or promote or archive reference workbooks. A CLI is also not available in this milestone.

Source workbooks are read by the reconciliation workflow and should not be modified. The report is generated at a separate output path, and the application prevents that path from overwriting the selected input files.

## Planned next steps

Planned extensions include a CLI to make execution easier to reproduce, a local mock adapter to represent task-board operations, and a monthly closing workflow with controlled reference archiving and promotion.

These features are planned and are not part of the currently implemented workflow.

## Planned monthly-close safeguards

When monthly closing is implemented, it should be repeatable after partial failures. The current reference should remain available if data validation or task processing fails.

The proposed design includes validating a temporary workbook before promoting the reference, preserving the previous version in history, and making task creation idempotent through a business key composed of the normalized company and competence.

These are design guidelines for a future milestone, not guarantees provided by the current implementation.