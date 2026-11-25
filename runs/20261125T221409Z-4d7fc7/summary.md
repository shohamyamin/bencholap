## bencholap: 483 vs 484

TPC-H (derived) SF1, layout `unpartitioned`, 5 measured runs per query (1 warmup, 2 round(s)). Machine: gh-standard: 4x AMD EPYC 7763 64-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 15.81 s | baseline | 15.52 s | 22 | 0 | 0 | 22 |
| change-484/default (484) | `484` | 14.71 s | -6.9% | 15.04 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q08 | change-484/default | -22.2% [-32%, -17%] | yes |
| q04 | change-484/default | -15.9% [-24%, -2%] | yes |
| q18 | change-484/default | -11.0% [-14%, -2%] | yes |
| q05 | change-484/default | -8.2% [-14%, -3%] | yes |
| q17 | change-484/default | -8.0% [-13%, -3%] | yes |
| q13 | change-484/default | -7.1% [-12%, -2%] | yes |

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
