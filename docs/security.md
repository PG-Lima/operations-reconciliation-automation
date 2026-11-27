# Segurança e limites dos dados

Este documento descreve os limites de segurança da implementação atual e orienta o uso do repositório como projeto público de portfólio e aprendizagem. Ele não é uma certificação de segurança nem uma avaliação formal de risco.

## Escopo de segurança atual

A execução implementada é local. O fluxo recebe caminhos de diretórios e datas, lê planilhas Excel, calcula a conciliação e grava um relatório no caminho informado.

A implementação atual:

- Não autentica em Microsoft 365, SharePoint, OneDrive ou Monday.com.
- Não envia planilhas para serviços remotos.
- Não cria tarefas ou itens em quadros externos.
- Não armazena credenciais ou tokens para conectores remotos.
- Não agenda execuções nem executa o fechamento mensal planejado.

A descoberta de arquivos examina somente os arquivos diretamente contidos nos diretórios fornecidos. Ela não percorre subpastas. Arquivos ocultos, temporários do Excel, vazios e com extensões não suportadas são ignorados. Uma planilha candidata não vazia que falhe na validação interrompe a descoberta com erro explícito.

## Dados permitidos no repositório público

Utilize somente dados fictícios, sintéticos ou criados especificamente para demonstração.

Não adicione ao repositório:

- Planilhas exportadas de empregadores, clientes ou fornecedores.
- Nomes reais de clientes, contratos, empregados ou parceiros.
- Dados pessoais, financeiros, operacionais ou comerciais não públicos.
- Senhas, tokens, chaves de API, cookies ou arquivos de sessão.
- URLs internas, nomes de servidores, caminhos corporativos ou identificadores de quadros.
- Capturas de tela que revelem informações internas.

Antes de adicionar um arquivo, revise seu conteúdo e também metadados, nomes de abas, comentários, fórmulas, propriedades do documento e nomes de arquivos. Dados aparentemente fictícios podem conter informações reais em campos auxiliares ou metadados.

## Validação e integridade dos arquivos

Os leitores verificam os contratos esperados das planilhas, incluindo colunas obrigatórias, datas, quantidades e chaves de empresa duplicadas após normalização. Registros inválidos não devem ser silenciosamente convertidos em resultados válidos.

A descoberta falha quando uma planilha candidata não vazia não pode ser validada ou quando a seleção de arquivos é ambígua. Esse comportamento evita escolher silenciosamente uma fonte incorreta.

A aplicação também verifica se:

- A data de corte pertence à competência solicitada.
- A data de avaliação, quando informada, não antecede a data de corte.
- O caminho de saída não corresponde ao caminho de uma das planilhas de entrada selecionadas.

O fluxo de conciliação lê as planilhas de origem e gera o relatório em um destino separado. Ainda assim, utilize cópias de trabalho e mantenha os arquivos originais protegidos por seus próprios controles de acesso e backup.

## Proteção do relatório gerado

O relatório pode conter informações derivadas das planilhas processadas. Escolha uma pasta de saída apropriada, com acesso restrito quando os dados assim exigirem.

Não publique relatórios reais em commits, issues, pull requests, mensagens de CI ou capturas de tela. A aplicação não implementa criptografia do arquivo, controle de acesso, retenção, descarte seguro ou anonimização automática do relatório.

## Segredos e configurações

A execução local atual não exige credenciais ou tokens de API. Não inclua segredos no código, nos testes, no README, nos exemplos, nas mensagens de erro ou nos commits.

Se uma integração externa for desenvolvida futuramente, os segredos deverão ser fornecidos por um mecanismo apropriado de gerenciamento de segredos, fora do controle de versão. Uma eventual integração deverá utilizar permissões mínimas, configuração explícita e destinos não produtivos durante desenvolvimento e testes.

## Dependências e cadeia de suprimentos

As dependências e faixas de versão estão declaradas em pyproject.toml. A configuração atual não inclui auditoria automatizada de vulnerabilidades, verificação de licenças, geração de inventário de componentes ou validação de hashes de instalação.

Mantenha as dependências atualizadas, revise alterações relevantes e execute os testes após atualizações. A CI atualmente executa testes automatizados e Ruff; ela não deve ser interpretada como uma varredura completa de segurança.

## Limitações e uso não produtivo

Este projeto é uma demonstração educacional e não deve ser tratado como pronto para produção. Ele não implementa autenticação, autorização, isolamento multiusuário, criptografia de dados em repouso, trilha de auditoria, backup, recuperação de desastre, monitoramento de segurança ou gestão formal de incidentes.

A validação de planilhas reduz erros de entrada, mas não torna seguro qualquer arquivo recebido de terceiros. Trate arquivos externos como dados não confiáveis e siga os controles de segurança do ambiente em que forem processados.

## Checklist para contribuições

Antes de abrir um pull request, confirme:

- [ ] Os exemplos e testes usam apenas dados sintéticos.
- [ ] Nenhum segredo, identificador interno ou caminho corporativo foi incluído.
- [ ] Os arquivos de entrada não são alterados pelo fluxo testado.
- [ ] Os relatórios de exemplo não expõem informações reais.
- [ ] As mensagens de erro não revelam credenciais ou detalhes internos.
- [ ] Os testes e a análise estática foram executados.

## Checklist para futuras integrações

Antes de conectar qualquer serviço real, será necessário definir e revisar:

1. O objetivo da integração e os dados estritamente necessários.
2. A identidade técnica e as permissões mínimas.
3. O armazenamento e a rotação de segredos fora do Git.
4. Um modo simulado para testes, sem chamadas reais.
5. Um ambiente não produtivo e um procedimento de autorização explícita.
6. Idempotência, repetição segura, tratamento de falhas e registros sem dados sensíveis.
7. Testes, revisão de segurança e documentação dos limites operacionais.

Esses itens são requisitos para uma possível etapa futura; não são controles já fornecidos pelo código atual.

## Referências internas

- [Arquitetura](architecture.md)
- [Regras de Negócio](business-rules.md)
- [Guia de aprendizagem](learning-guide.md)
- [Garantia de Qualidade](quality-assurance.md)
