## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@869ffdf528bb3fd83e91900517062c7d2dbae208

ClickBench (derived) SF10, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 33.01 s | baseline | 82.41 s | 43 | 0 | 0 | 0 |
| change-869ffdf528bb3fd83e91900517062c/default (485-SNAPSHOT) | `github:shohamyamin/trino@869ffdf528bb3fd83e91900517062c7d2dbae208` | 32.76 s | +0.2% | 82.65 s | 43 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q02 | change-869ffdf528bb3fd83e91900517062c/default | +5.8% [+1%, +11%] |  |
| q16 | change-869ffdf528bb3fd83e91900517062c/default | +7.8% [+3%, +11%] |  |
| q36 | change-869ffdf528bb3fd83e91900517062c/default | +14.0% [+2%, +21%] |  |

**Result sets differ between configurations:** q21, q22, q24, q30, q31, q32, q38, q39, q40

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
