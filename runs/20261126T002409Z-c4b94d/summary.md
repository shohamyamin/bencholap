## bencholap: Benchmark: TPC-DS SF1, 483 vs 484

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (1 warmup, 2 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 69.99 s | baseline | 71.04 s | 99 | 0 | 0 | 97 |
| change-484/default (484) | `484` | 60.05 s | -14.6% | 69.02 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q64 | change-484/default | -53.8% [-57%, -50%] | yes |
| q72 | change-484/default | -51.4% [-55%, -45%] | yes |
| q29 | change-484/default | -41.7% [-45%, -35%] | yes |
| q85 | change-484/default | -37.0% [-43%, -34%] | yes |
| q84 | change-484/default | -35.4% [-47%, -17%] | yes |
| q25 | change-484/default | -34.2% [-42%, -25%] | yes |
| q91 | change-484/default | -32.6% [-42%, -23%] | yes |
| q17 | change-484/default | -32.0% [-36%, -25%] | yes |
| q73 | change-484/default | -30.1% [-40%, -7%] | yes |
| q99 | change-484/default | -28.4% [-36%, -13%] | yes |
| q93 | change-484/default | -26.8% [-38%, -10%] | yes |
| q62 | change-484/default | -26.5% [-39%, -1%] | yes |
| q98 | change-484/default | -24.7% [-29%, -3%] | yes |
| q50 | change-484/default | -24.0% [-30%, -6%] | yes |
| q60 | change-484/default | -23.9% [-35%, -3%] | yes |
| q03 | change-484/default | -22.7% [-30%, -5%] | yes |
| q56 | change-484/default | -22.5% [-31%, -5%] | yes |
| q95 | change-484/default | -22.4% [-33%, -16%] | yes |
| q61 | change-484/default | -21.9% [-40%, -14%] | yes |
| q96 | change-484/default | -21.7% [-30%, -4%] | yes |
| q18 | change-484/default | -21.5% [-30%, -11%] | yes |
| q37 | change-484/default | -21.4% [-29%, -0%] |  |
| q27 | change-484/default | -21.1% [-28%, -13%] | yes |
| q19 | change-484/default | -20.6% [-29%, -10%] | yes |
| q52 | change-484/default | -19.4% [-40%, -3%] | yes |
| q54 | change-484/default | -19.4% [-33%, -4%] | yes |
| q71 | change-484/default | -19.3% [-31%, -3%] | yes |
| q80 | change-484/default | -19.1% [-29%, -8%] | yes |
| q12 | change-484/default | -17.8% [-34%, -1%] | yes |
| q55 | change-484/default | -17.8% [-30%, -7%] | yes |
| q58 | change-484/default | -17.7% [-32%, -1%] | yes |
| q32 | change-484/default | -16.4% [-30%, -4%] | yes |
| q24 | change-484/default | -16.2% [-23%, -5%] | yes |
| q74 | change-484/default | -15.9% [-19%, -4%] | yes |
| q02 | change-484/default | -15.7% [-22%, -4%] | yes |
| q89 | change-484/default | -15.1% [-30%, -3%] | yes |
| q39 | change-484/default | -14.6% [-22%, -7%] | yes |
| q26 | change-484/default | -14.1% [-21%, -7%] | yes |
| q45 | change-484/default | -13.7% [-24%, -3%] | yes |
| q70 | change-484/default | -12.6% [-23%, -8%] | yes |
| q41 | change-484/default | -12.0% [-24%, -3%] | yes |
| q69 | change-484/default | -11.4% [-19%, -1%] | yes |
| q59 | change-484/default | -11.2% [-26%, -5%] | yes |
| q20 | change-484/default | -11.1% [-21%, -0%] | yes |
| q15 | change-484/default | -10.7% [-14%, -2%] | yes |
| q11 | change-484/default | -9.7% [-19%, -2%] | yes |
| q48 | change-484/default | -9.5% [-20%, -4%] | yes |
| q86 | change-484/default | -9.1% [-16%, -2%] |  |
| q13 | change-484/default | -8.3% [-15%, -5%] | yes |
| q68 | change-484/default | -8.3% [-13%, -5%] | yes |
| q31 | change-484/default | -7.3% [-14%, -3%] | yes |
| q09 | change-484/default | -6.7% [-15%, -0%] |  |
| q83 | change-484/default | -6.5% [-23%, -0%] | yes |

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
