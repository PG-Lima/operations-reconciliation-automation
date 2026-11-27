# Operations Reconciliation Automation

[![CI](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml)

**English** | [Português](#português)

A Python project that demonstrates a reproducible, local workflow for reconciling monthly operational releases against a reference schedule. It validates and discovers Excel workbooks, consolidates released records, compares companies against scheduled quantities and dates, and generates a structured Excel report.

> This is an independent educational project. It contains no employer data, credentials, board identifiers, or connections to any employer's Microsoft 365 or Monday.com environment. The current workflow runs locally; remote board integration and task creation are not implemented.

## Project purpose

This repository has two equally important goals:

- **Professional portfolio:** demonstrate practical skills in Python, data validation, domain modeling, layered architecture, Excel automation, orchestration, and automated testing.
- **Open learning resource:** allow readers to study the implementation, reproduce the workflow with synthetic data, understand the design decisions, and adapt the ideas to other contexts and data contracts.

## Current scope

- Normalize company names and scheduled calendar days.
- Read and validate movement and reference Excel workbooks.
- Aggregate `LIBERADO` movements by company and release date.
- Compare monthly quantities with a reference while preserving companies with no movement.
- Classify companies as `Aguardando`, `Menor`, `Igual`, `Maior`, or `Não pagou`.
- Keep companies absent from the reference in a separate result.
- Read movement exports in `.xls`, `.xlsx`, and `.xlsm` formats, including HTML-based Excel exports saved as `.xls`.
- Read the reference workbook from the configured sheet and header row, including its monthly competence when present.
- Validate required columns, dates, quantities, and duplicate company keys before processing.
- Generate a local Excel report with seven worksheets: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou`, and `Novas empresas`.
- Discover movement and reference workbooks from explicitly configured local folders using deterministic selection rules.
- Orchestrate a complete local reconciliation run from explicitly supplied folders, competence, and dates.
- Keep local task-board simulation, monthly closing, reference archiving, and reference promotion as planned future milestones.

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

The current implementation includes the core domain rules, Excel input and report adapters, deterministic local workbook discovery, and single-run reconciliation orchestration. Local task-board simulation and monthly close remain planned.

## Project structure

```text
src/operations_reconciliation/
├── adapters/     # Excel input, output, and discovery adapters
├── application/  # Reconciliation workflow orchestration
├── domain/       # Typed domain models
└── services/     # Normalization, consolidation, comparison

tests/unit/       # Fast tests for rules and file validation
tests/integration/ # Excel-to-domain workflow tests
docs/             # Architecture and business-rule documentation
```

## Excel input contracts

The movement reader accepts `.xls`, `.xlsx`, and `.xlsm` files. It also detects HTML tables exported by Excel and saved with an `.xls` extension. Required movement headers are `Contrato`, `Data da Liberação`, `Situação do Arquivo`, and `Quantidade`; `Tipo da Carga` is optional. Header matching ignores accents, case, and surrounding whitespace. Only `LIBERADO` rows are converted; blank contracts and summary rows such as `Total` are skipped.

The reference reader expects the `Referencia_Principal` worksheet with its header on row 5 by default. It recognizes `Empresa`, `Quantidade consolidada (mmm/YYYY)`, and `Dias de liberação observados` columns by prefix; `Carteira` is optional. The competence is read from the month/year in the quantity header.

Invalid release quantities, invalid release dates, ambiguous headers, and duplicate companies after normalization stop the import with an explicit error. Numeric strings in Brazilian format such as `1.234,50` are supported for movement quantities.

## Safety and data boundaries

Use synthetic example records only. Do not commit spreadsheets exported from an employer, customer names, API tokens, access URLs, board IDs, or internal folder names. Any future live connector must be explicitly enabled, separately configured, and tested against a non-production destination.

---

<a id="português"></a>
# Automação de Conciliação Operacional

Projeto em Python que demonstra um fluxo local e reproduzível para conciliar movimentações operacionais mensais com uma referência de programação. Ele valida e descobre planilhas Excel, consolida registros liberados, compara empresas com as quantidades e datas previstas e gera um relatório Excel estruturado.

> Este é um projeto educacional independente. Ele não contém dados corporativos, credenciais, identificadores de quadros ou conexões com ambientes Microsoft 365 ou Monday.com de empregadores. O fluxo atual é executado localmente; a integração com quadros remotos e a criação de tarefas ainda não foram implementadas.

## Objetivos do projeto

Este repositório tem dois objetivos igualmente importantes:

- **Portfólio profissional:** demonstrar habilidades práticas em Python, validação de dados, modelagem de domínio, arquitetura em camadas, automação com Excel, orquestração e testes automatizados.
- **Recurso aberto de aprendizagem:** permitir que outras pessoas estudem a implementação, reproduzam o fluxo com dados fictícios, compreendam as decisões de projeto e adaptem as ideias a outros contextos e contratos de dados.

## Escopo atual

- Normalizar nomes de empresas e dias previstos.
- Consolidar movimentações `LIBERADO` por empresa e data de liberação.
- Comparar quantidades mensais com uma referência, preservando empresas sem movimentação.
- Classificar empresas como `Aguardando`, `Menor`, `Igual`, `Maior` ou `Não pagou`.
- Separar empresas que não constam na referência.
- Ler e validar planilhas de movimentações `.xls`, `.xlsx`, `.xlsm` e HTML do Excel salvo como `.xls`.
- Ler a referência mensal na aba `Referencia_Principal`, com competência extraída do cabeçalho quando disponível.
- Gerar localmente um relatório Excel com sete abas: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou` e `Novas empresas`.
- Descobrir planilhas de movimentação e referência em pastas locais configuradas explicitamente, com critérios determinísticos de seleção.
- Orquestrar uma execução local completa a partir das pastas, competência e datas informadas, gerando o relatório Excel.
- Manter a simulação local do quadro de tarefas, o fechamento mensal, o arquivamento e a promoção da referência como etapas futuras.

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

A implementação atual inclui as regras centrais do domínio, os adaptadores Excel, a descoberta determinística de planilhas locais e a orquestração de uma execução completa de conciliação. A simulação do quadro e o fechamento mensal permanecem planejados.

## Contratos de entrada Excel

O leitor de movimentações aceita arquivos `.xls`, `.xlsx` e `.xlsm`. Também detecta tabelas HTML exportadas pelo Excel e salvas com extensão `.xls`. Os cabeçalhos obrigatórios são `Contrato`, `Data da Liberação`, `Situação do Arquivo` e `Quantidade`; `Tipo da Carga` é opcional. A identificação dos cabeçalhos ignora acentos, maiúsculas/minúsculas e espaços externos. Somente registros `LIBERADO` são convertidos; contratos vazios e linhas de resumo como `Total` são ignorados.

O leitor da referência espera a aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão. Reconhece por prefixo as colunas `Empresa`, `Quantidade consolidada (mmm/AAAA)` e `Dias de liberação observados`; `Carteira` é opcional. A competência é extraída do mês/ano informado no cabeçalho da quantidade consolidada.

Quantidades de liberação inválidas, datas de liberação inválidas, cabeçalhos ambíguos e empresas duplicadas após normalização interrompem a importação com erro explícito. Strings numéricas no padrão brasileiro, como `1.234,50`, são aceitas para quantidades de movimentação.

## Segurança e limites dos dados

Utilize somente registros fictícios. Não envie para o Git planilhas exportadas de empregadores, nomes de clientes, tokens de API, URLs de acesso, IDs de quadros ou nomes de pastas internas. Qualquer conector real futuro deverá ser habilitado explicitamente, configurado separadamente e testado em um destino não produtivo.
