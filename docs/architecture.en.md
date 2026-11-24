# Architecture — Initial Design

The project is being rebuilt as an independent, layered Python application. The original script is a behavioral reference only; no employer-specific path, workbook, account, board ID, token, or endpoint configuration is reused.

## Layers

- **Domain:** immutable typed models and business classifications.
- **Services:** pure normalization, consolidation, and comparison rules.
- **Adapters (next milestone):** Excel readers/writers, local synced-folder storage, and a local mock work-board gateway.
- **Application (next milestone):** daily run and monthly-close orchestration.
- **CLI (next milestone):** explicit commands for demo, daily comparison, and monthly close.

## Planned boundaries

The source folder will be configured by the user and represented by a local path in the demo. That path can represent a folder synchronized by a cloud client, but this demo does not sign in to or connect to a real Microsoft 365 tenant. Reports and history are written to a local output directory.

The task-board adapter will be a local mock by default. The core application will depend on a narrow protocol so a real provider could be introduced later without embedding API calls in business rules. The initial public demo will not create tasks in a real Monday.com account.

## Monthly close safety

The monthly close must be repeatable after partial failures. Report generation and task creation happen before reference promotion. Task creation is idempotent using normalized company plus competency. Reference promotion uses a validated temporary workbook and preserves the prior version in history. If input validation or task processing fails, the current reference must remain available for retry.
