## bencholap: 483 vs 484

TPC-H (derived) SF1, layout `unpartitioned`, 2 measured runs per query (1 warmup, 1 round(s)). Machine: gh-distributed: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 2 worker(s), 4g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 18.87 s | baseline | 14.79 s | 22 | 0 | 0 | 22 |
| change-484/default (484) | `484` | 17.73 s | -5.4% | 14.40 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q11 | change-484/default | -28.8% [-30%, -27%] | yes |
| q20 | change-484/default | -18.0% [-24%, -11%] | yes |
| q08 | change-484/default | -17.1% [-21%, -13%] | yes |
| q21 | change-484/default | -17.0% [-29%, -3%] | yes |
| q18 | change-484/default | -10.2% [-13%, -7%] | yes |
| q15 | change-484/default | +14.9% [+6%, +24%] | yes |

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
