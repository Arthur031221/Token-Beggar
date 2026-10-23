# Token Beggar 🪙: 同じ回答を、より少ない請求額で

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="Token Beggar: 同じ回答を、より少ない請求額で。各タスクを、正しく処理できる最も安価なモデルに送信します。" width="100%">
</picture>

<p align="center">
  <a href="https://github.com/Arthur031221/Token-Beggar/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Arthur031221/Token-Beggar/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/Arthur031221/Token-Beggar/releases"><img src="https://img.shields.io/github/v/release/Arthur031221/Token-Beggar?style=flat-square&label=release" alt="リリース"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="依存関係ゼロ"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Arthur031221/Token-Beggar?style=flat-square" alt="ライセンス"></a>
</p>

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt-BR.md)

Token Beggar は Claude Code 向けのプラグインです。大規模モデルが処理を実行する前に、より安価なモデルでも同等に処理できるかを確認します。小規模なタスクはチャット内に留まります。まだ読んだことのないリポジトリのバグ修正といった大規模なタスクは、より安価な 1 つのワーカーに送られ、チャット側が diff 全体を検証してテストを実行します。設計、根本原因の特定、最終的な回答は、ユーザーが選択したモデルが担当します。

**18 件の実際のバグ修正において、単独動作と比べてクォータと費用を 1.42x 削減し、非公開テストの合格率も同等でした（69% 対 70%）。**

本プラグインはローカルマシン上の Claude Code セッション内で動作します。すでにサインインしている Claude Code を使用し、ユーザーに関する情報を外部に送信することは一切なく、自身のフォルダにのみ書き込みを行います。[具体的な動作内容](docs/on-your-machine.md)。

[インストール](#インストール) · [クイックスタート](#クイックスタート) · [結果](#結果) · [仕組み](#仕組み) · [よくある質問](#よくある質問) · [ドキュメント](#ドキュメント) · [更新履歴](CHANGELOG.md)

<p align="center"><img src="assets/demo.gif" width="760" alt="Terminal recording of the routing card, the compaction guard and the benchmark table"></p>

> [!TIP]
> 正常に動作しているか不明な場合は、`token-beggar doctor` を実行してください。ルーティングが密かに停止する原因を一覧表示し、問題がある場合は終了コード 1 で終了します。

## インストール

Claude Code および Python 3.10 以降が必要です。標準ライブラリのみを使用します。

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

エージェントを再起動するか、`/reload-plugins` を実行してください。スキルを読み込む他のエージェントでの使用方法など、詳細は [docs/install.md](docs/install.md) を参照してください。

## クイックスタート

普段通りに作業を進めてください。セッションの最初の実質的なプロンプトでフックが短いルーティングカードを追加し、チャットモデルがタスクの規模を判定します。何かがルーティングされ、節約が測定された返信の末尾に、次の 1 行が表示されます:

```
Token Beggar: about 1.4x less quota than Opus 5.5 high alone, saved about $0.21 (est.) | large task | routed 1: haiku medium x1
```

倍率は、お使いのモデルと effort において測定された、Token Beggar なしとありの定価コストの比率です。金額はその返信自体のコストに比率から 1 を引いた値を掛けたものです。いずれも推定値であり、その旨が記載されます。この行でトークン数をカウントすることはなく、1.15x 未満では実行ごとのばらつきの範囲内であるため、倍率は示されません。

自動で起動しなかったプロンプトで有効にするには、`/token-beggar` と入力してください。その後、フックが実行されることを確認します:

```
token-beggar doctor
```

## 結果

チャットモデルとして Opus 5.5（effort は high）を使用。コストはチャットおよびすべてのワーカーの定価（キャッシュを含む）です。信頼区間は 95 パーセントです。区間全体が 1.0x を上回り、かつ 1.15x 以上の場合にのみ節約として主張しています。

ここでのバージョンとは、本リポジトリのタグ付きリリースを指します。**Token Beggar なし (Without Token Beggar)** は、チャットモデル単独での動作です。**v0.3.0（本リリース） (v0.3.0 (this release))** は本バージョンです。**v0.2.0（前リリース） (v0.2.0 (previous release))** はその前のバージョンです。高難度ベンチマークでは、**v0.3.0 前の main (Main before v0.3.0)**（本リリースの直前における main ブランチのカード）と比較しています。v0.2.0 自体はこのベンチマークで実行されていないためです。

### 高難度タスク: 実際のバグ修正

12 件のオープンソース Python プロジェクト（Django、Sphinx、pylint、sympy、click など）からマージされた 18 件のプルリクエスト。チャットは修正前のコミットと Issue 本文から開始し、メンテナーが追加した（チャット側には非公開の）テストによって採点されます。1 タスクあたり 3 回実行、設定あたり 54 回実行。

| 設定 | 1 実行あたりのコスト | Token Beggar なしに対する倍率 | 解決率 |
| --- | --- | --- | --- |
| Token Beggar なし | $0.69 | 1.00x | 70% |
| v0.3.0 前の main | $0.45 | 1.54x (1.46 to 1.64) | 65% |
| v0.3.0（本リリース） | $0.49 | 1.42x (1.33 to 1.51) | 69% |

<p align="center"><img src="assets/chart-hard-cost.svg" alt="棒グラフ: 高難度タスクにおいてタスクごとに Token Beggar なしと比べてクォータと費用が何倍削減されたか。全タスク: v0.3.0 前の main は 1.54x、v0.3.0 は 1.42x。破線は削減なしの 1.0x を示します。"></p>

<p align="center"><em>18 件の高難度タスク中 17 件で Token Beggar によるコスト削減が見られ、コストが増加した 1 件（structlog-exception-outside）は約 10% の増加でした。</em></p>

<p align="center"><img src="assets/chart-hard-quality.svg" alt="棒グラフ: 高難度タスクにおいて問題が修正された割合（タスクごと）。全タスク: Token Beggar なしは 70%、v0.3.0 前の main は 65%、v0.3.0 は 69%。"></p>

<p align="center"><em>問題解決率は単独動作に近い水準を維持しており、品質を犠牲にしてコストを節約しているわけではないことが確認できます。</em></p>

コストは約 3 分の 1 削減され、問題解決率は同等です。v0.3.0 前の main はさらに安価でしたが解決数が少なく、click-format-filename では誤った修正のまま 2 ターンで停止しました（単独動作では 3 回中 3 回解決に対し、0 回）。v0.3.0 では、その節約分の一部を回答前の diff 全体の読み込みに充てています。これが本バージョンを出荷した理由です。

この結果が示していない点: 同等のコード品質です。小規模モデルによるブラインドレビューでは、v0.3.0 の diff はより低く評価され（0 から 2 のスコアで単独の 1.33 に対して 0.94）、非公開テストとの一致度もわずかでした。所要時間は単独動作と同水準（187 秒に対して 168 秒）であり、高速化はしていません。

### 小規模タスク

7 クラスの 28 件の小規模タスクで、各 3 回実行、設定あたり 84 回実行。21 件はチューニングに使用され、7 件は評価用に保持（ホールドアウト）されました。このベンチマークは v0.3.0 が存在する前に実行されたため、最後の列は v0.3.0 前の main となっています。どちらのカードでも小規模タスクはチャット内に留まるため、v0.3.0 も同等の結果になると予想されますが、再実行はされていません。

| グループ | Token Beggar なし | v0.2.0（前リリース） | v0.3.0 前の main | v0.3.0 前の main 対 なし |
| --- | --- | --- | --- | --- |
| 全 28 タスク | $0.148 | $0.139 | $0.134 | 1.11x (1.08 to 1.14) |
| 保持された 7 タスク | $0.134 | $0.136 | $0.129 | 1.04x (0.99 to 1.11) |
| 複数ファイル | $0.260 | $0.194 | $0.185 | 1.40x (1.27 to 1.55) |
| 定型コード | $0.152 | $0.149 | $0.132 | 1.15x (1.09 to 1.22) |

<p align="center"><img src="assets/chart-small-cost.svg" alt="棒グラフ: 小規模タスクにおいてクラスごとに Token Beggar なしと比べてクォータと費用が何倍削減されたか（v0.2.0 および v0.3.0 前の main）。破線は削減なしの 1.0x を示します。"></p>

<p align="center"><em>小規模タスクでは複数ファイルクラスのみ明確に削減されており、その他は破線付近に位置しています。</em></p>

<p align="center"><img src="assets/chart-small-quality.svg" alt="棒グラフ: クラスごとの小規模タスクにおける平均品質。全小規模タスク: Token Beggar なしは 0.96、v0.2.0 は 0.96、v0.3.0 前の main は 0.99。"></p>

<p align="center"><em>小規模タスクにおける回答品質は、どの設定でも低下しませんでした。</em></p>

小規模タスクでの削減効果はわずかです。他の 5 つのクラス（機械的編集、読み取り、デバッグ、設計、レビュー）は 0.97x から 1.09x の間であり、ノイズの範囲内でした。混合タスクの結果（1.11x）は 1.15x の基準を下回っているため節約とは主張しておらず、保持されたタスクでも単独動作のばらつきの範囲内です。ワーカーあたり約 $0.10 の起動コストは $0.15 のタスクの大半を占めるため、小規模タスクはチャット内に留められます。回答品質はどの設定でも低下しませんでした。

> [!IMPORTANT]
> **効果があるケースとないケース。** Opus 5.5（high effort）の大規模タスク（実測 1.42x）や、Fable 5.1 のすべての effort、および max effort の Opus で効果があり、これらでは小規模タスクでも節約が測定されています。他の effort の Opus や Sonnet 5.5 では、小規模タスクをチャット内に留め、大規模タスクをワーカーに送信します。大規模タスクの節約は Opus high でのみ測定されているため、Sonnet では未測定となり、フッターには倍率なしでコストが表示されます。最も安価なモデルである Haiku 5.5 では何もしません。主に 1 ファイルの小規模な編集を行う場合、変化はほぼ期待できません。

表、タスクリスト、試行したものの元に戻された機能（外部ツールによる一括読み込み、早期圧縮）、およびすべての再現手順は [docs/benchmark.md](docs/benchmark.md) に記載されています。すべての生実行データは [`benchmark/results`](benchmark/results) にあります。

## 仕組み

1. **モードの確認。** チャットのモデルと effort に応じて、`data/measured.json` から 3 つのモードのいずれかが選択されます。小規模タスクで 1.15x 以上の節約が測定された場合、またはモデルが未測定の場合は `full`（モデル、effort、外部ツールの全メニュー）。それ以外は `sized`。最も安価なモデルでは `off`。`token-beggar mode --all` で一覧を表示し、`TOKEN_BEGGAR_MODE=full|sized|off` で強制指定できます。
2. **タスク規模の判定。** `sized` モードでは、カードの指示に従い、小規模はチャット内で実行し、大規模は再現、調査、修正、テスト実行の全リストを 1 つのワーカーに委託します。大規模とは、モデルが読んだことのないリポジトリの Issue、約 5 回を超えるツール呼び出し、複数ファイル、または編集とテストのループを指します。約 5 ステップを超えて拡大した小規模タスクは大規模になります。
3. **ワーカー成果物の確認。** ワーカーは 150 語未満で報告し、同じ事象が発生しているすべての箇所を一覧化します。チャット側で `git diff` 全体を読み込み、テストを実行し、その一覧を確認した上で、不足があれば同じワーカーに差し戻します。
4. **上限の遵守。** チャットのモデルと effort により、同一ベンダーのモデルに割り当てられる上限が制限されます。Sonnet medium では、Opus や high effort に送信されることはありません。
5. **報告。** Stop フックがフッターを追加します。モデル自身が書くわけではないため、文章中で数値が捏造されることはありません。

しきい値の根拠: 1.15x は繰り返し実行で見られる実行ごとのばらつきに相当するため、これより小さい比率は節約とは呼びません。大規模タスクの比率 1.42x は上記高難度ベンチマークの結果です。詳細は [docs/benchmark.md](docs/benchmark.md#models-and-efforts) を参照してください。

### 全体構成

- **Skill**: チャットが読み込むルーティングルール。[`skills/token-beggar/SKILL.md`](skills/token-beggar/SKILL.md)、解説は [docs/usage.md](docs/usage.md)。
- **Hooks**: カードの追加、ワーカーの上限維持、コンテキスト圧縮の保護、フッターの追加を行う 7 つの軽量フック。[docs/on-your-machine.md](docs/on-your-machine.md)。
- **Worker**: 委託された作業を実行する、6 つのツールを持つ 1 つのエージェント。[`agents/beggar-worker.md`](agents/beggar-worker.md)、[docs/architecture.md](docs/architecture.md) を参照。
- **CLI**: `doctor`、`mode`、`stats`、`inventory`、`ask` などを行う `token-beggar`。[docs/usage.md](docs/usage.md#commands)。

また、長時間のセッションも保護します。ホストがコンテキストを圧縮するポイントを検出し、その直前に短いメモを保存するようチャットに促し、ステップの途中で行われる自動圧縮を延期し、圧縮後にメモを復元できます。[docs/architecture.md](docs/architecture.md) を参照してください。

## マシン上での動作

> [!NOTE]
> 以下の内容はすべて、フック一覧表とともに [docs/on-your-machine.md](docs/on-your-machine.md) にも記載されています。

- **読み取り**: 現在のセッションのトランスクリプト（コスト集計、コンテキストサイズおよびモデル検出用）、`ps` 経由でのチャットプロセスの起動フラグ、モデルと effort の環境変数および設定ファイル。これらの情報がマシン外に出ることはありません。
- **実行**: `python3 -m token_beggar hook <name>` を呼び出す 7 つのフック。フックが失敗してもエラーを記録して終了コード 0 で終了するため、セッションが壊れることはありません。ワーカーはユーザー自身の権限設定の下で実行されます。
- **送信**: 価格情報を最新に保つための、ベンダーの公開モデルページの週 1 回のダウンロード（`TOKEN_BEGGAR_OFFLINE=1` で停止可能）。テキストが外部 AI ツール（`agy`、`gemini`、`codex`）に送信されるのは、それらがインストールされており明示的に指定した場合、または読み込みが約 100k トークン以上の場合のみです。API キー等と思われるファイル名やテキストは拒否されます。
- **書き込み**: 1 つのフォルダ `~/.claude/token-beggar` のみ。エージェント設定やプロジェクト内のファイルは一切変更しません。
- **無効化**: 単一シェルでは `TOKEN_BEGGAR=off`、恒久的にはそのフォルダ内に `off` という名前のファイルを配置、または `/plugin uninstall token-beggar`。

## 設定

設定は不要です。デフォルト値は実測データに基づいています。

| 設定項目 | 動作内容 |
| --- | --- |
| `TOKEN_BEGGAR=off` | このシェルでのみ無効化 |
| `TOKEN_BEGGAR_MODE=full\|sized\|off` | 実測に基づくモードの代わりに指定したモードを強制 |
| `TOKEN_BEGGAR_EARLY=1` | 長時間セッションでの早期圧縮を提案（実測でコスト増となったためデフォルトはオフ） |
| `TOKEN_BEGGAR_OFFLINE=1` | 週 1 回のダウンロードを行わない |
| `token-beggar cap agy flash` | 外部ツールを flash モデルに限定 |

「no gemini」などのプロンプトを含むすべての設定: [docs/config.md](docs/config.md)。

## 制限事項

- 小規模タスクでの節約はわずかです。約 1.15x 未満は節約なしと区別がつかず、小規模タスクの混合結果（1.11x）はこれを下回っています。
- 高難度ベンチマークは、1 つのチャットモデルと effort（Opus 5.5、high）および Python プロジェクトのみを対象としています。大規模タスクにおける Sonnet、Haiku、Fable は測定されていません。
- 解決率 69% 対 70% はばらつきの範囲内で同等であり、ブラインドレビューでは v0.3.0 の diff はより低く評価されました。コードが同等に優れていることは示されていません。
- リリースされた v0.2.0 は高難度タスクで実行されておらず、v0.3.0 は小規模タスクで再実行されていません。
- 小さなファイルでは外部 AI ツールによる節約は見られず、Gemini は測定されていません。大規模な読み取りは未測定です。
- テストされた 1 回の長時間セッションにおいて早期圧縮はコスト増となったため、オプトイン方式となっています。
- フッターは実行されたタスクではなく実測比率から推定されます。フックはチャットモデルを直接確認できないため、トランスクリプト、プロセスのフラグ、環境変数、設定の順に読み取ります。いずれにも記載がない場合、カードには上限不明と表示されます。
- ワーカーは通常のセッションと同様にプロジェクトのメモリファイルを読み込みます。ベンチマークのプロジェクトにはメモリファイルが存在しないため、そのコストは数値に含まれていません。

## よくある質問

**回答内容は変わりますか？** 高難度タスクでは単独の 70% に対し 69% の Issue を解決し、ばらつきの範囲内で同等でした。コードが同等の品質であるとは主張していません。

**フッターが表示されないことがあるのはなぜですか？** 何かがルーティングされ、かつお使いのモデル、effort、タスク種別において 1.15x 以上の節約が測定されている場合にのみ表示されます。

**Sonnet や Haiku で何もしないのはなぜですか？** Haiku は最も安価なモデルであるため、作業を委託できるさらに安価なモデルが存在しません。Sonnet では小規模タスクで損失（約 0.85x）が測定されたためチャット内に留められ、大規模タスクでの節約は未測定です。

**自分のクォータを消費しますか？** ワーカーはより安価なモデルで通常の Claude クォータを消費します。外部 AI ツールはそれぞれのクォータを消費し、ユーザーの Claude クォータは消費しません。

**サーバーに何か送信されますか？** ユーザーに関するデータを含まないモデルページの週 1 回のダウンロードと、明示的に指定した外部ツールに渡すファイルのみです。[マシン上での動作](#マシン上での動作) を参照してください。

**他に類似のツールはありますか？** ルータープロキシはシナリオに応じて他のプロバイダーへ API リクエストを送信し、サブエージェントモデル変数は 1 つのモデルをサブエージェントに固定し、ccusage などのメーターは事後的に支出を報告します。Token Beggar はセッション内で動作し、タスクと上限を評価し、その倍率は履歴ではなくベンチマークに基づきます。より短いプロンプトや小さなコンテキストと組み合わせて使用できます。ここに掲載されていないツールがある場合は、Issue を開いてください。

## ドキュメント

| 目的 | 参照先 |
| --- | --- |
| インストール、または 1 セッションのみ試す | [docs/install.md](docs/install.md) |
| ルーティング対象とコマンドを学ぶ | [docs/usage.md](docs/usage.md) |
| マシン上で行われる動作を確認する | [docs/on-your-machine.md](docs/on-your-machine.md) |
| 設定やルールを変更する | [docs/config.md](docs/config.md) |
| 各コンポーネントとモードを理解する | [docs/architecture.md](docs/architecture.md) |
| 数値を確認する、または再現する | [docs/benchmark.md](docs/benchmark.md) |
| 変更点を確認する | [CHANGELOG.md](CHANGELOG.md) |

## 開発

```
python3 -m unittest discover -s tests -t .
cd benchmark && python3 selftest.py
uvx ruff check . && uvx ruff format --check .
```

## コントリビューション

Issue やプルリクエストを歓迎します。カード、スキル、または `data/profiles.json` への変更には、事前と事後のベンチマーク実行が必要であり、改善点と併せて損失も報告する必要があります。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

MIT © Arthur031221

Assisted by Claude/Codex.
