# Operations Reconciliation Automation

[![CI](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml)

**English** | [Português](#português)

A Python project that demonstrates a reproducible, local workflow for reconciling monthly operational releases against a reference schedule. It validates and discovers Excel workbooks, consolidates released records, compares companies against scheduled quantities and dates, and generates a structured Excel report.

> This is an independent educational project. It contains no employer data, credentials, board identifiers, or connections to any employer's Microsoft 365 or Monday.com environment. The workflow runs locally. The optional task-board feature uses a local JSON simulator only; no remote board integration or external task creation is implemented.

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
- Run the reconciliation workflow through the installed `operations-reconciliation` command-line interface.
- Optionally create title-only simulated tasks for companies classified as `Menor`, using a persistent local JSON board and a normalized company/competence deduplication key.
- Keep monthly closing, reference archiving, and reference promotion as planned future milestones.

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

## Run a reconciliation

After installing the project in the active virtual environment, run:

```powershell
operations-reconciliation reconcile --movement-dir "data/movements" --reference-dir "data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13 --task-board "local-state/task-board.json"
```

The evaluation date and `--task-board` are optional. When omitted, the evaluation date defaults to the cutoff date and no task-board simulation runs. When `--task-board` is supplied, the local JSON board persists title-only tasks for companies classified as `Menor`; repeated runs skip existing company/competence keys. Competence must use `YYYY-MM`; cutoff and evaluation dates must use `YYYY-MM-DD`. The input folders must contain workbooks that satisfy the documented Excel contracts. The report is written to the supplied `.xlsx` destination. The default `local-state/` folder is ignored by Git.

See the [CLI guide](docs/cli.en.md) for argument details and exit codes.

## Run the checks

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
python -m ruff check src tests
```

The current implementation includes the core domain rules, Excel input and report adapters, deterministic local workbook discovery, single-run reconciliation orchestration, and an installable command-line interface. The local task-board simulator is implemented; monthly close remains planned.

## Documentation

The documentation is available in Portuguese and English:

| Topic | Português | English |
|---|---|---|
| Architecture | [Arquitetura](docs/architecture.md) | [Architecture](docs/architecture.en.md) |
| CLI | [Interface de linha de comando](docs/cli.md) | [Command-line interface](docs/cli.en.md) |
| Business rules | [Regras de negócio](docs/business-rules.md) | [Business rules](docs/business-rules.en.md) |
| Learning guide | [Guia de aprendizagem](docs/learning-guide.md) | [Learning guide](docs/learning-guide.en.md) |
| Security | [Segurança e limites dos dados](docs/security.md) | [Security and data boundaries](docs/security.en.md) |
| Quality assurance | [Garantia de qualidade](docs/quality-assurance.md) | [Quality assurance](docs/quality-assurance.en.md) |

## Project structure

```text
src/operations_reconciliation/
├── adapters/     # Excel input, output, discovery, and local task-board adapters
├── application/  # Reconciliation workflow orchestration
├── cli.py        # Command-line interface
├── domain/       # Typed domain models
└── services/     # Normalization, consolidation, comparison, task creation

tests/unit/       # Fast tests for rules and file validation
tests/integration/ # Excel-to-domain workflow tests
docs/             # Bilingual architecture, rules, learning, security, and QA guides
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

> Este é um projeto educacional independente. Ele não contém dados corporativos, credenciais, identificadores de quadros ou conexões com ambientes Microsoft 365 ou Monday.com de empregadores. O fluxo é local; o quadro de tarefas é apenas uma simulação JSON opcional, sem integração remota.

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
- Executar o fluxo pelo comando de linha de comando `operations-reconciliation` instalado no ambiente Python.
- Criar opcionalmente tarefas simuladas, contendo apenas o título, para empresas classificadas como `Menor`, usando um quadro JSON local persistente e uma chave de deduplicação por empresa normalizada/competência.
- Manter o fechamento mensal, o arquivamento e a promoção da referência como etapas futuras.

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

## Executar uma conciliação

Depois de instalar o projeto no ambiente virtual ativo, execute:

```powershell
operations-reconciliation reconcile --movement-dir "data/movements" --reference-dir "data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13 --task-board "local-state/task-board.json"
```

A data de avaliação e `--task-board` são opcionais. Quando omitida, a data de avaliação assume a data de corte e nenhuma simulação de tarefas é executada. Com `--task-board`, o quadro JSON local persiste tarefas contendo apenas o título para empresas classificadas como `Menor`; reexecuções ignoram chaves de empresa/competência já existentes. A competência usa `YYYY-MM`; as datas de corte e avaliação usam `YYYY-MM-DD`. As pastas de entrada precisam conter planilhas que atendam aos contratos Excel documentados. O relatório é gravado no destino `.xlsx` informado. A pasta padrão `local-state/` é ignorada pelo Git.

Consulte o [guia da CLI](docs/cli.md) para detalhes dos argumentos e códigos de saída.

## Executar as verificações

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
python -m ruff check src tests
```

A implementação atual inclui as regras centrais do domínio, os adaptadores Excel, a descoberta determinística de planilhas locais, a orquestração de uma execução completa de conciliação e uma interface de linha de comando instalável. A simulação local do quadro está implementada; o fechamento mensal permanece planejado.

## Documentação

A documentação está disponível em português e inglês:

| Tema | Português | English |
|---|---|---|
| Arquitetura | [Arquitetura](docs/architecture.md) | [Architecture](docs/architecture.en.md) |
| CLI | [Interface de linha de comando](docs/cli.md) | [Command-line interface](docs/cli.en.md) |
| Regras de negócio | [Regras de negócio](docs/business-rules.md) | [Business rules](docs/business-rules.en.md) |
| Aprendizagem | [Guia de aprendizagem](docs/learning-guide.md) | [Learning guide](docs/learning-guide.en.md) |
| Segurança | [Segurança e limites dos dados](docs/security.md) | [Security and data boundaries](docs/security.en.md) |
| Qualidade | [Garantia de qualidade](docs/quality-assurance.md) | [Quality assurance](docs/quality-assurance.en.md) |

## Estrutura do projeto

```text
src/operations_reconciliation/
├── adapters/     # Entrada, saída, descoberta Excel e quadro local simulado
├── application/  # Orquestração do fluxo de conciliação
├── cli.py        # Interface de linha de comando
├── domain/       # Modelos tipados do domínio
└── services/     # Normalização, consolidação, comparação e criação de tarefas

tests/
├── unit/         # Testes isolados de regras e adaptadores
└── integration/  # Testes do fluxo completo com planilhas Excel

docs/             # Guias bilíngues de arquitetura, regras, aprendizagem, segurança e qualidade
```

## Contratos de entrada Excel

O leitor de movimentações aceita arquivos `.xls`, `.xlsx` e `.xlsm`. Também detecta tabelas HTML exportadas pelo Excel e salvas com extensão `.xls`. Os cabeçalhos obrigatórios são `Contrato`, `Data da Liberação`, `Situação do Arquivo` e `Quantidade`; `Tipo da Carga` é opcional. A identificação dos cabeçalhos ignora acentos, maiúsculas/minúsculas e espaços externos. Somente registros `LIBERADO` são convertidos; contratos vazios e linhas de resumo como `Total` são ignorados.

O leitor da referência espera a aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão. Reconhece por prefixo as colunas `Empresa`, `Quantidade consolidada (mmm/AAAA)` e `Dias de liberação observados`; `Carteira` é opcional. A competência é extraída do mês/ano informado no cabeçalho da quantidade consolidada.

Quantidades de liberação inválidas, datas de liberação inválidas, cabeçalhos ambíguos e empresas duplicadas após normalização interrompem a importação com erro explícito. Strings numéricas no padrão brasileiro, como `1.234,50`, são aceitas para quantidades de movimentação.

## Segurança e limites dos dados

Utilize somente registros fictícios. Não envie para o Git planilhas exportadas de empregadores, nomes de clientes, tokens de API, URLs de acesso, IDs de quadros ou nomes de pastas internas. Qualquer conector real futuro deverá ser habilitado explicitamente, configurado separadamente e testado em um destino não produtivo.
