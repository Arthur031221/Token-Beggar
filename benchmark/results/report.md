# Benchmark results

63 runs per arm (21 tasks), Opus 5.5 at high effort as the chat model. Cost at list price.

| class | cost alone | cost with | x cheaper | top-model tokens x | quality alone | quality with |
|---|---|---|---|---|---|---|
| mechanical | $1.11 | $0.80 | 1.4x | 1.86x | 1.00 | 1.00 |
| reading | $0.91 | $0.75 | 1.21x | 1.19x | 0.89 | 0.86 |
| routine_code | $1.47 | $1.32 | 1.12x | 1.25x | 1.00 | 1.00 |
| multi_file | $2.47 | $1.58 | 1.56x | 1.91x | 1.00 | 1.00 |
| debugging | $1.45 | $1.29 | 1.12x | 1.18x | 1.00 | 1.00 |
| design | $0.93 | $0.82 | 1.14x | 1.11x | 1.00 | 1.00 |
| review | $1.21 | $1.13 | 1.07x | 1.07x | 0.83 | 0.87 |
| **all** | $9.56 | $7.69 | 1.24x | 1.36x | 0.96 | 0.96 |

## Per task

| task | arm | cost | quality | turns | seconds |
|---|---|---|---|---|---|
| m1-rename | alone | $0.104 | 1.00 | 6 | 18.4 |
| m1-rename | alone | $0.103 | 1.00 | 6 | 10.9 |
| m1-rename | alone | $0.102 | 1.00 | 6 | 14.7 |
| m1-rename | beggar | $0.087 | 1.00 | 3 | 27.1 |
| m1-rename | beggar | $0.084 | 1.00 | 3 | 23.0 |
| m1-rename | beggar | $0.082 | 1.00 | 3 | 19.7 |
| m2-future | alone | $0.142 | 1.00 | 5 | 17.8 |
| m2-future | alone | $0.137 | 1.00 | 5 | 20.7 |
| m2-future | alone | $0.154 | 1.00 | 6 | 22.3 |
| m2-future | beggar | $0.089 | 1.00 | 3 | 32.0 |
| m2-future | beggar | $0.098 | 1.00 | 3 | 37.1 |
| m2-future | beggar | $0.091 | 1.00 | 3 | 36.1 |
| m3-todo | alone | $0.118 | 1.00 | 7 | 22.3 |
| m3-todo | alone | $0.125 | 1.00 | 8 | 15.2 |
| m3-todo | alone | $0.129 | 1.00 | 8 | 16.4 |
| m3-todo | beggar | $0.087 | 1.00 | 3 | 26.2 |
| m3-todo | beggar | $0.091 | 1.00 | 3 | 22.6 |
| m3-todo | beggar | $0.088 | 1.00 | 3 | 21.7 |
| r1-tracking | alone | $0.121 | 1.00 | 3 | 9.5 |
| r1-tracking | alone | $0.118 | 1.00 | 3 | 11.1 |
| r1-tracking | alone | $0.122 | 1.00 | 3 | 6.2 |
| r1-tracking | beggar | $0.078 | 1.00 | 3 | 7.3 |
| r1-tracking | beggar | $0.077 | 1.00 | 4 | 14.3 |
| r1-tracking | beggar | $0.088 | 1.00 | 3 | 7.8 |
| r2-toprate | alone | $0.078 | 1.00 | 3 | 5.0 |
| r2-toprate | alone | $0.083 | 1.00 | 4 | 6.1 |
| r2-toprate | alone | $0.084 | 1.00 | 3 | 8.4 |
| r2-toprate | beggar | $0.062 | 1.00 | 2 | 3.3 |
| r2-toprate | beggar | $0.063 | 1.00 | 2 | 5.4 |
| r2-toprate | beggar | $0.062 | 1.00 | 2 | 3.6 |
| r3-flow | alone | $0.093 | 0.75 | 6 | 12.2 |
| r3-flow | alone | $0.115 | 0.75 | 7 | 17.3 |
| r3-flow | alone | $0.099 | 0.50 | 4 | 15.1 |
| r3-flow | beggar | $0.111 | 0.75 | 5 | 34.4 |
| r3-flow | beggar | $0.095 | 0.50 | 3 | 25.4 |
| r3-flow | beggar | $0.117 | 0.50 | 3 | 23.6 |
| c1-coupon | alone | $0.226 | 1.00 | 9 | 41.1 |
| c1-coupon | alone | $0.281 | 1.00 | 8 | 39.2 |
| c1-coupon | alone | $0.285 | 1.00 | 10 | 38.6 |
| c1-coupon | beggar | $0.191 | 1.00 | 3 | 50.5 |
| c1-coupon | beggar | $0.175 | 1.00 | 4 | 53.8 |
| c1-coupon | beggar | $0.171 | 1.00 | 3 | 52.8 |
| c2-split | alone | $0.112 | 1.00 | 6 | 17.2 |
| c2-split | alone | $0.118 | 1.00 | 6 | 15.9 |
| c2-split | alone | $0.111 | 1.00 | 4 | 17.8 |
| c2-split | beggar | $0.134 | 1.00 | 3 | 29.2 |
| c2-split | beggar | $0.124 | 1.00 | 3 | 34.3 |
| c2-split | beggar | $0.118 | 1.00 | 3 | 29.4 |
| c3-json | alone | $0.114 | 1.00 | 4 | 12.3 |
| c3-json | alone | $0.114 | 1.00 | 4 | 15.4 |
| c3-json | alone | $0.114 | 1.00 | 4 | 12.8 |
| c3-json | beggar | $0.121 | 1.00 | 3 | 39.8 |
| c3-json | beggar | $0.163 | 1.00 | 7 | 52.5 |
| c3-json | beggar | $0.119 | 1.00 | 3 | 33.5 |
| f1-shipping | alone | $0.295 | 1.00 | 5 | 41.6 |
| f1-shipping | alone | $0.300 | 1.00 | 5 | 46.3 |
| f1-shipping | alone | $0.362 | 1.00 | 10 | 52.3 |
| f1-shipping | beggar | $0.223 | 1.00 | 5 | 71.5 |
| f1-shipping | beggar | $0.183 | 1.00 | 4 | 41.2 |
| f1-shipping | beggar | $0.177 | 1.00 | 3 | 52.1 |
| f2-refund | alone | $0.220 | 1.00 | 8 | 21.5 |
| f2-refund | alone | $0.223 | 1.00 | 8 | 26.7 |
| f2-refund | alone | $0.224 | 1.00 | 7 | 23.2 |
| f2-refund | beggar | $0.166 | 1.00 | 5 | 38.0 |
| f2-refund | beggar | $0.152 | 1.00 | 4 | 36.5 |
| f2-refund | beggar | $0.153 | 1.00 | 3 | 37.6 |
| f3-tier | alone | $0.271 | 1.00 | 6 | 36.3 |
| f3-tier | alone | $0.272 | 1.00 | 6 | 34.5 |
| f3-tier | alone | $0.297 | 1.00 | 7 | 41.2 |
| f3-tier | beggar | $0.158 | 1.00 | 3 | 43.9 |
| f3-tier | beggar | $0.169 | 1.00 | 3 | 45.7 |
| f3-tier | beggar | $0.196 | 1.00 | 4 | 42.7 |
| d1-cents | alone | $0.149 | 1.00 | 8 | 28.6 |
| d1-cents | alone | $0.144 | 1.00 | 8 | 19.9 |
| d1-cents | alone | $0.122 | 1.00 | 6 | 13.6 |
| d1-cents | beggar | $0.110 | 1.00 | 5 | 13.6 |
| d1-cents | beggar | $0.111 | 1.00 | 5 | 13.7 |
| d1-cents | beggar | $0.113 | 1.00 | 5 | 19.7 |
| d2-store | alone | $0.227 | 1.00 | 9 | 31.2 |
| d2-store | alone | $0.229 | 1.00 | 10 | 24.3 |
| d2-store | alone | $0.215 | 1.00 | 9 | 37.0 |
| d2-store | beggar | $0.184 | 1.00 | 7 | 26.3 |
| d2-store | beggar | $0.225 | 1.00 | 9 | 24.6 |
| d2-store | beggar | $0.201 | 1.00 | 8 | 23.3 |
| d3-remove | alone | $0.132 | 1.00 | 6 | 19.3 |
| d3-remove | alone | $0.117 | 1.00 | 6 | 15.4 |
| d3-remove | alone | $0.117 | 1.00 | 5 | 23.7 |
| d3-remove | beggar | $0.112 | 1.00 | 6 | 16.3 |
| d3-remove | beggar | $0.125 | 1.00 | 6 | 13.5 |
| d3-remove | beggar | $0.111 | 1.00 | 6 | 12.5 |
| g1-currency | alone | $0.144 | 1.00 | 4 | 20.5 |
| g1-currency | alone | $0.134 | 1.00 | 4 | 16.0 |
| g1-currency | alone | $0.134 | 1.00 | 4 | 15.3 |
| g1-currency | beggar | $0.120 | 1.00 | 3 | 17.2 |
| g1-currency | beggar | $0.118 | 1.00 | 3 | 16.0 |
| g1-currency | beggar | $0.128 | 1.00 | 3 | 20.3 |
| g2-store | alone | $0.089 | 1.00 | 3 | 14.6 |
| g2-store | alone | $0.100 | 1.00 | 4 | 12.8 |
| g2-store | alone | $0.091 | 1.00 | 3 | 14.7 |
| g2-store | beggar | $0.075 | 1.00 | 3 | 14.0 |
| g2-store | beggar | $0.078 | 1.00 | 3 | 12.8 |
| g2-store | beggar | $0.077 | 1.00 | 3 | 10.9 |
| g3-cache | alone | $0.080 | 1.00 | 2 | 14.7 |
| g3-cache | alone | $0.082 | 1.00 | 2 | 15.5 |
| g3-cache | alone | $0.080 | 1.00 | 2 | 13.8 |
| g3-cache | beggar | $0.073 | 1.00 | 2 | 16.8 |
| g3-cache | beggar | $0.076 | 1.00 | 2 | 16.6 |
| g3-cache | beggar | $0.074 | 1.00 | 2 | 16.8 |
| v1-diff | alone | $0.125 | 1.00 | 4 | 18.9 |
| v1-diff | alone | $0.137 | 1.00 | 5 | 24.2 |
| v1-diff | alone | $0.126 | 1.00 | 4 | 24.8 |
| v1-diff | beggar | $0.120 | 1.00 | 4 | 21.3 |
| v1-diff | beggar | $0.119 | 1.00 | 4 | 20.7 |
| v1-diff | beggar | $0.115 | 1.00 | 4 | 20.5 |
| v2-diff | alone | $0.122 | 1.00 | 4 | 21.3 |
| v2-diff | alone | $0.128 | 1.00 | 5 | 28.6 |
| v2-diff | alone | $0.110 | 0.50 | 4 | 17.6 |
| v2-diff | beggar | $0.110 | 0.50 | 4 | 21.4 |
| v2-diff | beggar | $0.120 | 1.00 | 7 | 23.3 |
| v2-diff | beggar | $0.105 | 1.00 | 4 | 17.6 |
| v3-carriers | alone | $0.160 | 0.67 | 5 | 17.8 |
| v3-carriers | alone | $0.143 | 0.67 | 5 | 20.0 |
| v3-carriers | alone | $0.157 | 0.67 | 3 | 15.6 |
| v3-carriers | beggar | $0.147 | 0.67 | 3 | 15.6 |
| v3-carriers | beggar | $0.136 | 0.67 | 4 | 17.6 |
| v3-carriers | beggar | $0.161 | 1.00 | 4 | 15.1 |
