# Regras de Negócio — Conciliação

Este documento registra as regras do fluxo de conciliação, distinguindo o comportamento implementado das regras propostas para etapas futuras. A implementação pública é independente e utiliza apenas dados fictícios.

## Entrada e elegibilidade

1. O leitor de movimentações aceita `.xls`, `.xlsx` e `.xlsm`, além de HTML do Excel salvo com extensão `.xls`.
2. A planilha de movimentações precisa conter `Contrato`, `Data da Liberação`, `Situação do Arquivo` e `Quantidade`; `Tipo da Carga` é opcional.
3. A referência é lida da aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão. São obrigatórias as colunas iniciadas por `Empresa`, `Quantidade consolidada` e `Dias de liberação observados`; `Carteira` é opcional.
4. A competência da referência é extraída do mês e ano no cabeçalho `Quantidade consolidada (mmm/AAAA)`, quando reconhecido.
5. Os nomes dos cabeçalhos são comparados sem diferenciar acentos, caixa ou espaços externos. Cabeçalhos duplicados após essa normalização são ambíguos e interrompem a leitura.
6. Quantidades de movimentação em texto podem usar o padrão brasileiro, por exemplo `1.234,50`.
7. Somente registros com situação `LIBERADO` participam da consolidação.
8. Contratos sem nome e linhas de resumo como `nan` ou `Total` são ignorados.
9. Um registro `LIBERADO` com nome de empresa impossível de normalizar, quantidade inválida ou data de liberação inválida interrompe o processamento, em vez de alterar os totais silenciosamente.
10. O período analisado começa no primeiro dia do mês da data de corte e termina na própria data de corte.
11. A competência é determinada pela Data da Liberação. Um campo separado de mês da carga não a substitui.

## Descoberta de arquivos Excel

1. A busca ocorre somente na pasta local informada, sem percorrer subpastas.
2. Arquivos ocultos, arquivos temporários do Excel iniciados por `~$`, arquivos vazios e extensões não suportadas são ignorados.
3. Uma planilha candidata não vazia que não puder ser lida ou validada interrompe a descoberta com um erro que identifica o arquivo.
4. A descoberta de movimentações considera somente registros `LIBERADO` cuja Data da Liberação pertença à competência solicitada.
5. A planilha de movimentações selecionada é a que contém a maior Data da Liberação dentro da competência. A data de modificação do arquivo é utilizada somente quando as maiores datas de liberação empatam.
6. Se duas ou mais planilhas de movimentações empatarem tanto na maior Data da Liberação quanto na data de modificação, a descoberta é interrompida por ambiguidade.
7. A descoberta da referência exige que a competência extraída do cabeçalho corresponda ao mês solicitado e que exista exatamente uma planilha correspondente. Ausência ou duplicidade interrompe o processo.
8. A descoberta não move, renomeia, sobrescreve ou modifica os arquivos de origem e não acessa serviços remotos.

## Consolidação

1. A identidade da empresa é normalizada removendo acentos, pontuação, diferenças entre maiúsculas e minúsculas e espaços repetidos.
2. As quantidades são somadas por empresa normalizada.
3. A consolidação preserva as datas da primeira e da última liberação, os dias únicos de liberação, a quantidade de registros liberados e os tipos de carga únicos.
4. O nome original da empresa é preservado para exibição; a chave normalizada é utilizada apenas para cruzamentos.

## Comparação

1. Todas as empresas da referência permanecem no resultado, inclusive aquelas sem movimentação liberada.
2. Uma empresa ausente da referência é apresentada separadamente como `Sem referência`; ela não é comparada com uma quantidade esperada.
3. O último dia previsto é o maior dia válido informado na referência. Um dia superior ao último dia do calendário é limitado ao último dia daquele mês.
4. A empresa permanece como `Aguardando` durante o próprio último dia previsto. A classificação definitiva começa no dia seguinte.
5. Quantidade esperada ausente ou negativa, ou dias previstos ausentes ou inválidos, resultam em `Aguardando`, com observação para revisão.
6. Depois do prazo:
   - `Igual`: quantidade liberada igual à esperada, dentro da tolerância de `1e-9`.
   - `Maior`: quantidade liberada acima da referência.
   - `Não pagou`: nenhuma liberação registrada.
   - `Menor`: houve liberação, mas o total ficou abaixo do esperado.
7. Uma quantidade acima da referência não substitui o status `Aguardando` antes do prazo previsto.

## Orquestração de uma execução

A função `run_reconciliation()` coordena uma execução local completa:

1. A data de corte deve pertencer à competência solicitada.
2. A data de avaliação, quando informada, não pode ser anterior à data de corte. Quando omitida, assume a data de corte.
3. A aplicação descobre as planilhas correspondentes, lê e valida os dados, consolida as movimentações, executa a comparação e gera o relatório.
4. O caminho de saída não pode corresponder ao caminho de uma das planilhas de entrada selecionadas.
5. A função retorna um `ReconciliationResult` com os caminhos dos arquivos selecionados, o resultado da comparação e o caminho do relatório.

Essa orquestração é local. A criação de tarefas simuladas ocorre somente quando um caminho `--task-board` é fornecido. O fluxo não agenda execuções, não cria tarefas em quadros externos, não promove referências e não acessa serviços remotos.

## Relatório Excel

1. O relatório é gerado a partir de um `ComparisonReport` já calculado; o adaptador de saída não executa novamente as regras de comparação.
2. O arquivo é salvo localmente no caminho `.xlsx` informado pelo chamador. A pasta de destino é criada quando necessário.
3. A aba `Resumo` apresenta contagens de empresas, totais liberados e quantidades por classificação.
4. As abas `Aguardando`, `Menor`, `Igual`, `Maior` e `Não pagou` contêm somente as empresas da respectiva classificação.
5. A aba `Novas empresas` apresenta movimentações de empresas ausentes da referência, sem compará-las com uma quantidade esperada.
6. A geração do relatório não modifica as planilhas de entrada nem acessa serviços externos.

## Fechamento mensal — fluxo planejado

As regras abaixo descrevem uma evolução futura e não fazem parte do fluxo implementado atualmente.

1. A competência anterior será fechada na primeira segunda-feira do novo mês ou na primeira execução posterior, caso a máquina agendada estivesse indisponível.
2. A planilha de fechamento será selecionada pela maior Data da Liberação válida dentro da competência; a data de modificação do arquivo será apenas critério de desempate.
3. A maior data real de liberação definirá o corte. Não será necessário haver movimentação no último dia do calendário.
4. A competência será avaliada no primeiro dia do mês seguinte, garantindo que o último dia previsto já tenha passado.
5. O relatório final será gerado e os itens `Menor` serão processados antes da promoção da nova referência mensal.
6. A nova referência conterá empresas com pelo menos um registro liberado no mês fechado. Empresas sem movimentação serão removidas; empresas novas serão adicionadas.
7. Se não for possível selecionar ou validar uma fonte de fechamento, a referência vigente será preservada e a comparação da nova competência será interrompida.

## Simulação local do quadro de tarefas

1. A simulação é opcional e só é executada quando o chamador fornece um caminho JSON por meio do argumento `--task-board` ou de `task_board_path` na aplicação.
2. Somente empresas classificadas como `Menor` geram tarefas. Empresas `Aguardando`, `Igual`, `Maior`, `Não pagou` e `Sem referência` não geram tarefas.
3. O título visível contém o nome da empresa e a competência no formato `Empresa - YYYY-MM`.
4. A chave interna de deduplicação é formada pelo nome normalizado da empresa e pela competência `YYYY-MM`. Reexecuções ignoram chaves já existentes, inclusive após uma execução anterior interrompida.
5. A tarefa visível contém somente o título. A chave da empresa e a competência são metadados internos necessários para a deduplicação, não campos de tarefa adicionais.
6. O quadro é persistido em JSON local, usa versão de esquema e grava atualizações por substituição atômica do arquivo temporário.
7. Um arquivo JSON inválido, corrompido ou com identidades duplicadas interrompe a execução; o simulador não descarta silenciosamente o estado existente.
8. A simulação não acessa APIs, não autentica em Monday.com e não cria tarefas em quadros externos. O arquivo local deve ser protegido e não deve conter dados reais de empregadores ou clientes.
