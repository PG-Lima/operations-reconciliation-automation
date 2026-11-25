# Regras de Negócio — Conciliação

Este documento registra as regras extraídas do fluxo operacional original e implementadas nas etapas de domínio, leitura Excel e geração do relatório. A nova implementação é independente e não utiliza dados reais de nenhuma empresa.

## Entrada e elegibilidade

1. O leitor de movimentações aceita `.xls`, `.xlsx` e `.xlsm`, além de HTML do Excel salvo com extensão `.xls`.
2. A planilha de movimentações precisa conter `Contrato`, `Data da Liberação`, `Situação do Arquivo` e `Quantidade`; `Tipo da Carga` é opcional.
3. A referência é lida da aba `Referencia_Principal`, com cabeçalho na linha 5 por padrão. São obrigatórias as colunas iniciadas por `Empresa`, `Quantidade consolidada` e `Dias de liberação observados`; `Carteira` é opcional.
4. A competência da referência é extraída do mês/ano no cabeçalho `Quantidade consolidada (mmm/AAAA)`, quando reconhecido.
5. Os nomes de cabeçalhos são comparados sem diferenciar acentos, caixa ou espaços externos; cabeçalhos duplicados após essa normalização são ambíguos e interrompem a leitura.
6. Quantidades de movimentação em texto podem usar o padrão brasileiro, por exemplo `1.234,50`.
7. Somente registros com situação `LIBERADO` participam da consolidação.
8. Contratos sem nome e linhas de resumo como `nan` ou `Total` são ignorados.
9. Um registro `LIBERADO` com nome de empresa impossível de normalizar, quantidade inválida ou data de liberação inválida deve interromper o processamento, em vez de alterar os totais silenciosamente.
10. O período analisado começa no primeiro dia do mês da data de corte e termina na própria data de corte.
11. A competência é determinada pela Data da Liberação. Um campo separado de mês da carga não a substitui.

## Consolidação

1. A identidade da empresa é normalizada removendo acentos, pontuação, diferenças entre maiúsculas/minúsculas e espaços repetidos.
2. As quantidades são somadas por empresa normalizada.
3. A consolidação preserva as datas da primeira e da última liberação, os dias únicos de liberação, a quantidade de registros liberados e os tipos de carga únicos.
4. O nome original da empresa é preservado para exibição; a chave normalizada é utilizada apenas para cruzamentos.

## Comparação

1. Todas as empresas da referência permanecem no resultado, inclusive aquelas sem movimentação liberada.
2. Uma empresa ausente da referência é apresentada separadamente como `Sem referência`; ela não é comparada com uma quantidade esperada.
3. O último dia previsto é o maior dia válido informado na referência. Um dia superior ao último dia do calendário é limitado ao último dia daquele mês.
4. A empresa permanece como `Aguardando` durante o próprio último dia previsto. A classificação definitiva começa no dia seguinte.
5. Quantidade esperada ausente/negativa ou dias previstos ausentes/inválidos resultam em `Aguardando`, com observação para revisão.
6. Depois do prazo:
   - `Igual`: quantidade liberada igual à esperada, dentro da tolerância de `1e-9`.
   - `Maior`: quantidade liberada acima da referência.
   - `Não pagou`: nenhuma liberação registrada.
   - `Menor`: houve liberação, mas o total ficou abaixo do esperado.
7. Uma quantidade acima da referência não substitui o status `Aguardando` antes do prazo previsto.

## Relatório Excel

1. O relatório é gerado a partir de um `ComparisonReport` já calculado; o adaptador de saída não executa novamente as regras de comparação.
2. O arquivo é salvo localmente no caminho `.xlsx` informado pelo chamador. A pasta de destino é criada quando necessário.
3. A aba `Resumo` apresenta contagens de empresas, totais liberados e quantidades por classificação.
4. As abas `Aguardando`, `Menor`, `Igual`, `Maior` e `Não pagou` contêm somente as empresas da respectiva classificação.
5. A aba `Novas empresas` apresenta movimentações de empresas ausentes da referência, sem compará-las com uma quantidade esperada.
6. A geração do relatório não modifica as planilhas de entrada nem acessa serviços externos.

## Fechamento mensal — fluxo planejado

1. A competência anterior é fechada na primeira segunda-feira do novo mês ou na primeira execução posterior, caso a máquina agendada estivesse indisponível.
2. A planilha de fechamento é selecionada pela maior Data da Liberação válida dentro da competência; a data de modificação do arquivo é apenas critério de desempate.
3. A maior data real de liberação define o corte. Não é necessário haver movimentação no último dia do calendário.
4. A competência é avaliada no primeiro dia do mês seguinte, garantindo que o último dia previsto já tenha passado.
5. O relatório final é gerado e os itens `Menor` são processados antes da promoção da nova referência mensal.
6. A nova referência contém empresas com pelo menos um registro liberado no mês fechado. Empresas sem movimentação são removidas; empresas novas são adicionadas.
7. Se não for possível selecionar ou validar uma fonte de fechamento, a referência vigente é preservada e a comparação da nova competência é interrompida.

## Integração com quadro de tarefas — fluxo planejado

1. Somente empresas classificadas como `Menor` geram tarefas.
2. O título da tarefa contém empresa e competência; esse par é a chave de deduplicação.
3. Tarefas existentes são ignoradas, inclusive quando uma execução anterior terminou parcialmente.
4. A tarefa é criada somente com o título; outras colunas não são preenchidas.
5. Testes automatizados e demonstrações utilizam um quadro simulado local. Um conector de API real não faz parte da etapa atual.
