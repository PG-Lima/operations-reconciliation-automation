# Security and Data Boundaries

This document describes the security boundaries of the current implementation and provides guidance for using the repository as a public portfolio and learning project. It is not a security certification or a formal risk assessment.

## Current security scope

The implemented workflow runs locally. It receives directory paths and dates, reads Excel workbooks, calculates the reconciliation, and writes a report to the supplied path. Optionally, it can update a simulated task board in a local JSON file.

The current implementation:

- Does not authenticate with Microsoft 365, SharePoint, OneDrive, or Monday.com.
- Does not upload workbooks to remote services.
- Does not create tasks or items on external boards; the only available task creation is the optional local simulation.
- Does not store credentials or tokens for remote connectors.
- Does not schedule executions or perform the planned monthly close.

When `--task-board` is used, the local JSON file contains task titles and internal metadata with normalized company names and competences. This information may be sensitive. Use only synthetic data in demonstrations, store the file in an appropriately restricted folder, and do not commit it to Git. The default `local-state/` folder is ignored by `.gitignore`; alternate paths must be protected by the user.

File discovery examines only files directly inside the supplied directories. It does not recurse into subdirectories. Hidden files, Excel temporary files, empty files, and unsupported extensions are ignored. A non-empty candidate workbook that fails validation stops discovery with an explicit error.

## Data allowed in the public repository

Use only fictional, synthetic, or purpose-created demonstration data.

Do not add the following to the repository:

- Workbooks exported from employers, customers, or suppliers.
- Real customer, contract, employee, or partner names.
- Non-public personal, financial, operational, or commercial data.
- Passwords, tokens, API keys, cookies, or session files.
- Internal URLs, server names, corporate paths, or board identifiers.
- Screenshots that reveal internal information.

Before adding a file, review its contents and also its metadata, worksheet names, comments, formulas, document properties, and filenames. Apparently fictional data may still contain real information in auxiliary fields or metadata.

## Workbook validation and integrity

The readers validate expected workbook contracts, including required columns, dates, quantities, and duplicate company keys after normalization. Invalid records must not be silently converted into valid results.

Discovery stops when a non-empty candidate workbook cannot be validated or when file selection is ambiguous. This avoids silently choosing an incorrect source.

The application also checks that:

- The cutoff date belongs to the requested competence.
- The evaluation date, when supplied, does not precede the cutoff date.
- The output path does not match the path of either selected input workbook.

The reconciliation workflow reads source workbooks and generates the report at a separate destination. Still, use working copies and keep original files protected by their own access controls and backup procedures.

## Protection of generated reports

The report may contain information derived from the processed workbooks. Choose an appropriate output directory, with restricted access when the data requires it.

Do not publish real reports in commits, issues, pull requests, CI messages, or screenshots. The application does not implement file encryption, access control, retention, secure disposal, or automatic report anonymization.

## Secrets and configuration

The current local workflow does not require API credentials or tokens. Do not include secrets in code, tests, the README, examples, error messages, or commits.

If an external integration is developed in the future, secrets must be provided through an appropriate secret-management mechanism outside version control. Any future integration should use least-privilege permissions, explicit configuration, and non-production destinations during development and testing.

## Dependencies and software supply chain

Dependencies and version ranges are declared in pyproject.toml. The current configuration does not include automated vulnerability auditing, license checks, software component inventory generation, or installation hash verification.

Keep dependencies updated, review relevant changes, and run the tests after updates. CI currently runs automated tests and Ruff; it must not be interpreted as a complete security scan.

## Limitations and non-production use

This project is an educational demonstration and must not be treated as production-ready. It does not implement authentication, authorization, multi-user isolation, encryption at rest, audit trails, backups, disaster recovery, security monitoring, or formal incident management.

Workbook validation reduces input errors, but it does not make every third-party file safe. Treat external files as untrusted data and follow the security controls of the environment in which they are processed.

## Contribution checklist

Before opening a pull request, confirm:

- [ ] Examples and tests use synthetic data only.
- [ ] No secret, internal identifier, or corporate path was included.
- [ ] Input workbooks are not modified by the tested workflow.
- [ ] Example reports do not expose real information.
- [ ] Error messages do not reveal credentials or internal details.
- [ ] Tests and static analysis have been run.

## Future integration checklist

Before connecting any real service, define and review:

1. The integration purpose and strictly necessary data.
2. The technical identity and least-privilege permissions.
3. Secret storage and rotation outside Git.
4. A mock mode for tests, without real calls.
5. A non-production environment and explicit authorization procedure.
6. Idempotency, safe retries, failure handling, and logs without sensitive data.
7. Tests, security review, and documentation of operational boundaries.

These items are requirements for a possible future milestone; they are not controls already provided by the current code.

## Internal references

- [Architecture](architecture.en.md)
- [Business Rules](business-rules.en.md)
- [Learning Guide](learning-guide.en.md)
- [Quality Assurance](quality-assurance.en.md)
