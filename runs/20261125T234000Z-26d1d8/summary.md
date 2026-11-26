## bencholap: 483 vs 484

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (1 warmup, 2 round(s)). Machine: gh-standard: 4x INTEL(R) XEON(R) PLATINUM 8573C, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 62.90 s | baseline | 65.79 s | 96 | 0 | 3 | 94 |
| change-484/default (484) | `484` | 55.05 s | -12.9% | 65.01 s | 96 | 0 | 3 | 94 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q64 | change-484/default | -51.8% [-54%, -48%] | yes |
| q72 | change-484/default | -47.7% [-55%, -43%] | yes |
| q29 | change-484/default | -44.0% [-46%, -41%] | yes |
| q91 | change-484/default | -40.5% [-43%, -35%] | yes |
| q85 | change-484/default | -39.0% [-44%, -34%] | yes |
| q25 | change-484/default | -37.0% [-44%, -33%] | yes |
| q17 | change-484/default | -29.8% [-39%, -27%] | yes |
| q19 | change-484/default | -28.8% [-33%, -17%] | yes |
| q84 | change-484/default | -26.1% [-35%, -23%] | yes |
| q41 | change-484/default | -24.8% [-34%, -3%] | yes |
| q95 | change-484/default | -24.4% [-29%, -21%] | yes |
| q90 | change-484/default | -23.7% [-39%, -4%] | yes |
| q40 | change-484/default | -23.3% [-28%, -13%] | yes |
| q71 | change-484/default | -22.9% [-30%, -13%] | yes |
| q06 | change-484/default | -21.5% [-28%, -18%] | yes |
| q99 | change-484/default | -21.4% [-30%, -10%] | yes |
| q27 | change-484/default | -20.8% [-25%, -12%] | yes |
| q61 | change-484/default | -20.8% [-28%, -12%] | yes |
| q43 | change-484/default | -19.4% [-29%, -5%] | yes |
| q37 | change-484/default | -18.7% [-23%, -12%] |  |
| q52 | change-484/default | -17.3% [-25%, -7%] | yes |
| q18 | change-484/default | -17.3% [-24%, -14%] | yes |
| q83 | change-484/default | -16.9% [-30%, -11%] | yes |
| q93 | change-484/default | -16.2% [-30%, -7%] | yes |
| q54 | change-484/default | -16.1% [-25%, -12%] | yes |
| q82 | change-484/default | -15.9% [-25%, -10%] |  |
| q63 | change-484/default | -15.2% [-24%, -4%] | yes |
| q68 | change-484/default | -14.9% [-18%, -9%] | yes |
| q59 | change-484/default | -14.5% [-21%, -4%] | yes |
| q07 | change-484/default | -13.9% [-21%, -3%] | yes |
| q58 | change-484/default | -13.7% [-24%, -5%] | yes |
| q80 | change-484/default | -13.4% [-18%, -8%] | yes |
| q12 | change-484/default | -12.9% [-20%, -4%] | yes |
| q26 | change-484/default | -12.4% [-18%, -4%] | yes |
| q15 | change-484/default | -11.5% [-18%, -4%] | yes |
| q03 | change-484/default | -10.9% [-22%, -2%] | yes |
| q39 | change-484/default | -10.3% [-20%, -8%] | yes |
| q48 | change-484/default | -10.1% [-13%, -4%] | yes |
| q45 | change-484/default | -9.9% [-19%, -4%] | yes |
| q31 | change-484/default | -9.4% [-15%, -0%] | yes |
| q35 | change-484/default | -8.9% [-16%, -1%] | yes |
| q57 | change-484/default | -8.3% [-12%, -3%] | yes |
| q13 | change-484/default | -5.6% [-16%, -0%] | yes |
| q77 | change-484/default | +14.7% [+1%, +21%] | yes |

**Failures:**

- q24 on baseline-483/default: wrong_result 
- q24 on change-484/default: wrong_result 
- q34 on baseline-483/default: wrong_result 
- q34 on change-484/default: wrong_result 
- q73 on baseline-483/default: wrong_result 
- q73 on change-484/default: wrong_result 

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
