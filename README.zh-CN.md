# Token Beggar 🪙: 同样的回答，更少的账单

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: 同样的回答，更少的账单。将每个任务发送给仍然能够正确完成该任务的最便宜模型。" width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="发布版本"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="零依赖"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="许可证"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar 是一个用于 Claude Code 的插件。在大型模型执行任务之前，它会检查是否有更便宜的模型能够同样做好该任务。小任务留在聊天中处理。大型任务（例如在尚未阅读过的代码仓库中修复 bug）会交给一个更便宜的 worker 处理，随后聊天会检查完整的 diff 并运行测试。设计、根本原因分析以及最终回答均由你所选择的模型负责。

**在 18 个真实的 bug 修复任务中，相比单独工作，它消耗的额度和资金减少了 1.42x，同时隐藏测试的通过率基本一致（69% 对 70%）。**

它运行在你的机器上，运行在你的 Claude Code 会话中。它使用你已经登录的 Claude Code，绝不向任何地方发送关于你的任何信息，并且仅写入其自身的文件夹。[具体操作细节](docs/on-your-machine.md)。

[安装](#安装) · [快速开始](#快速开始) · [结果](#结果) · [工作原理](#工作原理) · [常见问题](#常见问题) · [文档](#文档) · [更新日志](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> 不确定它是否在正常工作？请运行 `token-beggar doctor`。它会列出可能静默阻止路由的因素，并在出现问题时以状态码 1 退出。

## 安装

需要 Claude Code 以及 Python 3.10 或更高版本。它仅使用标准库。

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

重启智能体或运行 `/reload-plugins`。更多内容请参见 [docs/install.md](docs/install.md)，包括如何在支持读取技能的其他智能体中使用该技能。

## 快速开始

像平时一样正常工作。在会话的第一个实际 prompt 处，hook 会添加一张简短的路由卡片，并由聊天模型评估任务规模。在发生路由且测量到节省的回应末尾，你会看到这样一行：

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

该倍数是在你的模型和 effort 下，测量得到的不使用 Token Beggar 与使用 Token Beggar 的标价成本比率。美元金额则是该条回应自身成本乘以该比率减一的结果。两者均为估算值，且会明确注明。该行绝不会统计 token 数量，且在低于 1.15x 时不会声明倍数，因为这属于单次运行间的正常波动范围。

若要为未触发它的 prompt 手动启用，请输入 `/token-beggar`。然后确认 hook 正在运行：

```
token-beggar doctor
```

## 结果

两种设置，且仅有两种。**不使用 Token Beggar** 是指聊天模型单独运行，即你平时的正常使用方式。**使用 Token Beggar** 则是本次发布随附的提示卡，版本为 0.3.0。聊天模型为 high effort 的 Opus 5.5。成本包含聊天和每个 worker 的标价费用（含缓存）。置信区间为 95%。

高难度任务是来自 12 个开源 Python 项目（Django、Sphinx、pylint、sympy、click 等）的 18 个已合并 Pull Request。聊天从修复前的 commit 和 issue 文本开始，并由维护者添加的测试进行评分（聊天模型对此测试完全不可见）。每个任务运行 3 次，每种设置运行 54 次。

| 设置 | 每个任务成本 | 倍数 | 解决的 issue |
| --- | --- | --- | --- |
| 不使用 Token Beggar | $0.69 | 1.00x | 70% |
| 使用 Token Beggar | $0.49 | 1.42x 减少 (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="条形图：在高难度任务中按任务划分使用 Token Beggar 相比不使用时减少的额度与费用倍数。所有任务：1.42x。虚线标记 1.0x，即不使用 Token Beggar 的成本。"></p>

<p align="center"><em>18 个任务中有 17 个在使用 Token Beggar 时成本更低。唯一成本增加的任务（structlog-exception-outside）成本高出约 10%。</em></p>

<p align="center"><img src="assets/chart-hard-quality.svg" alt="条形图：18 个高难度任务中解决问题的比例，未使用 Token Beggar 为 70%，使用 Token Beggar 为 69%。"></p>

<p align="center"><em>未使用 Token Beggar 解决 70% 的问题，使用后为 69%：在波动范围内持平，每组 54 次运行。</em></p>

成本降低了 29%，且解决的 issue 比例持平（69% 对 70% 属于波动范围内的持平）。耗时同样相当（168 秒对 187 秒），并未更快。

小任务仅在较早的提示卡上进行了测量，未在 0.3.0 上测量。它们在当时节省甚微（1.11x，低于认定为节省的 1.15x 分界线），且它们留在聊天中处理，因此在单文件的微小编辑上预计几乎不会有任何变化。

完整的基准测试详情、任务列表以及如何复现全部内容：[docs/benchmark.md](docs/benchmark.md)。每次运行的原始数据都在 [`benchmark/results`](benchmark/results) 中。

> [!IMPORTANT]
> **在何处有用以及在何处无用。** 它在 high effort 的 Opus 5.5 处理大型任务时有用（实测 1.42x），在 Fable 5.1 的所有 effort 以及 max effort 的 Opus 上也有用，在这些情况下小任务也测量到了节省。在其他 effort 的 Opus 以及 Sonnet 5.5 上，它将小任务保留在聊天中，将大型任务发送给 worker。大型任务的节省仅针对 Opus high 进行了测量，因此在 Sonnet 上属于未测量状态，页脚将仅显示成本而不显示倍数。在最便宜的模型 Haiku 5.5 上，它不执行任何操作。如果你主要进行单文件的微小编辑，预计几乎不会有任何变化。

## 工作原理

1. **查找模式。** 聊天所使用的模型和 effort 会从 `data/measured.json` 中选择三种模式之一。在小任务测量到 1.15x 或更高节省、或者该模型从未被测量过时，选择 `full`（包含模型、effort 和外部工具的完整菜单）。其他情况选择 `sized`。最便宜的模型选择 `off`。`token-beggar mode --all` 会打印该网格，使用 `TOKEN_BEGGAR_MODE=full|sized|off` 可以强制指定模式。
2. **评估任务规模。** 在 `sized` 模式下，提示卡指明小型任务在聊天中完成，大型任务则将复现、探索、修复和运行测试的整套流程交给一个 worker。大型任务意味着模型未阅读过的代码仓库中的 issue、超过约 5 次工具调用、涉及多个文件，或者编辑与测试循环。超过约 5 个步骤的小任务将转为大型任务。
3. **检查 worker 的工作。** Worker 在 150 字以内进行汇报，并列出所有具有相同症状的位置。聊天模型读取完整的 `git diff`，运行测试，核对该列表，并在发现遗漏时让同一 worker 继续处理。
4. **遵循上限。** 聊天的模型和 effort 会限制同一供应商旗下模型所能获取的级别。在 Sonnet medium 下，任何任务都不会交给 Opus 或 high effort。
5. **汇报。** Stop hook 会添加页脚。该页脚并非由模型编写，因此数字无法在正文中虚构。

阈值的来源：1.15x 大致相当于重复运行中观察到的单次运行间波动，因此低于该比率不会被称为节省。大型任务的 1.42x 比率来自于上述高难度基准测试。详情参见 [docs/benchmark.md](docs/benchmark.md#models-and-efforts)。

### 整体架构

- **Skill**：聊天读取的路由规则。[`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md)，在 [docs/usage.md](docs/usage.md) 中有说明。
- **Hooks**：七个轻量 hook，负责添加提示卡、限制 worker 上限、保护压缩过程以及添加页脚。[docs/on-your-machine.md](docs/on-your-machine.md)。
- **Worker**：拥有六个工具并执行委派任务的单一智能体。[`agents/beggar-worker.md`](agents/beggar-worker.md)，参见 [docs/architecture.md](docs/architecture.md)。
- **CLI**：用于 `doctor`、`mode`、`stats`、`inventory`、`ask` 等命令的 `token-beggar`。[docs/usage.md](docs/usage.md#commands)。

它还可以保护长时间会话。它能够检测宿主压缩上下文的时机，在此之前提示聊天保存一段简短笔记，可以在步骤中间推迟自动压缩，并在压缩后将笔记恢复。参见 [docs/architecture.md](docs/architecture.md)。

## 在你的机器上做了什么

> [!NOTE]
> 以下所有内容以及 hook 列表也可在 [docs/on-your-machine.md](docs/on-your-machine.md) 中找到。

- **读取**：当前会话的 transcript（用于计算成本并获取上下文大小和模型）、通过 `ps` 获取的聊天进程启动参数，以及模型和 effort 的环境与配置文件。这些内容绝不会离开你的机器。
- **运行**：调用 `python3 -m token_beggar hook <name>` 的七个 hook。执行失败的 hook 会记录错误并以 0 退出，因此绝不会损坏你的会话。Worker 在你自己的权限设置下运行。
- **发送**：每周下载一次供应商公开的模型页面，以保持价格最新（`TOKEN_BEGGAR_OFFLINE=1` 可停止该操作）。仅当你安装并指定了外部 AI 工具（`agy`、`gemini`、`codex`），或者单次读取达到约 100k token 或更多时，文本才会发送给该工具。类似密钥的文件名和文本会被拒绝。
- **写入**：一个文件夹，`~/.claude/token-beggar`。不修改智能体设置，也不写入项目中的任何文件。
- **关闭**：在单个 shell 中设置 `TOKEN_BEGGAR=off`，在该文件夹中放置名为 `off` 的文件以永久关闭，或者运行 `/plugin uninstall token-beggar`。

## 配置

你无需进行任何配置。默认设置均来自测量数据。

| 设置 | 作用 |
| --- | --- |
| `TOKEN_BEGGAR=off` | 在当前 shell 中关闭 |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | 强制使用指定模式而非基于测量推断的模式 |
| `TOKEN_BEGGAR_EARLY=1` | 在长会话中建议提早压缩（经实测会增加成本，故默认关闭） |
| `TOKEN_BEGGAR_OFFLINE=1` | 禁用每周下载 |
| `token-beggar cap agy flash` | 将外部工具限制为其 flash 模型 |

全部配置（包括类似 "no gemini" 的 prompt）：[docs/config.md](docs/config.md)。

## 限制

- 小任务节省甚微。在约 1.15x 以下无法与没有节省区分开，而来自较早提示卡的小任务结果（1.11x）低于该数值。
- 高难度基准测试仅涵盖一种聊天模型和 effort（Opus 5.5，high）以及 Python 项目。大型任务中的 Sonnet、Haiku 和 Fable 均未测量。
- 69% 对 70% 的解决率属于波动范围内的持平，且由小型模型进行的盲审对 v0.3.0 的 diff 评分低于单独工作（在 0 到 2 的评分标准中为 0.94 对 1.33），尽管该评分与测试仅呈弱相关，因此并不能表明代码同样优秀。
- v0.3.0 未在小任务上重新运行。
- 在小文件上未发现外部 AI 工具带来节省，且 Gemini 未经测量。大规模读取未经测量。
- 提早压缩在测试的单次长会话中增加了成本，因此属于可选配置（opt in）。
- 页脚基于测量得到的比率估算，而非根据你的具体任务。Hook 无法直接获知聊天模型，因此会先从 transcript 读取，接着从进程参数、环境变量和设置中读取。如果均未指明，卡片将显示上限未知。
- Worker 会像任何普通会话一样加载你的项目 memory 文件。基准测试项目均无该文件，因此该成本未计入数据中。

## 常见问题

**它会改变我的答案吗？** 在高难度任务中，它修复了 69% 的 issue，而单独工作为 70%，在波动范围内持平。它并不宣称代码具有同等质量。

**为什么有时没有页脚？** 仅当进行了路由，且在你的模型、effort 和任务类型下测量到 1.15x 或更高的节省时，它才会打印页脚。

**它在 Sonnet 或 Haiku 上会执行任何操作吗？** 在 Haiku 上不执行任何操作，因为它是最便宜的模型，没有更便宜的模型可以派发工作。在 Sonnet 上，小任务测量到亏损（约 0.85x），因此保留在聊天中，大型任务会派发给 worker，但大型任务的节省尚未测量。

**它会消耗我的额度吗？** Worker 会以更便宜的模型消耗你正常的 Claude 额度。外部 AI 工具消耗它们自身的额度，不会消耗你的 Claude 额度。

**会有任何内容发送到服务器吗？** 仅有每周对模型公开页面的下载（不包含关于你的任何数据），以及你交给指定外部工具的文件。参见 [在你的机器上做了什么](#在你的机器上做了什么)。

**还有哪些类似的工具？** 路由代理根据场景将 API 请求发送到其他提供商，subagent 模型变量将单一模型固定给 subagent，而像 ccusage 这样的计量器在事后统计支出。Token Beggar 在会话内部工作，评估任务与上限，其倍数来自基准测试而非你的历史记录。它可以与更短的 prompt 和更小的上下文配合使用。如果这里遗漏了某种工具，欢迎提交 issue。

## 文档

| 目标 | 从这里开始 |
| --- | --- |
| 安装它，或者单次会话试用 | [docs/install.md](docs/install.md) |
| 了解它路由的内容以及相关命令 | [docs/usage.md](docs/usage.md) |
| 查看它在你的机器上执行的操作 | [docs/on-your-machine.md](docs/on-your-machine.md) |
| 修改设置或规则 | [docs/config.md](docs/config.md) |
| 理解各组件与运行模式 | [docs/architecture.md](docs/architecture.md) |
| 查看数据或进行复现 | [docs/benchmark.md](docs/benchmark.md) |
| 查看更新内容 | [CHANGELOG.md](CHANGELOG.md) |

## 开发

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## 贡献

欢迎提交 issue 和 pull request。对卡片、技能或 `data/profiles.json` 的修改需要在修改前后进行基准测试运行，并将损失与收益一同报告。参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT © Arthur031221

Assisted by Claude/Codex.
