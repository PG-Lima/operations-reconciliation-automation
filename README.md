# Operations Reconciliation Automation

[![CI](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml)

**English** | [Português](#português)

A Python project for reconciling monthly operational releases against a reference schedule. It demonstrates explicit Excel data contracts, deterministic local workbook discovery, domain rules, comparison, and structured report generation. Its design prioritizes reproducibility and keeps external service integrations outside the current scope.

> This is an independent educational project. It contains no employer data, credentials, board identifiers, or connections to an employer's Microsoft 365 or Monday.com environment. The implemented workflow runs locally; remote board integration and task creation are not available.

## Project purpose

This repository has two equally important goals:

- **Professional portfolio:** demonstrate practical skills in Python, data validation, domain modeling, layered architecture, Excel automation, and automated testing.
- **Open learning resource:** allow readers to study the implementation, reproduce the workflow with synthetic data, understand design decisions, and adapt the ideas to other contexts and data contracts.

## Current scope

- Normalize company names and scheduled calendar days.
- Read and validate movement and reference Excel workbooks.
- Aggregate `LIBERADO` movements by company and release date.
- Compare monthly quantities with a reference while preserving companies with no movement.
- Classify companies as `Aguardando`, `Menor`, `Igual`, `Maior`, or `Não pagou`.
- Keep companies absent from the reference in a separate result.
- Read movement exports in `.xls`, `.xlsx`, and `.xlsm` formats, including HTML-based Excel exports saved as `.xls`.
- Read the reference workbook from the `Referencia_Principal` worksheet, with a default header on row 5.
- Validate required columns, dates, quantities, and duplicate company keys before processing.
- Generate a local Excel report with seven worksheets: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou`, and `Novas empresas`.
- Discover movement and reference workbooks from explicitly supplied local folders using deterministic selection rules.

## Requirements

- Python 3.13 or newer
- Windows, macOS, or Linux

## Setup

Create and activate a virtual environment, then install the project with development dependencies:

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

## Documentation

The documentation is available in Portuguese and English:

| Topic | Português | English |
|---|---|---|
| Architecture | [Arquitetura](docs/architecture.md) | [Architecture](docs/architecture.en.md) |
| Business rules | [Regras de negócio](docs/business-rules.md) | [Business rules](docs/business-rules.en.md) |
| Learning guide | [Guia de aprendizagem](docs/learning-guide.md) | [Learning guide](docs/learning-guide.en.md) |
| Security | [Segurança e limites dos dados](docs/security.md) | [Security and data boundaries](docs/security.en.md) |
| Quality assurance | [Garantia de qualidade](docs/quality-assurance.md) | [Quality assurance](docs/quality-assurance.en.md) |

## Project structure

```text
src/operations_reconciliation/
├── adapters/     # Excel input, output, and local discovery
├── domain/       # Typed domain models
└── services/     # Normalization, consolidation, and comparison

tests/
├── unit/         # Isolated rules and adapter tests
└── integration/  # Excel-to-domain workflow tests

docs/             # Bilingual architecture, rules, learning, security, and QA guides
```

## Excel input contracts

The movement reader accepts `.xls`, `.xlsx`, and `.xlsm` files. It also detects HTML tables exported by Excel and saved with an `.xls` extension. Required movement headers are `Contrato`, `Data da Liberação`, `Situação do Arquivo`, and `Quantidade`; `Tipo da Carga` is optional. Header matching ignores accents, case, and surrounding whitespace. Only `LIBERADO` rows are converted; blank contracts and summary rows such as `Total` are skipped.

The reference reader expects the `Referencia_Principal` worksheet with its header on row 5 by default. It recognizes `Empresa`, `Quantidade consolidada (mmm/YYYY)`, and `Dias de liberação observados` columns by prefix; `Carteira` is optional. The competence is read from the month/year in the quantity header.

Invalid release quantities, invalid release dates, ambiguous headers, and duplicate companies after normalization stop the import with an explicit error. Numeric strings in Brazilian format such as `1.234,50` are supported for movement quantities.

## Safety and data boundaries

Use synthetic example records only. Do not commit employer workbooks, customer names, API tokens, access URLs, board IDs, or internal folder names. The local workflow does not access external services or create tasks. See the [Security guide](docs/security.en.md) for current boundaries and future integration requirements.

---

<a id="português"></a>
# Automação de Conciliação Operacional

[![CI](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/PG-Lima/operations-reconciliation-automation/actions/workflows/ci.yml)

**English** | [Português](#português)

Projeto em Python para conciliar movimentações operacionais mensais com uma referência de programação. Ele demonstra contratos explícitos de dados Excel, descoberta determinística de arquivos locais, regras de domínio, comparação e geração estruturada de relatórios. Seu desenho prioriza a reprodução local e mantém integrações com serviços externos fora do escopo atual.

> Este é um projeto educacional independente. Ele não contém dados de empregadores, credenciais, identificadores de quadros ou conexões com ambientes Microsoft 365 ou Monday.com de empregadores. O fluxo implementado é local; integração com quadros remotos e criação de tarefas não estão disponíveis.

## Objetivos do projeto

Este repositório tem dois objetivos igualmente importantes:

- **Portfólio profissional:** demonstrar habilidades práticas em Python, validação de dados, modelagem de domínio, arquitetura em camadas, automação com Excel e testes automatizados.
- **Recurso aberto de aprendizagem:** permitir que outras pessoas estudem a implementação, reproduzam o fluxo com dados fictícios, compreendam as decisões de projeto e adaptem as ideias a outros contextos e contratos de dados.

## Escopo atual

- Normalizar nomes de empresas e dias previstos.
- Ler e validar planilhas Excel de movimentações e referência.
- Consolidar movimentações `LIBERADO` por empresa e data de liberação.
- Comparar quantidades mensais com uma referência, preservando empresas sem movimentação.
- Classificar empresas como `Aguardando`, `Menor`, `Igual`, `Maior` ou `Não pagou`.
- Separar empresas que não constam na referência.
- Ler movimentações em `.xls`, `.xlsx` e `.xlsm`, incluindo exportações HTML do Excel salvas como `.xls`.
- Ler a referência na aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão.
- Validar colunas obrigatórias, datas, quantidades e chaves de empresa duplicadas antes do processamento.
- Gerar localmente um relatório Excel com sete abas: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou` e `Novas empresas`.
- Descobrir planilhas de movimentação e referência em pastas locais informadas explicitamente, com critérios determinísticos de seleção.

## Requisitos

- Python 3.13 ou superior
- Windows, macOS ou Linux

## Instalação

Crie e ative um ambiente virtual e instale o projeto com as dependências de desenvolvimento:

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

## Documentação

A documentação está disponível em português e inglês:

| Tema | Português | English |
|---|---|---|
| Arquitetura | [Arquitetura](docs/architecture.md) | [Architecture](docs/architecture.en.md) |
| Regras de negócio | [Regras de negócio](docs/business-rules.md) | [Business rules](docs/business-rules.en.md) |
| Aprendizagem | [Guia de aprendizagem](docs/learning-guide.md) | [Learning guide](docs/learning-guide.en.md) |
| Segurança | [Segurança e limites dos dados](docs/security.md) | [Security and data boundaries](docs/security.en.md) |
| Qualidade | [Garantia de qualidade](docs/quality-assurance.md) | [Quality assurance](docs/quality-assurance.en.md) |

## Estrutura do projeto

```text
src/operations_reconciliation/
├── adapters/     # Entrada, saída e descoberta local de planilhas Excel
├── domain/       # Modelos tipados do domínio
└── services/     # Normalização, consolidação e comparação

tests/
├── unit/         # Testes isolados de regras e adaptadores
└── integration/  # Testes do fluxo Excel até o domínio

docs/             # Documentação bilíngue de arquitetura, regras, aprendizagem, segurança e qualidade
```

## Contratos de entrada Excel

O leitor de movimentações aceita arquivos `.xls`, `.xlsx` e `.xlsm`. Também detecta tabelas HTML exportadas pelo Excel e salvas com extensão `.xls`. Os cabeçalhos obrigatórios são `Contrato`, `Data da Liberação`, `Situação do Arquivo` e `Quantidade`; `Tipo da Carga` é opcional. A identificação dos cabeçalhos ignora acentos, maiúsculas/minúsculas e espaços externos. Somente registros `LIBERADO` são convertidos; contratos vazios e linhas de resumo como `Total` são ignorados.

O leitor da referência espera a aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão. Reconhece por prefixo as colunas `Empresa`, `Quantidade consolidada (mmm/AAAA)` e `Dias de liberação observados`; `Carteira` é opcional. A competência é extraída do mês/ano informado no cabeçalho da quantidade consolidada.

Quantidades de liberação inválidas, datas de liberação inválidas, cabeçalhos ambíguos e empresas duplicadas após normalização interrompem a importação com erro explícito. Strings numéricas no padrão brasileiro, como `1.234,50`, são aceitas para quantidades de movimentação.

## Segurança e limites dos dados

Utilize somente registros fictícios. Não envie para o Git planilhas de empregadores, nomes de clientes, tokens de API, URLs de acesso, IDs de quadros ou nomes de pastas internas. O fluxo local não acessa serviços externos nem cria tarefas. Consulte o [guia de Segurança](docs/security.md) para conhecer os limites atuais e os requisitos para futuras integrações.
