# Arquitetura — Projeto Inicial

O projeto está sendo reconstruído como uma aplicação Python independente e organizada em camadas. O script original serve apenas como referência comportamental; nenhum caminho interno, planilha, conta, ID de quadro, token ou configuração de endpoint corporativo será reutilizado.

## Camadas

- **Domínio:** modelos tipados imutáveis e classificações de negócio.
- **Serviços:** regras puras de normalização, consolidação e comparação.
- **Adaptadores:** leitura, descoberta de arquivos e geração de relatórios Excel locais estão implementadas. O gateway de quadro simulado permanece para uma etapa futura.
- **Aplicação (próxima etapa):** orquestração da execução diária e do fechamento mensal.
- **CLI (próxima etapa):** comandos explícitos para demonstração, comparação diária e fechamento mensal.

## Adaptador de entrada Excel

O módulo `adapters/excel_reader.py` converte arquivos externos em modelos tipados do domínio. O leitor de movimentações aceita `.xls`, `.xlsx`, `.xlsm` e exportações HTML do Excel identificadas pelo conteúdo; o leitor da referência espera a aba `Referencia_Principal` e cabeçalho na linha 5 por padrão. Cabeçalhos são localizados por nomes normalizados ou prefixos definidos no contrato de dados. A camada de domínio não depende do Pandas nem conhece nomes de arquivos ou abas.

## Adaptador de saída do relatório Excel

O módulo `adapters/excel_report.py` serializa um `ComparisonReport` já calculado em um arquivo `.xlsx` no caminho local informado pelo chamador. Ele cria a pasta de destino quando necessário e gera as abas `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou` e `Novas empresas`. O adaptador não recalcula classificações, não modifica as planilhas de entrada e não acessa serviços externos.

## Descoberta de arquivos Excel

O módulo `adapters/file_discovery.py` procura somente arquivos diretamente na pasta local informada, sem percorrer subpastas. Arquivos ocultos, arquivos temporários do Excel (`~# Arquitetura — Projeto Inicial

O projeto está sendo reconstruído como uma aplicação Python independente e organizada em camadas. O script original serve apenas como referência comportamental; nenhum caminho interno, planilha, conta, ID de quadro, token ou configuração de endpoint corporativo será reutilizado.

## Camadas

- **Domínio:** modelos tipados imutáveis e classificações de negócio.
- **Serviços:** regras puras de normalização, consolidação e comparação.
- **Adaptadores:** os leitores de movimentações e referência Excel e o gerador de relatório Excel local estão implementados. O gateway de quadro simulado permanece para uma etapa futura.
- **Aplicação (próxima etapa):** orquestração da execução diária e do fechamento mensal.
- **CLI (próxima etapa):** comandos explícitos para demonstração, comparação diária e fechamento mensal.

## Adaptador de entrada Excel

O módulo `adapters/excel_reader.py` converte arquivos externos em modelos tipados do domínio. O leitor de movimentações aceita `.xls`, `.xlsx`, `.xlsm` e exportações HTML do Excel identificadas pelo conteúdo; o leitor da referência espera a aba `Referencia_Principal` e cabeçalho na linha 5 por padrão. Cabeçalhos são localizados por nomes normalizados ou prefixos definidos no contrato de dados. A camada de domínio não depende do Pandas nem conhece nomes de arquivos ou abas.

## Adaptador de saída do relatório Excel

O módulo `adapters/excel_report.py` serializa um `ComparisonReport` já calculado em um arquivo `.xlsx` no caminho local informado pelo chamador. Ele cria a pasta de destino quando necessário e gera as abas `Resumo`, `Aguardando`, `Menor`, `Igual`, `Maior`, `Não pagou` e `Novas empresas`. O adaptador não recalcula classificações, não modifica as planilhas de entrada e não acessa serviços externos.

), arquivos vazios e extensões não suportadas são ignorados. Uma planilha candidata não vazia que falhar na validação interrompe a descoberta com o nome do arquivo no erro.

Para movimentações, a seleção considera apenas registros liberados cuja Data da Liberação pertence à competência solicitada. Vence o arquivo com a maior data de liberação; a data de modificação do arquivo é usada somente como desempate. Se ambos os critérios empatarem, a descoberta falha por ambiguidade. Para referências, a competência extraída do cabeçalho deve corresponder ao mês solicitado e deve existir exatamente um arquivo correspondente.

A descoberta recebe caminhos locais e datas explicitamente informados. Ela não pesquisa OneDrive, SharePoint ou qualquer serviço remoto, e não move, renomeia ou modifica arquivos.

## Limites planejados

A pasta de origem será configurada pelo usuário e representada por um caminho local na demonstração. Esse caminho pode apontar para uma pasta sincronizada por um cliente de nuvem, mas a demonstração não fará login nem conexão com um tenant real do Microsoft 365. Relatórios e histórico serão gravados em uma pasta local de saída.

O adaptador do quadro de tarefas será um simulador local por padrão. A aplicação dependerá de um protocolo pequeno, permitindo introduzir um provedor real futuramente sem colocar chamadas de API dentro das regras de negócio. A demonstração pública inicial não criará tarefas em uma conta real do Monday.com.

## Segurança do fechamento mensal

O fechamento precisa ser repetível após falhas parciais. A geração do relatório e o processamento de tarefas ocorrem antes da promoção da referência. A criação de tarefas é idempotente usando empresa normalizada mais competência. A promoção da referência utiliza uma planilha temporária validada e preserva a versão anterior no histórico. Se a validação da entrada ou o processamento das tarefas falhar, a referência vigente deve continuar disponível para nova tentativa.
