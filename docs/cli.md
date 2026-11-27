# Interface de linha de comando

A interface de linha de comando permite executar uma conciliação local sem escrever um script Python que chame diretamente a função de aplicação.

## Instalação

Com o ambiente virtual ativo, instale o projeto e as dependências:

```powershell
python -m pip install -e ".[dev]"
```

O pacote registra o comando `operations-reconciliation` no ambiente Python ativo.

## Executar uma conciliação

```powershell
operations-reconciliation reconcile --movement-dir "data/movements" --reference-dir "data/references" --competence 2026-11 --cutoff-date 2026-11-12 --output "output/reconciliation.xlsx" --evaluation-date 2026-11-13 --task-board "local-state/task-board.json"
```

### Argumentos

| Argumento | Obrigatório | Descrição |
|---|---|---|
| `reconcile` | Sim | Subcomando para executar uma conciliação. |
| `--movement-dir` | Sim | Pasta local com as planilhas de movimentação. |
| `--reference-dir` | Sim | Pasta local com a planilha de referência. |
| `--competence` | Sim | Competência no formato `YYYY-MM`. |
| `--cutoff-date` | Sim | Última data de liberação incluída, no formato `YYYY-MM-DD`. |
| `--output` | Sim | Caminho local do relatório de saída, com extensão `.xlsx`. |
| `--evaluation-date` | Não | Data usada para avaliar as classificações. Quando omitida, assume a data de corte. |
| `--task-board` | Não | Caminho de um arquivo `.json` para persistir a simulação local. Quando omitido, nenhuma tarefa é simulada. |

A CLI valida o formato da competência e das datas antes de chamar `run_reconciliation()`. As regras de negócio, a descoberta dos arquivos, a leitura das planilhas, a comparação e a geração do relatório permanecem na aplicação e nos adaptadores existentes. Quando `--task-board` é informado, somente empresas `Menor` geram tarefas simuladas com título `Empresa - YYYY-MM`; reexecuções ignoram identidades já armazenadas. O diretório `local-state/` é ignorado pelo Git por padrão.

Os diretórios e arquivos de entrada precisam existir e atender aos [contratos Excel](learning-guide.md#entender-os-contratos-das-planilhas). A descoberta procura arquivos diretamente nas pastas informadas e não percorre subpastas.

## Códigos de saída

- `0`: conciliação concluída e relatório gerado.
- `1`: falha durante a execução, como arquivo ausente, planilha inválida, parâmetros incompatíveis ou quadro JSON inválido. Como o relatório é gerado antes da simulação, ele pode já existir quando ocorrer uma falha no quadro.
- `2`: argumentos ausentes ou inválidos, tratados pelo argparse.

A CLI não cria dados de exemplo, não agenda execuções, não acessa serviços remotos, não cria tarefas em quadros externos e não modifica as planilhas de origem. O argumento `--task-board` habilita somente a simulação local.

## Verificação

Execute os testes da interface:

```powershell
python -m pytest tests/unit/test_cli.py -v
```

Execute também a suíte completa de qualidade antes de propor mudanças.
