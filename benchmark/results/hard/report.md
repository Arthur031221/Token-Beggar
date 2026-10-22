# Hard task benchmark results

86 runs, 19 tasks, Opus 5.5 at high effort as the chat model.

| setup | runs | cost per run | multiple vs Without Token Beggar (95% interval) | resolved | regressions | turns | seconds |
|---|---|---|---|---|---|---|---|
| Without Token Beggar | 32 | $0.67 | 1.00x | 62% | 0 | 22 | 148 |
| v0.2.0 (previous release) | 28 | $0.46 | 1.50x (1.45 to 1.54) | 57% | 0 | 14 | 188 |
| v0.3.0 (this release) | 26 | $0.66 | 1.04x (1.00 to 1.08) within noise | 65% | 0 | 23 | 240 |

## Per task

| task | setup | runs | cost per run | multiple | resolved | tests fixed | turns | seconds |
|---|---|---|---|---|---|---|---|---|
| click-format-filename | Without Token Beggar | 3 | $0.75 | 1.00x | 100% | 100% | 31 | 154 |
| click-format-filename | v0.2.0 (previous release) | 2 | $0.24 | 3.12x | 0% | 60% | 2 | 65 |
| click-format-filename | v0.3.0 (this release) | 1 | $0.67 | 1.12x | 100% | 100% | 27 | 130 |
| django-aggregate-count | Without Token Beggar | 1 | $0.86 | 1.00x | 0% | 67% | 4 | 96 |
| django-aggregate-count | v0.2.0 (previous release) | 1 | $0.90 | 0.95x | 0% | 67% | 33 | 911 |
| django-aggregate-count | v0.3.0 (this release) | 1 | $0.98 | 0.87x | 0% | 67% | 23 | 936 |
| django-constraint-violation | Without Token Beggar | 1 | $0.91 | 1.00x | 100% | 100% | 20 | 141 |
| django-constraint-violation | v0.2.0 (previous release) | 1 | $0.44 | 2.07x | 100% | 100% | 3 | 142 |
| django-constraint-violation | v0.3.0 (this release) | 1 | $0.85 | 1.07x | 100% | 100% | 18 | 143 |
| django-prefetch-sliced | Without Token Beggar | 1 | $0.90 | 1.00x | 100% | 100% | 27 | 211 |
| django-prefetch-sliced | v0.2.0 (previous release) | 1 | $0.45 | 2.02x | 100% | 100% | 20 | 93 |
| django-prefetch-sliced | v0.3.0 (this release) | 1 | $0.41 | 2.23x | 100% | 100% | 14 | 85 |
| django-remake-table-index | Without Token Beggar | 1 | $0.85 | 1.00x | 100% | 100% | 28 | 226 |
| django-remake-table-index | v0.2.0 (previous release) | 1 | $0.55 | 1.55x | 100% | 100% | 22 | 113 |
| django-remake-table-index | v0.3.0 (this release) | 1 | $0.90 | 0.94x | 100% | 100% | 36 | 210 |
| jinja-namespace-tuple | Without Token Beggar | 3 | $0.51 | 1.00x | 100% | 100% | 25 | 100 |
| jinja-namespace-tuple | v0.2.0 (previous release) | 2 | $0.60 | 0.85x | 100% | 100% | 30 | 128 |
| jinja-namespace-tuple | v0.3.0 (this release) | 1 | $0.56 | 0.92x | 100% | 100% | 30 | 163 |
| md-backslash-smarty | Without Token Beggar | 3 | $0.69 | 1.00x | 100% | 100% | 27 | 139 |
| md-backslash-smarty | v0.2.0 (previous release) | 3 | $0.67 | 1.03x | 100% | 100% | 26 | 125 |
| md-backslash-smarty | v0.3.0 (this release) | 2 | $0.82 | 0.84x | 100% | 100% | 33 | 145 |
| md-footnote-order | Without Token Beggar | 2 | $0.79 | 1.00x | 100% | 100% | 18 | 175 |
| md-footnote-order | v0.2.0 (previous release) | 2 | $0.30 | 2.63x | 100% | 100% | 3 | 103 |
| md-footnote-order | v0.3.0 (this release) | 3 | $0.72 | 1.09x | 100% | 100% | 19 | 158 |
| packaging-extras-marker | Without Token Beggar | 2 | $0.58 | 1.00x | 100% | 100% | 14 | 141 |
| packaging-extras-marker | v0.2.0 (previous release) | 3 | $0.36 | 1.61x | 67% | 97% | 3 | 95 |
| packaging-extras-marker | v0.3.0 (this release) | 2 | $0.62 | 0.94x | 100% | 100% | 13 | 122 |
| pylint-pyreverse-hints | Without Token Beggar | 1 | $1.25 | 1.00x | 0% | 0% | 37 | 254 |
| pylint-pyreverse-hints | v0.2.0 (previous release) | 1 | $0.35 | 3.55x | 0% | 80% | 4 | 103 |
| pylint-pyreverse-hints | v0.3.0 (this release) | 1 | $0.93 | 1.35x | 0% | 80% | 23 | 212 |
| pylint-regexp-csv | Without Token Beggar | 1 | $0.39 | 1.00x | 100% | 100% | 12 | 109 |
| pylint-regexp-csv | v0.2.0 (previous release) | 1 | $0.20 | 1.97x | 100% | 100% | 2 | 61 |
| pylint-regexp-csv | v0.3.0 (this release) | 1 | $0.58 | 0.67x | 0% | 50% | 24 | 469 |
| pytest-mark-mro | Without Token Beggar | 1 | $0.39 | 1.00x | 0% | 0% | 19 | 391 |
| pytest-mark-mro | v0.2.0 (previous release) | 1 | $0.22 | 1.81x | 0% | 0% | 2 | 79 |
| pytest-mark-mro | v0.3.0 (this release) | 1 | $0.37 | 1.07x | 100% | 100% | 20 | 584 |
| rich-inspect-methods | Without Token Beggar | 3 | $0.47 | 1.00x | 0% | 0% | 20 | 97 |
| rich-inspect-methods | v0.2.0 (previous release) | 2 | $0.46 | 1.01x | 0% | 0% | 24 | 87 |
| rich-inspect-methods | v0.3.0 (this release) | 2 | $0.49 | 0.96x | 0% | 0% | 13 | 55 |
| sphinx-include-source-read | Without Token Beggar | 1 | $0.67 | 1.00x | 100% | 100% | 28 | 227 |
| sphinx-include-source-read | v0.2.0 (previous release) | 1 | $0.33 | 2.02x | 100% | 100% | 3 | 103 |
| sphinx-include-source-read | v0.3.0 (this release) | 1 | $0.58 | 1.16x | 100% | 100% | 24 | 595 |
| sphinx-property-type | Without Token Beggar | 1 | $0.80 | 1.00x | 100% | 100% | 24 | 191 |
| sphinx-property-type | v0.2.0 (previous release) | 1 | $0.67 | 1.20x | 100% | 100% | 22 | 173 |
| sphinx-property-type | v0.3.0 (this release) | 1 | $0.91 | 0.88x | 100% | 100% | 39 | 684 |
| structlog-exception-outside | Without Token Beggar | 3 | $0.67 | 1.00x | 0% | 75% | 25 | 124 |
| structlog-exception-outside | v0.2.0 (previous release) | 1 | $0.58 | 1.15x | 0% | 0% | 32 | 105 |
| structlog-exception-outside | v0.3.0 (this release) | 3 | $0.59 | 1.13x | 0% | 75% | 30 | 111 |
| sympy-permutation-subclass | Without Token Beggar | 1 | $0.53 | 1.00x | 100% | 100% | 14 | 196 |
| sympy-permutation-subclass | v0.2.0 (previous release) | 1 | $0.51 | 1.03x | 100% | 100% | 18 | 348 |
| sympy-permutation-subclass | v0.3.0 (this release) | 1 | $0.46 | 1.15x | 100% | 100% | 15 | 327 |
| sympy-power-assumptions | Without Token Beggar | 1 | $0.82 | 1.00x | 0% | 0% | 1 | 3 |
| sympy-power-assumptions | v0.2.0 (previous release) | 1 | $0.69 | 1.20x | 0% | 0% | 25 | 1381 |
| werkzeug-rule-methods | Without Token Beggar | 2 | $0.52 | 1.00x | 0% | 50% | 18 | 113 |
| werkzeug-rule-methods | v0.2.0 (previous release) | 2 | $0.41 | 1.29x | 0% | 50% | 6 | 114 |
| werkzeug-rule-methods | v0.3.0 (this release) | 2 | $0.59 | 0.88x | 50% | 75% | 19 | 129 |

## Run to run spread of the resolved share (one value per rep)

- Without Token Beggar: rep 1 63%, rep 2 60%, rep 3 62%
- v0.2.0 (previous release): rep 1 59%, rep 2 43%, rep 3 75%
- v0.3.0 (this release): rep 1 62%, rep 2 80%, rep 3 60%
