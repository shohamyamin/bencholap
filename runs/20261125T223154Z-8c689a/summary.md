## bencholap: Benchmark: TPC-DS avg queries, 483 vs 484

TPC-DS (derived) SF1, layout `unpartitioned`, 2 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 20.68 s | baseline | 23.06 s | 24 | 0 | 3 | 24 |
| change-484/default (484) | `484` | 20.10 s | -5.3% | 23.36 s | 24 | 0 | 3 | 24 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q27 | change-484/default | -20.8% [-30%, -11%] | yes |
| q17 | change-484/default | -16.5% [-29%, -2%] | yes |
| q18 | change-484/default | -13.6% [-20%, -7%] | yes |
| q92 | change-484/default | -12.5% [-16%, -9%] | yes |
| q65 | change-484/default | -10.1% [-11%, -9%] | yes |
| q57 | change-484/default | -6.8% [-11%, -2%] | yes |
| q14 | change-484/default | -5.4% [-11%, -0%] | yes |
| q09 | change-484/default | +11.2% [+1%, +22%] |  |
| q13 | change-484/default | +12.3% [+5%, +21%] | yes |
| q22 | change-484/default | +12.5% [+5%, +21%] | yes |
| q28 | change-484/default | +17.6% [+8%, +29%] | yes |

**Failures:**

- q24 on baseline-483/default: wrong_result 
- q24 on change-484/default: wrong_result 
- q30 on baseline-483/default: wrong_result 
- q30 on change-484/default: wrong_result 
- q85 on baseline-483/default: wrong_result 
- q85 on change-484/default: wrong_result 

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
