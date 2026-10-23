# Hard task benchmark results

111 runs, 19 tasks, Opus 5.5 at high effort as the chat model.

| setup | runs | cost per run | multiple vs Without Token Beggar (95% interval) | resolved | regressions | turns | seconds |
|---|---|---|---|---|---|---|---|
| Without Token Beggar | 32 | $0.67 | 1.00x | 62% | 0 | 22 | 148 |
| v0.2.0 (previous release) | 28 | $0.46 | 1.50x (1.45 to 1.54) | 57% | 0 | 14 | 188 |
| v0.3.0 (this release) | 51 | $0.39 | 1.82x (1.62 to 2.09) | 57% | 0 | 9 | 188 |

## Per task

| task | setup | runs | cost per run | multiple | resolved | tests fixed | turns | seconds |
|---|---|---|---|---|---|---|---|---|
| click-format-filename | Without Token Beggar | 3 | $0.75 | 1.00x | 100% | 100% | 31 | 154 |
| click-format-filename | v0.2.0 (previous release) | 2 | $0.24 | 3.12x | 0% | 60% | 2 | 65 |
| click-format-filename | v0.3.0 (this release) | 3 | $0.27 | 2.75x | 0% | 40% | 4 | 78 |
| django-aggregate-count | Without Token Beggar | 1 | $0.86 | 1.00x | 0% | 67% | 4 | 96 |
| django-aggregate-count | v0.2.0 (previous release) | 1 | $0.90 | 0.95x | 0% | 67% | 33 | 911 |
| django-aggregate-count | v0.3.0 (this release) | 3 | $0.85 | 1.01x | 0% | 67% | 16 | 877 |
| django-constraint-violation | Without Token Beggar | 1 | $0.91 | 1.00x | 100% | 100% | 20 | 141 |
| django-constraint-violation | v0.2.0 (previous release) | 1 | $0.44 | 2.07x | 100% | 100% | 3 | 142 |
| django-constraint-violation | v0.3.0 (this release) | 3 | $0.37 | 2.44x | 100% | 100% | 4 | 93 |
| django-prefetch-sliced | Without Token Beggar | 1 | $0.90 | 1.00x | 100% | 100% | 27 | 211 |
| django-prefetch-sliced | v0.2.0 (previous release) | 1 | $0.45 | 2.02x | 100% | 100% | 20 | 93 |
| django-prefetch-sliced | v0.3.0 (this release) | 3 | $0.42 | 2.17x | 67% | 67% | 8 | 124 |
| django-remake-table-index | Without Token Beggar | 1 | $0.85 | 1.00x | 100% | 100% | 28 | 226 |
| django-remake-table-index | v0.2.0 (previous release) | 1 | $0.55 | 1.55x | 100% | 100% | 22 | 113 |
| django-remake-table-index | v0.3.0 (this release) | 3 | $0.45 | 1.88x | 67% | 67% | 11 | 189 |
| jinja-namespace-tuple | Without Token Beggar | 3 | $0.51 | 1.00x | 100% | 100% | 25 | 100 |
| jinja-namespace-tuple | v0.2.0 (previous release) | 2 | $0.60 | 0.85x | 100% | 100% | 30 | 128 |
| jinja-namespace-tuple | v0.3.0 (this release) | 3 | $0.43 | 1.20x | 100% | 100% | 8 | 151 |
| md-backslash-smarty | Without Token Beggar | 3 | $0.69 | 1.00x | 100% | 100% | 27 | 139 |
| md-backslash-smarty | v0.2.0 (previous release) | 3 | $0.67 | 1.03x | 100% | 100% | 26 | 125 |
| md-backslash-smarty | v0.3.0 (this release) | 3 | $0.43 | 1.61x | 33% | 33% | 13 | 130 |
| md-footnote-order | Without Token Beggar | 2 | $0.79 | 1.00x | 100% | 100% | 18 | 175 |
| md-footnote-order | v0.2.0 (previous release) | 2 | $0.30 | 2.63x | 100% | 100% | 3 | 103 |
| md-footnote-order | v0.3.0 (this release) | 3 | $0.46 | 1.71x | 100% | 100% | 9 | 135 |
| packaging-extras-marker | Without Token Beggar | 2 | $0.58 | 1.00x | 100% | 100% | 14 | 141 |
| packaging-extras-marker | v0.2.0 (previous release) | 3 | $0.36 | 1.61x | 67% | 97% | 3 | 95 |
| packaging-extras-marker | v0.3.0 (this release) | 3 | $0.43 | 1.36x | 67% | 97% | 8 | 171 |
| pylint-pyreverse-hints | Without Token Beggar | 1 | $1.25 | 1.00x | 0% | 0% | 37 | 254 |
| pylint-pyreverse-hints | v0.2.0 (previous release) | 1 | $0.35 | 3.55x | 0% | 80% | 4 | 103 |
| pylint-pyreverse-hints | v0.3.0 (this release) | 3 | $0.53 | 2.34x | 67% | 93% | 12 | 245 |
| pylint-regexp-csv | Without Token Beggar | 1 | $0.39 | 1.00x | 100% | 100% | 12 | 109 |
| pylint-regexp-csv | v0.2.0 (previous release) | 1 | $0.20 | 1.97x | 100% | 100% | 2 | 61 |
| pylint-regexp-csv | v0.3.0 (this release) | 3 | $0.34 | 1.15x | 100% | 100% | 8 | 138 |
| pytest-mark-mro | Without Token Beggar | 1 | $0.39 | 1.00x | 0% | 0% | 19 | 391 |
| pytest-mark-mro | v0.2.0 (previous release) | 1 | $0.22 | 1.81x | 0% | 0% | 2 | 79 |
| pytest-mark-mro | v0.3.0 (this release) | 3 | $0.32 | 1.24x | 33% | 33% | 8 | 168 |
| rich-inspect-methods | Without Token Beggar | 3 | $0.47 | 1.00x | 0% | 0% | 20 | 97 |
| rich-inspect-methods | v0.2.0 (previous release) | 2 | $0.46 | 1.01x | 0% | 0% | 24 | 87 |
| sphinx-include-source-read | Without Token Beggar | 1 | $0.67 | 1.00x | 100% | 100% | 28 | 227 |
| sphinx-include-source-read | v0.2.0 (previous release) | 1 | $0.33 | 2.02x | 100% | 100% | 3 | 103 |
| sphinx-include-source-read | v0.3.0 (this release) | 3 | $0.34 | 1.99x | 100% | 100% | 9 | 173 |
| sphinx-property-type | Without Token Beggar | 1 | $0.80 | 1.00x | 100% | 100% | 24 | 191 |
| sphinx-property-type | v0.2.0 (previous release) | 1 | $0.67 | 1.20x | 100% | 100% | 22 | 173 |
| sphinx-property-type | v0.3.0 (this release) | 3 | $0.63 | 1.26x | 100% | 100% | 19 | 329 |
| structlog-exception-outside | Without Token Beggar | 3 | $0.67 | 1.00x | 0% | 75% | 25 | 124 |
| structlog-exception-outside | v0.2.0 (previous release) | 1 | $0.58 | 1.15x | 0% | 0% | 32 | 105 |
| sympy-permutation-subclass | Without Token Beggar | 1 | $0.53 | 1.00x | 100% | 100% | 14 | 196 |
| sympy-permutation-subclass | v0.2.0 (previous release) | 1 | $0.51 | 1.03x | 100% | 100% | 18 | 348 |
| sympy-permutation-subclass | v0.3.0 (this release) | 3 | $0.14 | 3.80x | 33% | 33% | 3 | 106 |
| sympy-power-assumptions | Without Token Beggar | 1 | $0.82 | 1.00x | 0% | 0% | 1 | 3 |
| sympy-power-assumptions | v0.2.0 (previous release) | 1 | $0.69 | 1.20x | 0% | 0% | 25 | 1381 |
| sympy-power-assumptions | v0.3.0 (this release) | 3 | $0.00 | 0.00x | 0% | 0% | 1 | 1 |
| werkzeug-rule-methods | Without Token Beggar | 2 | $0.52 | 1.00x | 0% | 50% | 18 | 113 |
| werkzeug-rule-methods | v0.2.0 (previous release) | 2 | $0.41 | 1.29x | 0% | 50% | 6 | 114 |
| werkzeug-rule-methods | v0.3.0 (this release) | 3 | $0.29 | 1.83x | 0% | 33% | 7 | 88 |

## Run to run spread of the resolved share (one value per rep)

- Without Token Beggar: rep 1 63%, rep 2 60%, rep 3 62%
- v0.2.0 (previous release): rep 1 59%, rep 2 43%, rep 3 75%
- v0.3.0 (this release): rep 1 59%, rep 2 53%, rep 3 59%
