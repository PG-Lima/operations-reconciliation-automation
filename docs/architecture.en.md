# Architecture — Initial Design

The project is being rebuilt as an independent, layered Python application. The original script is a behavioral reference only; no employer-specific path, workbook, account, board ID, token, or endpoint configuration is reused.

## Layers

- **Domain:** immutable typed models and business classifications.
- **Services:** pure normalization, consolidation, and comparison rules.
- **Adapters:** movement and reference Excel input readers and the local Excel report writer are implemented. The local mock work-board gateway remains planned.
- **Application (next milestone):** daily run and monthly-close orchestration.
- **CLI (next milestone):** explicit commands for demo, daily comparison, and monthly close.

## Excel input adapter

The `adapters/excel_reader.py` module converts external files into typed domain models. The movement reader accepts `.xls`, `.xlsx`, `.xlsm`, and HTML-based Excel exports detected from their content; the reference reader expects the `Referencia_Principal` worksheet and uses row 5 as its default header row. Headers are resolved by normalized names or the documented prefixes. The domain layer does not depend on Pandas and does not know source filenames or worksheet names.

## Excel report output adapter

The `adapters/excel_report.py` module serializes an already-computed `ComparisonReport` to an `.xlsx` file at the caller-supplied local path. It creates the destination directory when needed and writes the `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou`, and `Novas empresas` worksheets. The adapter does not recalculate classifications, modify input workbooks, or access external services.

## Planned boundaries

The source folder will be configured by the user and represented by a local path in the demo. That path can represent a folder synchronized by a cloud client, but this demo does not sign in to or connect to a real Microsoft 365 tenant. Reports and history are written to a local output directory.

The task-board adapter will be a local mock by default. The core application will depend on a narrow protocol so a real provider could be introduced later without embedding API calls in business rules. The initial public demo will not create tasks in a real Monday.com account.

## Monthly close safety

The monthly close must be repeatable after partial failures. Report generation and task creation happen before reference promotion. Task creation is idempotent using normalized company plus competency. Reference promotion uses a validated temporary workbook and preserves the prior version in history. If input validation or task processing fails, the current reference must remain available for retry.
