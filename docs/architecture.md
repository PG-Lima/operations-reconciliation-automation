# Arquitetura — Projeto Inicial

O projeto está sendo reconstruído como uma aplicação Python independente e organizada em camadas. O script original serve apenas como referência comportamental; nenhum caminho interno, planilha, conta, ID de quadro, token ou configuração de endpoint corporativo será reutilizado.

## Camadas

- **Domínio:** modelos tipados imutáveis e classificações de negócio.
- **Serviços:** regras puras de normalização, consolidação e comparação.
- **Adaptadores (próxima etapa):** leitores/gravadores Excel, armazenamento em pasta local sincronizada e gateway de quadro simulado.
- **Aplicação (próxima etapa):** orquestração da execução diária e do fechamento mensal.
- **CLI (próxima etapa):** comandos explícitos para demonstração, comparação diária e fechamento mensal.

## Limites planejados

A pasta de origem será configurada pelo usuário e representada por um caminho local na demonstração. Esse caminho pode apontar para uma pasta sincronizada por um cliente de nuvem, mas a demonstração não fará login nem conexão com um tenant real do Microsoft 365. Relatórios e histórico serão gravados em uma pasta local de saída.

O adaptador do quadro de tarefas será um simulador local por padrão. A aplicação dependerá de um protocolo pequeno, permitindo introduzir um provedor real futuramente sem colocar chamadas de API dentro das regras de negócio. A demonstração pública inicial não criará tarefas em uma conta real do Monday.com.

## Segurança do fechamento mensal

O fechamento precisa ser repetível após falhas parciais. A geração do relatório e o processamento de tarefas ocorrem antes da promoção da referência. A criação de tarefas é idempotente usando empresa normalizada mais competência. A promoção da referência utiliza uma planilha temporária validada e preserva a versão anterior no histórico. Se a validação da entrada ou o processamento das tarefas falhar, a referência vigente deve continuar disponível para nova tentativa.
