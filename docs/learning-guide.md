# Guia de aprendizagem — Automação de Conciliação Operacional

Este guia apresenta um caminho para estudar o projeto, reproduzir o fluxo de conciliação com dados fictícios e adaptar a implementação a outro contexto. O repositório tem dois objetivos de igual importância: servir como portfólio profissional e como recurso aberto de aprendizagem.

## O que você vai aprender

- Organizar uma aplicação Python em camadas de domínio, serviços, adaptadores e aplicação.
- Validar e interpretar planilhas Excel com contratos de dados explícitos.
- Normalizar e consolidar registros antes de compará-los com uma referência.
- Separar regras de negócio de operações de entrada e saída de arquivos.
- Coordenar um fluxo completo e testá-lo com arquivos sintéticos.
- Utilizar Pytest, cobertura de código e Ruff em um projeto Python.

## Pré-requisitos

- Python 3.13 ou superior.
- Git.
- Familiaridade básica com terminal, ambientes virtuais e Python.
- Conhecimento básico de planilhas Excel.

A integração contínua deste repositório executa os testes com Python 3.14. O projeto também pode ser instalado em ambientes compatíveis com Python 3.13 ou superior.

## Preparar o ambiente

Clone o repositório e entre na pasta:

```bash
git clone https://github.com/PG-Lima/operations-reconciliation-automation.git
cd operations-reconciliation-automation
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative-o no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No macOS ou Linux:

```bash
source .venv/bin/activate
```

Instale o projeto e as dependências de desenvolvimento:

```bash
python -m pip install -e ".[dev]"
```

## Reproduzir o fluxo completo

O fluxo pode ser executado pela CLI com planilhas fictícias que atendam aos contratos descritos neste guia. O teste de integração também permanece disponível como demonstração reproduzível de ponta a ponta:

```bash
python -m pytest tests/integration/test_application_workflow_integration.py -v
```

Esse teste cria planilhas Excel fictícias em diretórios temporários, executa a aplicação real e verifica o relatório produzido. Nenhuma planilha corporativa ou conexão remota é necessária.

O cenário de teste usa:

- Uma planilha de movimentações com registros liberados e pendentes.
- Uma planilha de referência na aba `Referencia_Principal`, com cabeçalho na linha 5.
- Duas liberações da empresa ACME, totalizando 50 unidades.
- Uma empresa Beta presente na referência, mas sem movimentação liberada.
- Uma empresa nova, ausente da referência, com 5 unidades liberadas.

A execução considera competência novembro de 2026, data de corte em 12 de novembro e data de avaliação em 13 de novembro. O teste verifica as classificações, os totais, as sete abas do relatório e a preservação dos arquivos de origem.

## Executar pela linha de comando

Com o ambiente virtual ativo e o projeto instalado com `python -m pip install -e ".[dev]"`, execute o comando abaixo no PowerShell, ajustando os diretórios e datas para os arquivos fictícios preparados:

```powershell
operations-reconciliation reconcile --movement-dir "examples/data/movements" --reference-dir "examples/data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13
```

A competência usa `YYYY-MM`; as datas usam `YYYY-MM-DD`. A data de avaliação pode ser omitida, caso em que será utilizada a data de corte. O comando imprime os caminhos dos arquivos selecionados e do relatório gerado. Ele não cria as planilhas de entrada: os diretórios e arquivos devem existir e seguir os contratos deste guia.

Consulte [Interface de linha de comando](cli.md) para ver todos os argumentos e códigos de saída.

## Entender os contratos das planilhas

### Planilha de movimentações

O leitor aceita `.xls`, `.xlsx` e `.xlsm`, além de exportações HTML do Excel identificadas pelo conteúdo e salvas com extensão `.xls`.

As colunas obrigatórias são:

- `Contrato`
- `Data da Liberação`
- `Situação do Arquivo`
- `Quantidade`

A coluna `Tipo da Carga` é opcional. Somente registros com situação `LIBERADO` participam da consolidação. Contratos vazios e linhas de resumo, como `Total`, são ignorados.

### Planilha de referência

O leitor espera a aba `Referencia_Principal` e o cabeçalho na linha 5 por padrão. As colunas reconhecidas incluem:

- `Empresa`
- `Quantidade consolidada (mmm/AAAA)`
- `Dias de liberação observados`

A coluna `Carteira` é opcional. A competência é extraída do mês e ano no cabeçalho da quantidade consolidada.

Os nomes dos cabeçalhos são normalizados para desconsiderar acentos, caixa e espaços externos. Cabeçalhos ambíguos, datas inválidas, quantidades inválidas e empresas duplicadas após normalização interrompem a leitura com erro explícito.

Consulte [Regras de Negócio](business-rules.md) para os critérios detalhados e exemplos de classificação.

## Usar a função de aplicação

A função que coordena uma execução é `run_reconciliation()`, em `src/operations_reconciliation/application/reconciliation.py`.

Exemplo de chamada para quem já preparou planilhas fictícias de acordo com os contratos acima:

```python
from datetime import date
from pathlib import Path

from operations_reconciliation.application.reconciliation import run_reconciliation

result = run_reconciliation(
    movement_directory=Path("examples/data/movements"),
    reference_directory=Path("examples/data/references"),
    competence=date(2026, 11, 1),
    cutoff_date=date(2026, 11, 12),
    output_path=Path("output/reconciliation.xlsx"),
    evaluation_date=date(2026, 11, 13),
)

print(f"Movement workbook: {result.movement_workbook}")
print(f"Reference workbook: {result.reference_workbook}")
print(f"Report: {result.output_workbook}")
```

Os caminhos do exemplo são ilustrativos: as pastas e planilhas precisam existir e obedecer aos contratos de entrada. A descoberta procura somente os arquivos diretamente dentro das pastas informadas; ela não percorre subpastas.

A data de corte deve pertencer à competência solicitada. Quando informada, a data de avaliação não pode ser anterior à data de corte. Se a data de avaliação for omitida, a aplicação utiliza a data de corte. O caminho de saída não pode apontar para uma das planilhas de entrada selecionadas.

A função retorna um `ReconciliationResult` com os caminhos das planilhas selecionadas, o relatório de comparação e o caminho do arquivo gerado.

## Caminho recomendado para ler o código

1. `domain/models.py`: comece pelos modelos e estruturas que representam os dados e resultados.
2. `services/normalization.py`: entenda como os nomes e valores são normalizados.
3. `services/consolidation.py`: acompanhe a agregação das movimentações liberadas.
4. `services/comparison.py`: estude as classificações e a comparação com a referência.
5. `adapters/excel_reader.py`: veja como as planilhas são convertidas em dados do domínio.
6. `adapters/file_discovery.py`: entenda os critérios de seleção dos arquivos locais.
7. `adapters/excel_report.py`: acompanhe a criação das sete abas do relatório.
8. `application/reconciliation.py`: por último, veja como a aplicação coordena todas as etapas.

Use os testes unitários para entender casos isolados e o teste `test_application_workflow_integration.py` para observar a execução ponta a ponta.

## Executar a suíte de qualidade

Execute todos os testes com cobertura de linhas e branches:

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
```

Execute a análise estática:

```bash
python -m ruff check src tests
```

A configuração exige cobertura mínima de 100% e habilita a medição de branches. Consulte [Garantia de Qualidade](quality-assurance.md) para conhecer a estratégia, o significado dessas métricas e a automação de CI.

## Adaptar o projeto a outro contexto

Antes de alterar o código, identifique as diferenças entre o novo cenário e os contratos atuais.

1. Documente as colunas, formatos, identificadores e regras das novas fontes de dados.
2. Altere os adaptadores de entrada para interpretar o novo formato sem levar detalhes de planilhas para o domínio.
3. Revise as regras de normalização, consolidação e comparação nos serviços.
4. Atualize os modelos de domínio somente quando os conceitos de negócio realmente mudarem.
5. Atualize ou crie testes unitários e de integração com dados fictícios.
6. Execute a suíte completa e o Ruff antes de propor a alteração.

Não reutilize dados reais de empregadores ou clientes nos exemplos, testes ou commits. Consulte [Segurança](security.md) antes de introduzir novos caminhos de dados ou integrações.

## Limites atuais

O fluxo documentado é local. Não há agendamento, integração com Monday.com, criação de tarefas, fechamento mensal automático ou promoção de referência implementados nesta etapa. Esses itens são planejados e não devem ser tratados como funcionalidades disponíveis.

A CLI executa o fluxo com planilhas fornecidas pelo usuário; o teste de integração continua sendo a demonstração autossuficiente que cria os próprios arquivos sintéticos.
