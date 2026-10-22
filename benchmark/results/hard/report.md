# Hard task benchmark results

42 runs, 8 tasks, Opus 5.5 at high effort as the chat model.

| setup | runs | cost per run | multiple vs Without Token Beggar (95% interval) | resolved | regressions | turns | seconds |
|---|---|---|---|---|---|---|---|
| Without Token Beggar | 16 | $0.61 | 1.00x | 69% | 0 | 23 | 125 |
| v0.2.0 (previous release) | 13 | $0.45 | 1.39x (1.28 to 1.49) | 54% | 0 | 14 | 103 |
| v0.3.0 (this release) | 13 | $0.66 | 0.95x (0.85 to 1.06) within noise | 62% | 0 | 24 | 133 |

## Per task

| task | setup | runs | cost per run | multiple | resolved | tests fixed | turns | seconds |
|---|---|---|---|---|---|---|---|---|
| click-format-filename | Without Token Beggar | 2 | $0.77 | 1.00x | 100% | 100% | 31 | 148 |
| click-format-filename | v0.2.0 (previous release) | 2 | $0.24 | 3.19x | 0% | 60% | 2 | 65 |
| click-format-filename | v0.3.0 (this release) | 1 | $0.67 | 1.14x | 100% | 100% | 27 | 130 |
| jinja-namespace-tuple | Without Token Beggar | 3 | $0.51 | 1.00x | 100% | 100% | 25 | 100 |
| jinja-namespace-tuple | v0.2.0 (previous release) | 2 | $0.60 | 0.85x | 100% | 100% | 30 | 128 |
| md-backslash-smarty | Without Token Beggar | 3 | $0.69 | 1.00x | 100% | 100% | 27 | 139 |
| md-backslash-smarty | v0.2.0 (previous release) | 2 | $0.64 | 1.08x | 100% | 100% | 22 | 114 |
| md-backslash-smarty | v0.3.0 (this release) | 2 | $0.82 | 0.84x | 100% | 100% | 33 | 145 |
| md-footnote-order | Without Token Beggar | 2 | $0.79 | 1.00x | 100% | 100% | 18 | 175 |
| md-footnote-order | v0.2.0 (previous release) | 2 | $0.30 | 2.63x | 100% | 100% | 3 | 103 |
| md-footnote-order | v0.3.0 (this release) | 3 | $0.72 | 1.09x | 100% | 100% | 19 | 158 |
| packaging-extras-marker | Without Token Beggar | 1 | $0.55 | 1.00x | 100% | 100% | 14 | 125 |
| packaging-extras-marker | v0.2.0 (previous release) | 2 | $0.34 | 1.63x | 50% | 95% | 3 | 88 |
| packaging-extras-marker | v0.3.0 (this release) | 1 | $0.65 | 0.85x | 100% | 100% | 14 | 131 |
| rich-inspect-methods | Without Token Beggar | 3 | $0.47 | 1.00x | 0% | 0% | 20 | 97 |
| rich-inspect-methods | v0.2.0 (previous release) | 1 | $0.53 | 0.88x | 0% | 0% | 27 | 100 |
| rich-inspect-methods | v0.3.0 (this release) | 1 | $0.53 | 0.87x | 0% | 0% | 25 | 106 |
| structlog-exception-outside | v0.2.0 (previous release) | 1 | $0.58 | 0.00x | 0% | 0% | 32 | 105 |
| structlog-exception-outside | v0.3.0 (this release) | 3 | $0.59 | 0.00x | 0% | 75% | 30 | 111 |
| werkzeug-rule-methods | Without Token Beggar | 2 | $0.52 | 1.00x | 0% | 50% | 18 | 113 |
| werkzeug-rule-methods | v0.2.0 (previous release) | 1 | $0.44 | 1.18x | 0% | 50% | 6 | 132 |
| werkzeug-rule-methods | v0.3.0 (this release) | 2 | $0.59 | 0.88x | 50% | 75% | 19 | 129 |

## Run to run spread of the resolved share (one value per rep)

- Without Token Beggar: rep 1 71%, rep 2 67%, rep 3 67%
- v0.2.0 (previous release): rep 1 40%, rep 2 40%, rep 3 100%
- v0.3.0 (this release): rep 1 50%, rep 2 67%, rep 3 75%
