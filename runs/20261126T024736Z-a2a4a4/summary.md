## bencholap: Benchmark: test 476 against 484

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (1 warmup, 2 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-476/default (476) | `476` | 51.23 s | baseline | 50.86 s | 92 | 0 | 7 | 90 |
| change-484/default (484) | `484` | 44.97 s | -11.3% | 51.79 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q64 | change-484/default | -50.6% [-53%, -47%] | yes |
| q72 | change-484/default | -44.7% [-49%, -38%] | yes |
| q99 | change-484/default | -33.7% [-40%, -15%] | yes |
| q81 | change-484/default | -32.9% [-44%, -11%] | yes |
| q85 | change-484/default | -31.8% [-46%, -20%] | yes |
| q29 | change-484/default | -30.7% [-35%, -23%] | yes |
| q25 | change-484/default | -30.4% [-36%, -17%] | yes |
| q94 | change-484/default | -29.2% [-36%, -16%] | yes |
| q91 | change-484/default | -27.8% [-43%, -11%] | yes |
| q17 | change-484/default | -26.7% [-32%, -17%] | yes |
| q69 | change-484/default | -25.5% [-35%, -9%] | yes |
| q95 | change-484/default | -22.0% [-32%, -11%] | yes |
| q19 | change-484/default | -21.4% [-28%, -16%] | yes |
| q68 | change-484/default | -20.8% [-24%, -15%] | yes |
| q28 | change-484/default | +23.4% [+0%, +38%] | yes |

38 significant changes in total (37 faster, 1 slower); the 15 largest are listed, all are in the report.

**Failures:**

- q11 on baseline-476/default: wrong_result 
- q21 on baseline-476/default: wrong_result 
- q31 on baseline-476/default: wrong_result 
- q36 on baseline-476/default: wrong_result 
- q53 on baseline-476/default: wrong_result 
- q58 on baseline-476/default: wrong_result 
- q83 on baseline-476/default: wrong_result 

**Result sets differ between configurations:** q66

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-476/default | change-484/default |
|---|---|---|
| `catalog / iceberg / fs.native-s3.enabled` | true | – |
| `catalog / iceberg / fs.s3.enabled` | – | true |
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |
| `config.properties / http-server.http.port` | 8080 | – |
| `jvm.config / -Dfile.encoding` | UTF-8 | – |
| `jvm.config / -XX:+EnableDynamicAgentLoading` | set | – |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
