# Token Beggar 🪙: mesmas respostas, uma fatura menor

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: mesmas respostas, uma fatura menor. Envia cada tarefa para o modelo mais econômico que ainda assim a resolve corretamente." width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="Versão"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Zero dependências"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="Licença"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

O Token Beggar é um plugin para o Claude Code. Antes de o modelo grande realizar um trabalho, ele verifica se um modelo mais econômico pode fazê-lo tão bem quanto. Tarefas pequenas permanecem no chat. Uma tarefa grande, como corrigir um bug em um repositório que você ainda não leu, vai para um worker mais econômico, e o chat então verifica todo o diff e executa os testes. Design, causas-raiz e a resposta final continuam com o modelo que você escolheu.

**Em 18 correções reais de bugs, custou 1.42x menos cota e dinheiro do que trabalhando sozinho, com a mesma proporção de testes ocultos passando (69% contra 70%).**

Ele roda na sua máquina, na sua sessão do Claude Code. Usa o Claude Code no qual você já está conectado, não envia nada sobre você para lugar nenhum e grava apenas na sua própria pasta. [Exatamente o que ele faz](docs/on-your-machine.md).

[Instalação](#instalação) · [Início rápido](#início-rápido) · [Resultados](#resultados) · [Como funciona](#como-funciona) · [Perguntas frequentes](#perguntas-frequentes) · [Documentação](#documentação) · [Registro de alterações](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> Não tem certeza se está funcionando? Execute `token-beggar doctor`. Ele lista o que pode interromper o roteamento silenciosamente e encerra com código 1 quando algo está quebrado.

## Instalação

Requer o Claude Code e Python 3.10 ou superior. Usa apenas a biblioteca padrão.

```
# From the marketplace in this repository (inside Claude Code)
/plugin marketplace add Arthur031221/Token-Beggar
/plugin install token-beggar@token-beggar
```

```
# Try it for one session without installing
git clone https://github.com/Arthur031221/Token-Beggar
claude --plugin-dir ./Token-Beggar
```

```
# From a shell, the same two steps as the first block
claude plugin marketplace add Arthur031221/Token-Beggar
claude plugin install token-beggar@token-beggar
```

Reinicie o agente ou execute `/reload-plugins`. Mais detalhes em [docs/install.md](docs/install.md), incluindo como usar a skill em outro agente que lê skills.

## Início rápido

Trabalhe como você sempre faz. No primeiro prompt real de uma sessão, um hook adiciona um cartão curto de roteamento, e o modelo de chat dimensiona a tarefa. No final de uma resposta em que algo foi roteado e uma economia foi medida, você recebe uma linha:

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

O múltiplo é a razão medida do custo a preço de tabela sem Token Beggar sobre com ele, para o seu modelo e effort. Os dólares são o custo da própria resposta multiplicado por essa razão menos um. Ambos são estimativas e deixam isso claro. A linha nunca conta tokens e, abaixo de 1.15x, não indica nenhum múltiplo, porque isso está dentro da dispersão de execução para execução.

Para ativá-lo em um prompt que não o acionou, digite `/token-beggar`. Em seguida, confirme se os hooks rodam:

```
token-beggar doctor
```

## Resultados

Duas configurações, e apenas duas. **Sem Token Beggar** é o modelo de chat trabalhando sozinho, da forma como você usa normalmente. **Com Token Beggar** é o cartão distribuído neste lançamento, versão 0.3.0. Opus 5.5 em effort high é o modelo de chat. O custo é o preço de tabela para o chat e cada worker, cache incluído. Os intervalos são de 95 por cento.

Tarefas difíceis são 18 pull requests mesclados de 12 projetos Python de código aberto (Django, Sphinx, pylint, sympy, click e outros). O chat começa a partir do commit anterior à correção com o texto da issue, e é avaliado pelos testes que os mantenedores adicionaram, os quais ele nunca vê. 3 execuções por tarefa, 54 por configuração.

| Configuração | Custo por tarefa | Múltiplo | Issues resolvidas |
| --- | --- | --- | --- |
| Sem Token Beggar | $0.69 | 1.00x | 70% |
| Com Token Beggar | $0.49 | 1.42x menos (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="Gráfico de barras: vezes menos cota e dinheiro com Token Beggar do que sem ele, por tarefa difícil. Todas as tarefas: 1.42x. Uma linha tracejada marca 1.0x, o custo sem Token Beggar."></p>

<p align="center"><em>17 das 18 tarefas custaram menos com o Token Beggar. A única que custou mais (structlog-exception-outside) custou cerca de 10% a mais.</em></p>

O custo caiu 29 por cento e a proporção de issues resolvidas fica no mesmo nível (69% contra 70% é um empate dentro da dispersão). O tempo também fica no mesmo nível (168 segundos contra 187), não mais rápido.

Tarefas pequenas foram medidas apenas com um cartão anterior, não com a 0.3.0. Elas economizaram pouco lá (1.11x, abaixo da linha de 1.15x em que uma economia é alegada), e elas permanecem no chat, portanto espere quase nenhuma mudança em pequenas edições em um único arquivo.

Detalhes completos do benchmark, a lista de tarefas e como reproduzir tudo: [docs/benchmark.md](docs/benchmark.md). Cada execução bruta está em [`benchmark/results`](benchmark/results).

> [!IMPORTANT]
> **Onde ajuda e onde não ajuda.** Ajuda em tarefas grandes com o Opus 5.5 em effort high (1.42x, medido), e em todos os níveis de effort do Fable 5.1 e Opus em max, onde tarefas pequenas também medem economia. No Opus em outros níveis de effort e no Sonnet 5.5, ele mantém tarefas pequenas no chat e envia as grandes para um worker. A economia em tarefas grandes é medida apenas para o Opus high, portanto no Sonnet ela não é medida e o rodapé então informa o custo sem um múltiplo. No Haiku 5.5, o modelo mais barato, ele não faz nada. Se você realiza principalmente pequenas edições em um único arquivo, espere quase nenhuma mudança.

## Como funciona

1. **Consultar o modo.** O modelo e o effort do seu chat selecionam um de três modos em `data/measured.json`. `full` (o menu completo de modelos, níveis de effort e ferramentas externas) onde tarefas pequenas mediram economia de 1.15x ou mais, ou o modelo nunca foi medido. `sized` em todos os outros casos. `off` para o modelo mais barato. `token-beggar mode --all` exibe a grade, e `TOKEN_BEGGAR_MODE=full|sized|off` força um deles.
2. **Dimensionar a tarefa.** No modo `sized`, o cartão diz que pequeno significa fazer no chat, e grande significa enviar a um worker a lista completa de reproduzir, explorar, corrigir e executar os testes. Grande significa uma issue em um repositório que o modelo não leu, mais de cerca de 5 chamadas de ferramentas, mais de um arquivo ou um ciclo de edição e testes. Uma tarefa pequena que passa de cerca de 5 etapas se torna grande.
3. **Verificar o trabalho do worker.** O worker relata em menos de 150 palavras e lista cada local que compartilha o sintoma. O chat lê todo o `git diff`, executa os testes, confere essa lista e envia o mesmo worker de volta se algo estiver faltando.
4. **Respeitar o teto.** O modelo e o effort do seu chat limitam o que os modelos do mesmo provedor recebem. No Sonnet medium, nada vai para o Opus ou para effort high.
5. **Informar.** O hook Stop adiciona o rodapé. O modelo não o escreve, portanto o número não pode ser inventado em prosa.

De onde vieram os limites: 1.15x é aproximadamente a dispersão de execução para execução observada em execuções repetidas, portanto uma razão menor não é chamada de economia. A razão para tarefas grandes de 1.42x vem do benchmark difícil acima. Detalhes em [docs/benchmark.md](docs/benchmark.md#models-and-efforts).

### Como tudo se encaixa

- **Skill**: as regras de roteamento que o chat lê. [`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md), explicadas em [docs/usage.md](docs/usage.md).
- **Hooks**: sete hooks pequenos que adicionam o cartão, mantêm os workers dentro do teto, protegem a compactação e adicionam o rodapé. [docs/on-your-machine.md](docs/on-your-machine.md).
- **Worker**: um agente com seis ferramentas que realiza o trabalho delegado. [`agents/beggar-worker.md`](agents/beggar-worker.md), veja [docs/architecture.md](docs/architecture.md).
- **CLI**: `token-beggar` para `doctor`, `mode`, `stats`, `inventory`, `ask` e mais. [docs/usage.md](docs/usage.md#commands).

Ele também protege sessões longas. Encontra o ponto em que o host compacta o contexto, pede ao chat para salvar uma nota curta antes disso, pode adiar uma compactação automática no meio de uma etapa e coloca a nota de volta depois. Veja [docs/architecture.md](docs/architecture.md).

## O que faz na sua máquina

> [!NOTE]
> Tudo abaixo também está em [docs/on-your-machine.md](docs/on-your-machine.md), com a tabela de hooks.

- **Lê**: a transcrição da sessão atual (para contabilizar o custo e encontrar o tamanho do contexto e o modelo), as flags de inicialização do processo de chat via `ps`, e os arquivos de ambiente e configuração para o modelo e o effort. Nada disso sai da sua máquina.
- **Executa**: sete hooks que chamam `python3 -m token_beggar hook <name>`. Um hook que falha registra o erro e encerra com código 0, portanto nunca quebra sua sessão. Workers rodam sob as suas próprias configurações de permissão.
- **Envia**: um download semanal da página pública de modelos do provedor, para manter os preços atualizados (`TOKEN_BEGGAR_OFFLINE=1` interrompe isso). Texto vai para uma ferramenta externa de IA (`agy`, `gemini`, `codex`) apenas se você a tiver instalada e a nomear ou se uma leitura for de cerca de 100k tokens ou mais. Nomes de arquivos e textos que pareçam chaves são recusados.
- **Grava**: uma pasta, `~/.claude/token-beggar`. Nenhuma configuração de agente, nenhum arquivo no seu projeto.
- **Desativar**: `TOKEN_BEGGAR=off` para um shell, um arquivo chamado `off` nessa pasta para sempre, ou `/plugin uninstall token-beggar`.

## Configuração

Você não precisa de nenhuma. Os padrões vêm das medições.

| Configuração | O que faz |
| --- | --- |
| `TOKEN_BEGGAR=off` | Desativado para este shell |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | Força um modo em vez do medido |
| `TOKEN_BEGGAR_EARLY=1` | Sugere compactação antecipada em sessões longas (medido como mais caro, portanto desativado) |
| `TOKEN_BEGGAR_OFFLINE=1` | Sem download semanal |
| `token-beggar cap agy flash` | Mantém uma ferramenta externa nos seus modelos flash |

Tudo isso, incluindo prompts como "no gemini": [docs/config.md](docs/config.md).

## Limites

- Tarefas pequenas economizam pouco. Abaixo de cerca de 1.15x, não se distingue de nenhuma economia, e o resultado de tarefas pequenas do cartão anterior (1.11x) está abaixo disso.
- O benchmark difícil cobre um único modelo de chat e effort (Opus 5.5, high) e projetos em Python. Sonnet, Haiku e Fable em tarefas grandes não foram medidos.
- 69% contra 70% de resolução é um empate dentro da dispersão, e uma avaliação cega por um modelo pequeno avaliou os diffs da v0.3.0 como inferiores a trabalhar sozinho (0.94 contra 1.33 em uma escala de 0 a 2), embora concorde apenas fracamente com os testes, portanto não está demonstrado que o código seja tão bom quanto.
- A v0.3.0 não foi executada novamente nas tarefas pequenas.
- Nenhuma economia com ferramentas externas de IA foi encontrada em arquivos pequenos, e o Gemini não foi medido. Leituras grandes não foram medidas.
- A compactação antecipada custou mais na única sessão longa testada, portanto é opcional.
- O rodapé é estimado a partir de uma razão medida, não da sua tarefa. Hooks não conseguem ver o modelo de chat, portanto ele é lido da transcrição, depois das flags do processo, do ambiente e das configurações. Se nenhum informar, o cartão diz que o teto é desconhecido.
- Workers carregam o arquivo de memória do seu projeto como em qualquer sessão. Os projetos do benchmark não possuem nenhum, portanto esse custo não está nos números.

## Perguntas frequentes

**Isso altera minhas respostas?** Nas tarefas difíceis, corrigiu 69% dos problemas contra 70% sozinho, um empate dentro da dispersão. Não afirma que o código seja de igual qualidade.

**Por que às vezes não há rodapé?** Ele só exibe um quando roteou algo e uma economia de 1.15x ou mais foi medida para o seu modelo, effort e tipo de tarefa.

**Ele faz alguma coisa no Sonnet ou Haiku?** No Haiku nada, porque é o modelo mais barato e não há nada mais econômico para onde enviar o trabalho. No Sonnet, tarefas pequenas mediram perda (cerca de 0.85x), então elas permanecem no chat, e tarefas grandes vão para um worker, mas a economia em tarefas grandes não foi medida.

**Isso consome minha cota?** O worker gasta a sua cota normal do Claude em um modelo mais econômico. Ferramentas externas de IA gastam a cota própria delas e nada da sua.

**Algo é enviado para algum servidor?** Apenas o download semanal da página de modelos, que não contém dados sobre você, e os arquivos que você repassar para uma ferramenta externa que tenha nomeado. Veja [o que faz na sua máquina](#o-que-faz-na-sua-máquina).

**Quais outras ferramentas são parecidas?** Proxies de roteamento enviam requisições de API para outros provedores por cenário, a variável de modelo de subagente fixa um modelo para subagentes, e medidores como ccusage relatam o gasto posteriormente. O Token Beggar funciona dentro da sessão, classifica a tarefa e o teto, e seu múltiplo vem de um benchmark, não do seu histórico. Ele se combina com prompts mais curtos e contextos menores. Se alguma ferramenta estiver faltando aqui, abra uma issue.

## Documentação

| Objetivo | Comece aqui |
| --- | --- |
| Instalar, ou testar por uma sessão | [docs/install.md](docs/install.md) |
| Aprender o que ele roteia e os comandos | [docs/usage.md](docs/usage.md) |
| Ver o que faz na sua máquina | [docs/on-your-machine.md](docs/on-your-machine.md) |
| Alterar uma configuração ou regra | [docs/config.md](docs/config.md) |
| Compreender as partes e os modos | [docs/architecture.md](docs/architecture.md) |
| Conferir os números ou reproduzi-los | [docs/benchmark.md](docs/benchmark.md) |
| Ver o que mudou | [CHANGELOG.md](CHANGELOG.md) |

## Desenvolvimento

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## Contribuindo

Issues e pull requests são bem-vindos. Uma alteração no cartão, na skill ou em `data/profiles.json` precisa de uma execução de benchmark antes e depois, com as perdas relatadas ao lado dos ganhos. Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

MIT © Arthur031221

Assisted by Claude/Codex.
