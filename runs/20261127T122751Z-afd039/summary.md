## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@d4c1d043429de0cc104a29e7a72cefc9cdbd1aaf vs github:shohamyamin/trino@869ffdf528bb3fd83e91900517062c7d2dbae208

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 38.22 s | baseline | 48.10 s | 99 | 0 | 0 | 97 |
| change-d4c1d043429de0cc104a29e7a72cef/default (485-SNAPSHOT) | `github:shohamyamin/trino@d4c1d043429de0cc104a29e7a72cefc9cdbd1aaf` | 37.89 s | -1.5% | 47.94 s | 99 | 0 | 0 | 97 |
| target2-869ffdf528bb3fd83e91900517062c/default (485-SNAPSHOT) | `github:shohamyamin/trino@869ffdf528bb3fd83e91900517062c7d2dbae208` | 38.26 s | -0.2% | 48.07 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q77 | change-d4c1d043429de0cc104a29e7a72cef/default | -8.6% [-15%, -2%] |  |
| q89 | target2-869ffdf528bb3fd83e91900517062c/default | -7.7% [-17%, -2%] |  |
| q89 | change-d4c1d043429de0cc104a29e7a72cef/default | -7.3% [-16%, -0%] |  |
| q88 | target2-869ffdf528bb3fd83e91900517062c/default | -5.2% [-12%, -0%] |  |
| q95 | target2-869ffdf528bb3fd83e91900517062c/default | +6.6% [+0%, +13%] |  |

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
