# Operations Reconciliation Automation

[![CI](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml)

**English** | [Português](#português)

A Python demonstration project for reconciling monthly operational releases against a reference schedule. It consolidates released records, classifies companies after their scheduled deadlines, generates Excel reports, and demonstrates task creation through a safe local work-board adapter.

> This is an independent educational demo. It does not contain company data, credentials, board identifiers, or connections to any employer's Microsoft 365 or Monday.com environment. The work-board integration will use a local mock by default; no real items are created.

## Current scope

- Normalize company names and scheduled calendar days.
- Aggregate `LIBERADO` movements by company and release date.
- Compare monthly quantities with a reference while preserving companies with no movement.
- Classify companies as `Aguardando`, `Menor`, `Igual`, `Maior`, or `Não pagou`.
- Keep companies absent from the reference in a separate result.
- Build an Excel report and a local mock work-board workflow in later milestones.
- Support month closing, reference archiving, and promotion through a controlled, testable workflow in later milestones.

## Requirements

- Python 3.13 or newer
- Windows, macOS, or Linux

## Setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run the checks

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
python -m ruff check src tests
```

The current milestone implements and tests the core domain rules. File discovery, Excel adapters, reporting, local board simulation, and monthly orchestration are planned next.

## Project structure

```text
src/operations_reconciliation/
├── domain/       # Typed domain models
└── services/     # Normalization, consolidation, comparison

tests/unit/       # Fast tests for business rules
docs/             # Architecture and business-rule documentation
```

## Safety and data boundaries

Use synthetic example records only. Do not commit spreadsheets exported from an employer, customer names, API tokens, access URLs, board IDs, or internal folder names. Any future live connector must be explicitly enabled, separately configured, and tested against a non-production destination.

---

<a id="português"></a>
# Automação de Conciliação Operacional

Projeto demonstrativo em Python para conciliar movimentações operacionais mensais com uma referência de programação. O sistema consolida registros liberados, classifica empresas após os prazos previstos, gera relatórios Excel e demonstra a criação de tarefas por meio de um quadro local simulado.

> Este é um projeto educacional independente. Ele não contém dados da empresa, credenciais, identificadores de quadros ou conexões com ambientes Microsoft 365 ou Monday.com de empregadores. A integração com o quadro utilizará um simulador local por padrão; nenhum item real será criado.

## Escopo atual

- Normalizar nomes de empresas e dias previstos.
- Consolidar movimentações `LIBERADO` por empresa e data de liberação.
- Comparar quantidades mensais com uma referência, preservando empresas sem movimentação.
- Classificar empresas como `Aguardando`, `Menor`, `Igual`, `Maior` ou `Não pagou`.
- Separar empresas que não constam na referência.
- Construir relatório Excel e fluxo de quadro de tarefas simulado nas próximas etapas.
- Implementar fechamento mensal, arquivamento e promoção da referência em um fluxo controlado e testável nas próximas etapas.

## Requisitos

- Python 3.13 ou superior
- Windows, macOS ou Linux

## Instalação

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

No macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Executar as verificações

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
python -m ruff check src tests
```

Esta primeira etapa implementa e testa as regras centrais do domínio. Descoberta de arquivos, adaptadores Excel, relatórios, simulação local do quadro e orquestração mensal serão desenvolvidos a seguir.

## Segurança e limites dos dados

Utilize somente registros fictícios. Não envie para o Git planilhas exportadas de empregadores, nomes de clientes, tokens de API, URLs de acesso, IDs de quadros ou nomes de pastas internas. Qualquer conector real futuro deverá ser habilitado explicitamente, configurado separadamente e testado em um destino não produtivo.
