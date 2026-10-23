# Changelog

## 0.3.0 - 2026-10-23

- Size aware strategy. The card now decides by the size of the task first and by the model second. A small task (about 3 steps, one or two files, a one shot answer) is done in the chat with no worker and no footer. A large task (an issue in code the model has not read, several files, an edit and test loop, large reads) goes to one worker, whatever the chat model, except on Haiku. A task that grows past about 5 steps becomes large. The chat keeps the plan, the root cause and the final answer, and reads the whole `git diff` before it answers. The worker reports in under 150 words and lists every site that shares the symptom, and the chat checks that list.
- Hard task benchmark. 18 merged pull requests from 12 open source Python projects, scored by the maintainers' own tests that the chat never sees, 3 runs per task and setup, Opus 5.5 at high effort. Without Token Beggar the cost per run is $0.69 and 70% of issues are resolved. v0.3.0 costs $0.49 (1.42x, interval 1.33 to 1.51) and resolves 69%. The card on main before this release was cheaper (1.54x) and resolved 65%, and was set aside because it stopped after 2 turns with a wrong fix on one task. A blind review by a small model rated the v0.3.0 diffs lower (0.94 against 1.33 alone). That review is weak evidence, and it is reported for that reason. All 229 raw runs are in `benchmark/results/hard`, with the task list, base commits and install commands in [docs/benchmark.md](docs/benchmark.md).
- Small task benchmark, unchanged from before: 1.11x over 28 tasks, under the 1.15x line, so it is not claimed as a saving. It was not re-run for v0.3.0, because small tasks stay in the chat in both cards.
- Stand down modes. `full`, `sized` and `off` are chosen from the model and effort of the chat and the measured table in `data/measured.json`. `token-beggar mode --all` prints the grid and `TOKEN_BEGGAR_MODE` forces one. Haiku gets `off`, since there is nothing cheaper to send work to.
- The footer shows the quota multiple and the dollars saved (estimated), never token counts. It states no multiple under 1.15x.
- When you set your own compaction window, Token Beggar uses your value and stops choosing the point, and it keeps the note and the deferral of an automatic compaction in the middle of a step. It used to turn the deferral off too.
- On max effort for a small task the card adds one line suggesting a lower effort. It can only suggest.
- `docs/on-your-machine.md` lists everything the plugin reads, runs, sends and writes, and how to turn it off. The README leads with the same summary.
- New README with a banner, badges, charts that show one question each, and eight translations (Traditional and Simplified Chinese, Japanese, Korean, Spanish, French, German, Brazilian Portuguese).
- Tried and reverted, both documented in [docs/benchmark.md](docs/benchmark.md): reading in bulk with an outside tool (agy), which showed no saving on small files, and early compaction, which cost more in the one long session tested and stays opt in with `TOKEN_BEGGAR_EARLY=1`.
- The plugin manifest, the package and the module now say 0.3.0. The manifest still said 0.2.0 while main had moved on.

## 0.2.0 - 2026-10-22

- `token-beggar doctor` lists what can quietly stop routing, and `token-beggar stats` shows spend from your own sessions.
- Install steps on the first screen of the README.

## 0.1.0 - 2026-10-22

- First release: a skill, hooks, a lean worker and a CLI that route each task to the cheapest model and effort that keeps the answer the same.
