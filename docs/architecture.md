# Arquitetura — Automação de Conciliação Operacional

O projeto é uma aplicação Python independente, organizada em camadas, para conciliar movimentações operacionais com uma referência de programação. O script original é utilizado apenas como referência comportamental. Caminhos internos, planilhas corporativas, credenciais, identificadores de quadros e configurações de serviços externos não fazem parte desta implementação pública.

## Visão geral

A execução local é coordenada por `application/reconciliation.py`, por meio da função `run_reconciliation()`. Ela recebe os diretórios das planilhas de movimentação e referência, a competência, a data de corte e o caminho do relatório de saída. A data de avaliação é opcional.

O fluxo atual segue estas etapas:

1. Validar a relação entre a competência, a data de corte e a data de avaliação.
2. Descobrir as planilhas de movimentação e referência correspondentes.
3. Ler e validar os dados dos arquivos selecionados.
4. Consolidar as movimentações liberadas.
5. Comparar os resultados com a referência e aplicar as classificações do domínio.
6. Gerar o relatório Excel no destino informado.
7. Retornar um `ReconciliationResult` com os caminhos dos arquivos selecionados, o resultado da comparação e o caminho do relatório.

## Camadas da aplicação

- **Domínio (`domain/`):** modelos tipados e imutáveis que representam os dados e resultados da conciliação.
- **Serviços (`services/`):** regras de normalização, consolidação de movimentações, comparação e seleção de empresas `Menor` para tarefas simuladas. As regras não dependem de arquivos Excel ou serviços externos.
- **Adaptadores (`adapters/`):** leitura e validação das planilhas Excel, descoberta de arquivos locais, geração do relatório Excel e persistência do quadro de tarefas simulado.
- **Aplicação (`application/`):** coordena os adaptadores e serviços para executar o fluxo completo de uma conciliação local.
- **CLI (`cli.py`):** interpreta os argumentos do terminal, valida o formato das datas e chama a função de aplicação sem duplicar regras de negócio.

## Adaptador de entrada Excel

O módulo `adapters/excel_reader.py` converte os arquivos de origem em modelos tipados do domínio.

O leitor de movimentações aceita arquivos `.xls`, `.xlsx` e `.xlsm`. Também reconhece exportações HTML do Excel identificadas pelo conteúdo, mesmo quando salvas com a extensão `.xls`.

O leitor da referência espera a planilha `Referencia_Principal` e utiliza a linha 5 como cabeçalho por padrão. Os cabeçalhos são identificados por nomes normalizados ou pelos prefixos definidos no contrato de dados.

A camada de domínio não depende do Pandas e não precisa conhecer nomes de arquivos, abas ou detalhes de apresentação das planilhas.

## Adaptador de saída do relatório Excel

O módulo `adapters/excel_report.py` transforma um `ComparisonReport` já calculado em um arquivo `.xlsx` no caminho local informado pelo chamador.

O relatório contém sete planilhas: `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou` e `Novas empresas`.

O adaptador cria o diretório de destino quando necessário. Ele não recalcula classificações, não altera as planilhas de entrada e não acessa serviços externos.

## Descoberta de arquivos Excel

O módulo `adapters/file_discovery.py` procura arquivos somente no diretório local informado, sem percorrer subpastas.

Arquivos ocultos, arquivos temporários do Excel, arquivos vazios e extensões não suportadas são ignorados. Uma planilha candidata não vazia que falhar na validação interrompe a descoberta e informa o nome do arquivo.

Para as movimentações, são considerados os registros liberados cuja data de liberação pertence à competência solicitada. A seleção prioriza a maior data de liberação; a data de modificação do arquivo é utilizada apenas como critério de desempate. Se os critérios continuarem empatados, a descoberta falha por ambiguidade.

Para a referência, a competência extraída do cabeçalho deve corresponder à competência solicitada, e deve existir exatamente um arquivo correspondente.

A descoberta recebe caminhos locais e datas explicitamente informados. Não pesquisa OneDrive, SharePoint ou outros serviços remotos, e não move, renomeia ou modifica arquivos.

## Orquestração de uma execução

A função `run_reconciliation()` coordena o fluxo descrito nesta documentação. A data de avaliação, quando omitida, assume o valor da data de corte.

A aplicação rejeita:
- Uma data de corte cuja competência não corresponda à competência solicitada.
- Uma data de avaliação anterior à data de corte.
- Um caminho de saída que sobrescreveria uma das planilhas de entrada.

Ao concluir, a função retorna um `ReconciliationResult` com as planilhas selecionadas, o relatório de comparação e o caminho do arquivo de saída.

## Interface de linha de comando

O entry point `operations-reconciliation` disponibiliza o subcomando `reconcile`. Ele recebe os diretórios de movimentações e referência, a competência no formato `YYYY-MM`, a data de corte, o caminho de saída e, opcionalmente, a data de avaliação.

A CLI valida os formatos de entrada e delega o processamento para `run_reconciliation()`. Ela não implementa descoberta, leitura, comparação ou geração de planilhas por conta própria. O código de saída é `0` em caso de sucesso, `1` para falhas da execução e `2` para argumentos inválidos tratados pelo argparse.

## Simulação local do quadro de tarefas

O adaptador `adapters/local_task_board.py` persiste o quadro simulado em um arquivo JSON local. Cada tarefa visível possui somente o título; a identidade interna é armazenada com a empresa normalizada e a competência para permitir deduplicação em reexecuções.

O serviço `services/task_creation.py` seleciona exclusivamente linhas com classificação `Menor` e constrói o título `Empresa - YYYY-MM`. A aplicação executa essa etapa somente quando `task_board_path` é fornecido. O arquivo é validado antes de ser atualizado, e a gravação utiliza arquivo temporário e substituição atômica. O simulador destina-se a execuções sequenciais locais; não oferece coordenação entre escritores concorrentes.

O relatório Excel é gravado antes da simulação do quadro. Portanto, uma falha ao ler ou atualizar o arquivo JSON pode encerrar a execução com erro, embora o relatório já tenha sido produzido.

## Limites da implementação atual

A execução é local e depende dos diretórios e das datas fornecidos pelo chamador. O projeto não realiza autenticação em serviços remotos, não acessa diretamente ambientes Microsoft 365 ou Monday.com e não cria tarefas em quadros externos. A simulação local é opcional e não substitui uma integração real.

A aplicação não agenda execuções, não implementa fechamento mensal e não promove ou arquiva planilhas de referência.

As planilhas de origem são utilizadas para leitura e não devem ser modificadas pelo fluxo de conciliação. A geração do relatório ocorre em um caminho de saída separado, e a aplicação impede que esse caminho sobrescreva os arquivos de entrada selecionados.

## Próximas etapas planejadas

A próxima evolução prevista é um fluxo de fechamento mensal com arquivamento e promoção controlada da referência.

Essas funcionalidades são planejamento e não fazem parte do fluxo implementado atualmente.

## Diretrizes planejadas para o fechamento mensal

Quando o fechamento mensal for implementado, deverá ser repetível após falhas parciais. A referência vigente deverá permanecer disponível caso a validação dos dados ou o processamento de tarefas falhe.

O desenho previsto inclui validar uma planilha temporária antes da promoção da referência, preservar a versão anterior no histórico e tornar a criação de tarefas idempotente, utilizando uma chave de negócio formada pela empresa normalizada e pela competência.

Essas são diretrizes para uma etapa futura, não garantias de comportamento da implementação atual.