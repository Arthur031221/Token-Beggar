# Hard task benchmark results

229 runs, 18 tasks, Opus 5.5 at high effort as the chat model.

| setup | runs | cost per run | multiple vs Without Token Beggar (95% interval) | resolved | regressions | blind review (0 to 2) | turns | seconds |
|---|---|---|---|---|---|---|---|---|
| Without Token Beggar | 54 | $0.69 | 1.00x | 70% | 0 | 1.33 | 23 | 187 |
| Main before v0.3.0 (commit b761ce6) | 54 | $0.45 | 1.54x (1.46 to 1.64) | 65% | 0 | 1.15 | 13 | 163 |
| v0.3.0 (this release) | 54 | $0.49 | 1.42x (1.33 to 1.51) | 69% | 0 | 0.94 | 10 | 168 |
| Draft 2 of v0.3.0 (not shipped) | 41 | $0.49 | 1.44x (1.33 to 1.56) | 68% | 0 | not reviewed | 10 | 233 |
| Draft 1 of v0.3.0 (not shipped) | 26 | $0.66 | 1.04x (1.00 to 1.08) within noise | 65% | 0 | not reviewed | 23 | 240 |

## Per task

| task | setup | runs | cost per run | multiple | resolved | tests fixed | turns | seconds |
|---|---|---|---|---|---|---|---|---|
| click-format-filename | Without Token Beggar | 3 | $0.75 | 1.00x | 100% | 100% | 31 | 154 |
| click-format-filename | Main before v0.3.0 (commit b761ce6) | 3 | $0.24 | 3.12x | 0% | 53% | 2 | 65 |
| click-format-filename | v0.3.0 (this release) | 3 | $0.38 | 1.96x | 100% | 100% | 7 | 91 |
| click-format-filename | Draft 2 of v0.3.0 (not shipped) | 3 | $0.27 | 2.75x | 0% | 40% | 4 | 78 |
| click-format-filename | Draft 1 of v0.3.0 (not shipped) | 1 | $0.67 | 1.12x | 100% | 100% | 27 | 130 |
| django-aggregate-count | Without Token Beggar | 3 | $0.90 | 1.00x | 0% | 67% | 11 | 289 |
| django-aggregate-count | Main before v0.3.0 (commit b761ce6) | 3 | $0.87 | 1.03x | 0% | 67% | 29 | 870 |
| django-aggregate-count | v0.3.0 (this release) | 3 | $0.65 | 1.39x | 0% | 44% | 12 | 201 |
| django-aggregate-count | Draft 2 of v0.3.0 (not shipped) | 3 | $0.85 | 1.05x | 0% | 67% | 16 | 877 |
| django-aggregate-count | Draft 1 of v0.3.0 (not shipped) | 1 | $0.98 | 0.91x | 0% | 67% | 23 | 936 |
| django-constraint-violation | Without Token Beggar | 3 | $1.01 | 1.00x | 100% | 100% | 24 | 169 |
| django-constraint-violation | Main before v0.3.0 (commit b761ce6) | 3 | $0.38 | 2.66x | 100% | 100% | 3 | 125 |
| django-constraint-violation | v0.3.0 (this release) | 3 | $0.48 | 2.08x | 100% | 100% | 8 | 115 |
| django-constraint-violation | Draft 2 of v0.3.0 (not shipped) | 2 | $0.47 | 2.12x | 100% | 100% | 6 | 119 |
| django-constraint-violation | Draft 1 of v0.3.0 (not shipped) | 1 | $0.85 | 1.19x | 100% | 100% | 18 | 143 |
| django-prefetch-sliced | Without Token Beggar | 3 | $0.88 | 1.00x | 100% | 100% | 32 | 194 |
| django-prefetch-sliced | Main before v0.3.0 (commit b761ce6) | 3 | $0.40 | 2.17x | 100% | 100% | 8 | 120 |
| django-prefetch-sliced | v0.3.0 (this release) | 3 | $0.48 | 1.83x | 100% | 100% | 6 | 136 |
| django-prefetch-sliced | Draft 2 of v0.3.0 (not shipped) | 2 | $0.63 | 1.40x | 100% | 100% | 11 | 186 |
| django-prefetch-sliced | Draft 1 of v0.3.0 (not shipped) | 1 | $0.41 | 2.16x | 100% | 100% | 14 | 85 |
| django-remake-table-index | Without Token Beggar | 3 | $0.82 | 1.00x | 100% | 100% | 31 | 192 |
| django-remake-table-index | Main before v0.3.0 (commit b761ce6) | 3 | $0.53 | 1.55x | 100% | 100% | 19 | 114 |
| django-remake-table-index | v0.3.0 (this release) | 3 | $0.62 | 1.33x | 100% | 100% | 11 | 197 |
| django-remake-table-index | Draft 2 of v0.3.0 (not shipped) | 2 | $0.68 | 1.22x | 100% | 100% | 16 | 284 |
| django-remake-table-index | Draft 1 of v0.3.0 (not shipped) | 1 | $0.90 | 0.91x | 100% | 100% | 36 | 210 |
| jinja-namespace-tuple | Without Token Beggar | 3 | $0.51 | 1.00x | 100% | 100% | 25 | 100 |
| jinja-namespace-tuple | Main before v0.3.0 (commit b761ce6) | 3 | $0.56 | 0.91x | 100% | 100% | 27 | 119 |
| jinja-namespace-tuple | v0.3.0 (this release) | 3 | $0.40 | 1.28x | 100% | 100% | 6 | 114 |
| jinja-namespace-tuple | Draft 2 of v0.3.0 (not shipped) | 3 | $0.43 | 1.20x | 100% | 100% | 8 | 151 |
| jinja-namespace-tuple | Draft 1 of v0.3.0 (not shipped) | 1 | $0.56 | 0.92x | 100% | 100% | 30 | 163 |
| md-backslash-smarty | Without Token Beggar | 3 | $0.69 | 1.00x | 100% | 100% | 27 | 139 |
| md-backslash-smarty | Main before v0.3.0 (commit b761ce6) | 3 | $0.67 | 1.03x | 100% | 100% | 26 | 125 |
| md-backslash-smarty | v0.3.0 (this release) | 3 | $0.63 | 1.09x | 67% | 67% | 18 | 154 |
| md-backslash-smarty | Draft 2 of v0.3.0 (not shipped) | 2 | $0.64 | 1.07x | 50% | 50% | 18 | 195 |
| md-backslash-smarty | Draft 1 of v0.3.0 (not shipped) | 2 | $0.82 | 0.84x | 100% | 100% | 33 | 145 |
| md-footnote-order | Without Token Beggar | 3 | $0.83 | 1.00x | 100% | 100% | 18 | 181 |
| md-footnote-order | Main before v0.3.0 (commit b761ce6) | 3 | $0.40 | 2.08x | 100% | 100% | 5 | 121 |
| md-footnote-order | v0.3.0 (this release) | 3 | $0.48 | 1.74x | 100% | 100% | 9 | 141 |
| md-footnote-order | Draft 2 of v0.3.0 (not shipped) | 3 | $0.46 | 1.80x | 100% | 100% | 9 | 135 |
| md-footnote-order | Draft 1 of v0.3.0 (not shipped) | 3 | $0.72 | 1.15x | 100% | 100% | 19 | 158 |
| packaging-extras-marker | Without Token Beggar | 3 | $0.59 | 1.00x | 100% | 100% | 15 | 146 |
| packaging-extras-marker | Main before v0.3.0 (commit b761ce6) | 3 | $0.36 | 1.64x | 67% | 97% | 3 | 95 |
| packaging-extras-marker | v0.3.0 (this release) | 3 | $0.43 | 1.39x | 100% | 100% | 7 | 184 |
| packaging-extras-marker | Draft 2 of v0.3.0 (not shipped) | 3 | $0.43 | 1.38x | 67% | 97% | 8 | 171 |
| packaging-extras-marker | Draft 1 of v0.3.0 (not shipped) | 2 | $0.62 | 0.96x | 100% | 100% | 13 | 122 |
| pylint-pyreverse-hints | Without Token Beggar | 3 | $1.16 | 1.00x | 33% | 60% | 32 | 259 |
| pylint-pyreverse-hints | Main before v0.3.0 (commit b761ce6) | 3 | $0.35 | 3.30x | 0% | 80% | 2 | 62 |
| pylint-pyreverse-hints | v0.3.0 (this release) | 3 | $0.65 | 1.78x | 0% | 80% | 16 | 213 |
| pylint-pyreverse-hints | Draft 2 of v0.3.0 (not shipped) | 3 | $0.53 | 2.18x | 67% | 93% | 12 | 245 |
| pylint-pyreverse-hints | Draft 1 of v0.3.0 (not shipped) | 1 | $0.93 | 1.25x | 0% | 80% | 23 | 212 |
| pylint-regexp-csv | Without Token Beggar | 3 | $0.42 | 1.00x | 67% | 83% | 16 | 149 |
| pylint-regexp-csv | Main before v0.3.0 (commit b761ce6) | 3 | $0.29 | 1.44x | 100% | 100% | 6 | 77 |
| pylint-regexp-csv | v0.3.0 (this release) | 3 | $0.36 | 1.16x | 100% | 100% | 9 | 120 |
| pylint-regexp-csv | Draft 2 of v0.3.0 (not shipped) | 3 | $0.34 | 1.23x | 100% | 100% | 8 | 138 |
| pylint-regexp-csv | Draft 1 of v0.3.0 (not shipped) | 1 | $0.58 | 0.72x | 0% | 50% | 24 | 469 |
| pytest-mark-mro | Without Token Beggar | 3 | $0.42 | 1.00x | 67% | 67% | 22 | 332 |
| pytest-mark-mro | Main before v0.3.0 (commit b761ce6) | 3 | $0.22 | 1.90x | 67% | 67% | 2 | 78 |
| pytest-mark-mro | v0.3.0 (this release) | 3 | $0.30 | 1.39x | 67% | 67% | 7 | 304 |
| pytest-mark-mro | Draft 2 of v0.3.0 (not shipped) | 3 | $0.32 | 1.32x | 33% | 33% | 8 | 168 |
| pytest-mark-mro | Draft 1 of v0.3.0 (not shipped) | 1 | $0.37 | 1.14x | 100% | 100% | 20 | 584 |
| rich-inspect-methods | Without Token Beggar | 3 | $0.47 | 1.00x | 0% | 0% | 20 | 97 |
| rich-inspect-methods | Main before v0.3.0 (commit b761ce6) | 3 | $0.49 | 0.96x | 0% | 0% | 24 | 95 |
| rich-inspect-methods | v0.3.0 (this release) | 3 | $0.32 | 1.46x | 0% | 0% | 7 | 72 |
| rich-inspect-methods | Draft 1 of v0.3.0 (not shipped) | 2 | $0.49 | 0.96x | 0% | 0% | 13 | 55 |
| sphinx-include-source-read | Without Token Beggar | 3 | $0.53 | 1.00x | 100% | 100% | 22 | 304 |
| sphinx-include-source-read | Main before v0.3.0 (commit b761ce6) | 3 | $0.42 | 1.24x | 100% | 100% | 14 | 229 |
| sphinx-include-source-read | v0.3.0 (this release) | 3 | $0.39 | 1.35x | 100% | 100% | 9 | 166 |
| sphinx-include-source-read | Draft 2 of v0.3.0 (not shipped) | 3 | $0.34 | 1.56x | 100% | 100% | 9 | 173 |
| sphinx-include-source-read | Draft 1 of v0.3.0 (not shipped) | 1 | $0.58 | 0.91x | 100% | 100% | 24 | 595 |
| sphinx-property-type | Without Token Beggar | 3 | $0.80 | 1.00x | 100% | 100% | 25 | 281 |
| sphinx-property-type | Main before v0.3.0 (commit b761ce6) | 3 | $0.48 | 1.66x | 100% | 100% | 11 | 183 |
| sphinx-property-type | v0.3.0 (this release) | 3 | $0.58 | 1.37x | 100% | 100% | 12 | 212 |
| sphinx-property-type | Draft 2 of v0.3.0 (not shipped) | 3 | $0.63 | 1.26x | 100% | 100% | 19 | 329 |
| sphinx-property-type | Draft 1 of v0.3.0 (not shipped) | 1 | $0.91 | 0.88x | 100% | 100% | 39 | 684 |
| structlog-exception-outside | Without Token Beggar | 3 | $0.67 | 1.00x | 0% | 75% | 25 | 124 |
| structlog-exception-outside | Main before v0.3.0 (commit b761ce6) | 3 | $0.50 | 1.34x | 0% | 50% | 22 | 98 |
| structlog-exception-outside | v0.3.0 (this release) | 3 | $0.74 | 0.91x | 0% | 50% | 25 | 174 |
| structlog-exception-outside | Draft 1 of v0.3.0 (not shipped) | 3 | $0.59 | 1.13x | 0% | 75% | 30 | 111 |
| sympy-permutation-subclass | Without Token Beggar | 3 | $0.50 | 1.00x | 100% | 100% | 14 | 149 |
| sympy-permutation-subclass | Main before v0.3.0 (commit b761ce6) | 3 | $0.45 | 1.11x | 100% | 100% | 18 | 242 |
| sympy-permutation-subclass | v0.3.0 (this release) | 3 | $0.45 | 1.13x | 100% | 100% | 6 | 309 |
| sympy-permutation-subclass | Draft 2 of v0.3.0 (not shipped) | 1 | $0.42 | 1.21x | 100% | 100% | 8 | 318 |
| sympy-permutation-subclass | Draft 1 of v0.3.0 (not shipped) | 1 | $0.46 | 1.10x | 100% | 100% | 15 | 327 |
| werkzeug-rule-methods | Without Token Beggar | 3 | $0.52 | 1.00x | 0% | 50% | 19 | 113 |
| werkzeug-rule-methods | Main before v0.3.0 (commit b761ce6) | 3 | $0.46 | 1.13x | 33% | 67% | 8 | 120 |
| werkzeug-rule-methods | v0.3.0 (this release) | 3 | $0.46 | 1.15x | 0% | 50% | 10 | 130 |
| werkzeug-rule-methods | Draft 2 of v0.3.0 (not shipped) | 2 | $0.43 | 1.23x | 0% | 50% | 10 | 131 |
| werkzeug-rule-methods | Draft 1 of v0.3.0 (not shipped) | 2 | $0.59 | 0.88x | 50% | 75% | 19 | 129 |

## Run to run spread of the resolved share (one value per rep)

- Without Token Beggar: rep 1 67%, rep 2 78%, rep 3 67%
- Main before v0.3.0 (commit b761ce6): rep 1 61%, rep 2 67%, rep 3 67%
- v0.3.0 (this release): rep 1 67%, rep 2 67%, rep 3 72%
- Draft 2 of v0.3.0 (not shipped): rep 1 67%, rep 2 62%, rep 3 77%
- Draft 1 of v0.3.0 (not shipped): rep 1 62%, rep 2 80%, rep 3 60%
