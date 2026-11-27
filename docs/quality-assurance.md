# Garantia de Qualidade — Automação de Conciliação Operacional

Este documento descreve como a qualidade é verificada localmente e na integração contínua. A estratégia combina testes unitários, testes de integração, cobertura de código e análise estática.

## Objetivos

- Verificar as regras de domínio e os contratos das planilhas.
- Detectar regressões na leitura, descoberta, consolidação, comparação e geração de relatórios.
- Validar o fluxo de conciliação ponta a ponta com arquivos Excel sintéticos.
- Exigir cobertura de statements e branches conforme a configuração do projeto.
- Aplicar regras de análise estática com Ruff.

## Organização dos testes

Os testes estão separados em duas camadas:

- **Unitários — tests/unit/:** verificam regras e componentes isolados, incluindo normalização, consolidação, comparação, leitura Excel, descoberta, geração de relatórios, orquestração da aplicação e parsing/execução da CLI.
- **Integração — tests/integration/:** verificam fluxos que conectam componentes reais. Incluem a passagem de Excel para comparação e o fluxo completo de arquivos de entrada até o relatório final.

Os testes da CLI verificam parsing de datas, argumentos obrigatórios, execução da aplicação e mensagens de erro. O teste test_application_workflow_integration.py cria planilhas sintéticas em diretórios temporários e executa a função de aplicação sem substituir os componentes por mocks. Ele verifica as classificações, os totais, as sete abas do relatório e se as planilhas originais permanecem inalteradas.

## Executar localmente

Instale as dependências de desenvolvimento:

```bash
python -m pip install -e ".[dev]"
```

Execute a suíte completa com cobertura:

```bash
python -m pytest tests -v --cov=operations_reconciliation --cov-report=term-missing --cov-fail-under=100
```

Execute apenas os testes unitários:

```bash
python -m pytest tests/unit -v
```

Execute apenas os testes de integração:

```bash
python -m pytest tests/integration -v
```

Execute o teste ponta a ponta da aplicação:

```bash
python -m pytest tests/integration/test_application_workflow_integration.py -v
```

Execute Ruff:

```bash
python -m ruff check src tests
```

## Cobertura de código

A configuração em pyproject.toml habilita a medição de branches e limita a análise ao pacote operations_reconciliation.

A meta configurada é de 100% de cobertura. A execução de pytest-cov utiliza --cov-fail-under=100 para que uma cobertura inferior à meta faça o comando falhar.

Cobertura de statements indica quais instruções foram executadas pelos testes. Cobertura de branches indica se os caminhos de decisão medidos foram exercitados. As duas métricas ajudam a encontrar lacunas, mas não provam ausência de defeitos, qualidade de todos os casos de teste ou adequação para produção.

Ao adicionar uma nova condição, exceção ou caminho alternativo, inclua testes que exercitem tanto o comportamento esperado quanto as rejeições relevantes.

## Análise estática com Ruff

O Ruff é configurado em pyproject.toml com comprimento máximo de linha de 100 caracteres, alvo Python 3.13 e as famílias de regras E4, E7, E9, F, I, B e UP.

Execute:

```bash
python -m ruff check src tests
```

A configuração atual executa a verificação de lint. O workflow de CI não executa ruff format nem uma etapa separada de verificação de formatação.

## Integração contínua

O workflow .github/workflows/ci.yml executa em:

- Pushes para a branch main.
- Pull requests direcionados à branch main.

O job utiliza Ubuntu, configura Python 3.14, instala o projeto com as dependências de desenvolvimento, executa os testes com a meta de cobertura de 100% e executa Ruff.

O workflow limita as permissões do token a contents: read e utiliza concorrência para cancelar uma execução anterior do mesmo grupo quando uma nova execução é iniciada.

A CI atual verifica testes e lint. Ela não executa análise estática de tipos, auditoria automatizada de dependências, varredura de segredos, análise dinâmica, build de pacote ou validação automatizada de links e documentação.

## Fluxo recomendado para pull requests

1. Crie uma branch de trabalho a partir da main atualizada.
2. Implemente a alteração e seus testes.
3. Execute os testes unitários e de integração localmente.
4. Execute a suíte completa com cobertura e Ruff.
5. Revise os diffs e confirme que apenas arquivos intencionais foram alterados.
6. Abra o pull request e aguarde a CI.
7. Corrija falhas e execute novamente as verificações antes do merge.

Não reduza a meta de cobertura apenas para fazer uma alteração passar. Se uma regra de cobertura precisar mudar, documente a justificativa e o impacto.

## Interpretar resultados

- **Testes aprovados:** os casos automatizados executados passaram; isso não garante que todos os cenários possíveis foram cobertos.
- **Cobertura abaixo de 100%:** identifique statements ou branches não exercitados e avalie testes adicionais.
- **Falha no Ruff:** corrija os problemas de lint antes do merge.
- **Falha na CI:** consulte o log do job, reproduza o comando localmente e corrija a causa, não apenas o sintoma.

Uma CI verde é uma condição importante para integração, mas não substitui revisão de código, revisão das regras de negócio ou avaliação de segurança.

## Limites da estratégia atual

A configuração atual não inclui testes de desempenho, testes de carga, testes de compatibilidade em todas as versões de Python, testes em Windows/macOS na CI, análise estática de tipos, auditoria de vulnerabilidades ou validação automatizada de documentação.

Essas verificações podem ser adicionadas conforme o escopo crescer. Até lá, não devem ser descritas como controles existentes.

## Referências internas

- [Arquitetura](architecture.md)
- [Regras de Negócio](business-rules.md)
- [Guia de aprendizagem](learning-guide.md)
- [Segurança](security.md)
