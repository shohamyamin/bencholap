## bencholap: 483 vs 484

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (1 warmup, 2 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 48.71 s | baseline | 49.12 s | 90 | 0 | 9 | 89 |
| change-484/default (484) | `484` | 44.13 s | -13.3% | 49.42 s | 90 | 0 | 9 | 89 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q72 | change-484/default | -44.2% [-49%, -41%] | yes |
| q29 | change-484/default | -39.7% [-43%, -37%] | yes |
| q25 | change-484/default | -38.5% [-42%, -34%] | yes |
| q85 | change-484/default | -33.9% [-41%, -24%] | yes |
| q91 | change-484/default | -33.6% [-38%, -23%] | yes |
| q17 | change-484/default | -31.9% [-36%, -26%] | yes |
| q55 | change-484/default | -30.8% [-41%, -13%] | yes |
| q71 | change-484/default | -26.7% [-34%, -13%] | yes |
| q98 | change-484/default | -26.4% [-37%, -13%] | yes |
| q20 | change-484/default | -26.3% [-34%, -14%] | yes |
| q19 | change-484/default | -26.0% [-36%, -20%] | yes |
| q06 | change-484/default | -25.3% [-32%, -10%] | yes |
| q61 | change-484/default | -24.0% [-29%, -16%] | yes |
| q69 | change-484/default | -22.9% [-34%, -8%] | yes |
| q95 | change-484/default | -21.8% [-35%, -7%] | yes |
| q66 | change-484/default | -21.2% [-29%, -6%] | yes |
| q52 | change-484/default | -21.1% [-32%, -9%] | yes |
| q94 | change-484/default | -20.5% [-29%, -10%] | yes |
| q65 | change-484/default | -20.2% [-29%, -6%] | yes |
| q41 | change-484/default | -19.6% [-28%, -6%] | yes |
| q18 | change-484/default | -19.5% [-30%, -15%] | yes |
| q50 | change-484/default | -18.9% [-28%, -13%] | yes |
| q24 | change-484/default | -18.4% [-25%, -15%] | yes |
| q58 | change-484/default | -17.4% [-28%, -3%] | yes |
| q68 | change-484/default | -17.3% [-21%, -12%] | yes |
| q60 | change-484/default | -17.3% [-29%, -6%] | yes |
| q10 | change-484/default | -17.1% [-25%, -11%] | yes |
| q27 | change-484/default | -16.6% [-25%, -11%] | yes |
| q37 | change-484/default | -15.8% [-20%, -11%] |  |
| q12 | change-484/default | -15.4% [-33%, -8%] | yes |
| q54 | change-484/default | -15.0% [-25%, -11%] | yes |
| q59 | change-484/default | -14.2% [-25%, -1%] | yes |
| q62 | change-484/default | -13.1% [-29%, -5%] | yes |
| q33 | change-484/default | -12.9% [-24%, -3%] | yes |
| q05 | change-484/default | -12.7% [-31%, -6%] | yes |
| q02 | change-484/default | -12.5% [-25%, -7%] | yes |
| q26 | change-484/default | -12.1% [-20%, -4%] | yes |
| q80 | change-484/default | -12.1% [-18%, -7%] | yes |
| q31 | change-484/default | -12.0% [-16%, -8%] | yes |
| q30 | change-484/default | -11.8% [-22%, -2%] | yes |
| q07 | change-484/default | -11.6% [-25%, -1%] | yes |
| q57 | change-484/default | -9.7% [-16%, -3%] | yes |
| q53 | change-484/default | -9.6% [-16%, -3%] | yes |
| q39 | change-484/default | -9.3% [-13%, -5%] | yes |
| q48 | change-484/default | -9.1% [-17%, -2%] | yes |
| q15 | change-484/default | -8.7% [-14%, -1%] | yes |
| q35 | change-484/default | -8.5% [-14%, -2%] | yes |
| q13 | change-484/default | -8.3% [-12%, -3%] | yes |
| q46 | change-484/default | -7.9% [-14%, -3%] | yes |
| q09 | change-484/default | -7.8% [-12%, -1%] |  |
| q11 | change-484/default | -7.6% [-11%, -0%] | yes |

**Failures:**

- q21 on baseline-483/default: wrong_result 
- q21 on change-484/default: wrong_result 
- q34 on baseline-483/default: wrong_result 
- q34 on change-484/default: wrong_result 
- q45 on baseline-483/default: wrong_result 
- q45 on change-484/default: wrong_result 
- q64 on baseline-483/default: wrong_result 
- q64 on change-484/default: wrong_result 
- q73 on baseline-483/default: wrong_result 
- q73 on change-484/default: wrong_result 
- q78 on baseline-483/default: wrong_result 
- q78 on change-484/default: wrong_result 
- q83 on baseline-483/default: wrong_result 
- q83 on change-484/default: wrong_result 
- q84 on baseline-483/default: wrong_result 
- q84 on change-484/default: wrong_result 
- q93 on baseline-483/default: wrong_result 
- q93 on change-484/default: wrong_result 

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
