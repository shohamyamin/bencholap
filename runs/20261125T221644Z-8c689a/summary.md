## bencholap: Benchmark: TPC-DS avg queries, 483 vs 484

TPC-DS (derived) SF1, layout `unpartitioned`, 2 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 2.71 s | baseline | 1.44 s | 6 | 0 | 21 | 6 |
| change-484/default (484) | `484` | 2.42 s | -10.9% | 1.38 s | 6 | 0 | 21 | 6 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q63 | change-484/default | -23.6% [-32%, -15%] | yes |
| q07 | change-484/default | -19.2% [-23%, -16%] | yes |

**Failures:**

- q06 on baseline-483/default: wrong_result 
- q06 on change-484/default: wrong_result 
- q09 on baseline-483/default: wrong_result 
- q09 on change-484/default: wrong_result 
- q13 on baseline-483/default: wrong_result 
- q13 on change-484/default: wrong_result 
- q14 on baseline-483/default: wrong_result 
- q14 on change-484/default: wrong_result 
- q17 on baseline-483/default: wrong_result 
- q17 on change-484/default: wrong_result 
- q18 on baseline-483/default: wrong_result 
- q18 on change-484/default: wrong_result 
- q22 on baseline-483/default: wrong_result 
- q22 on change-484/default: wrong_result 
- q24 on baseline-483/default: wrong_result 
- q24 on change-484/default: wrong_result 
- q26 on baseline-483/default: wrong_result 
- q26 on change-484/default: wrong_result 
- q27 on baseline-483/default: wrong_result 
- q27 on change-484/default: wrong_result 
- q28 on baseline-483/default: wrong_result 
- q28 on change-484/default: wrong_result 
- q30 on baseline-483/default: wrong_result 
- q30 on change-484/default: wrong_result 
- q35 on baseline-483/default: wrong_result 
- q35 on change-484/default: wrong_result 
- q39 on baseline-483/default: wrong_result 
- q39 on change-484/default: wrong_result 
- q44 on baseline-483/default: wrong_result 
- q44 on change-484/default: wrong_result 
- q47 on baseline-483/default: wrong_result 
- q47 on change-484/default: wrong_result 
- q57 on baseline-483/default: wrong_result 
- q57 on change-484/default: wrong_result 
- q65 on baseline-483/default: wrong_result 
- q65 on change-484/default: wrong_result 
- q81 on baseline-483/default: wrong_result 
- q81 on change-484/default: wrong_result 
- q85 on baseline-483/default: wrong_result 
- q85 on change-484/default: wrong_result 
- q89 on baseline-483/default: wrong_result 
- q89 on change-484/default: wrong_result 

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
