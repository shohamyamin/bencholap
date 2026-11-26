## bencholap: 474 vs 484

ClickBench (derived) SF1, layout `unpartitioned, sorted, date-partitioned, bloom-filters`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-474/default/unpartitioned (474) | `474` | 8.40 s | baseline | 9.37 s | 43 | 0 | 0 | 0 |
| baseline-474/default/sorted (474) | `474` | 8.37 s | +0.1% | 9.32 s | 43 | 0 | 0 | 0 |
| baseline-474/default/date-partitioned (474) | `474` | 8.48 s | -1.1% | 8.85 s | 43 | 0 | 0 | 0 |
| baseline-474/default/bloom-filters (474) | `474` | 8.13 s | -1.9% | 9.24 s | 43 | 0 | 0 | 0 |
| change-484/default/unpartitioned (484) | `484` | 8.14 s | -2.2% | 8.54 s | 43 | 0 | 0 | 0 |
| change-484/default/sorted (484) | `484` | 8.13 s | -2.9% | 8.42 s | 43 | 0 | 0 | 0 |
| change-484/default/date-partitioned (484) | `484` | 8.15 s | -2.5% | 8.14 s | 43 | 0 | 0 | 0 |
| change-484/default/bloom-filters (484) | `484` | 8.05 s | -4.4% | 8.55 s | 43 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q17 | change-484/default/bloom-filters | -35.1% [-37%, -4%] | yes |
| q17 | change-484/default/date-partitioned | -31.9% [-33%, -0%] | yes |
| q13 | baseline-474/default/sorted | -30.1% [-34%, -19%] | yes |
| q34 | change-484/default/sorted | -30.1% [-35%, -10%] | yes |
| q03 | change-484/default/date-partitioned | -27.7% [-36%, -15%] | yes |
| q03 | change-484/default/bloom-filters | -27.1% [-34%, -13%] | yes |
| q34 | change-484/default/date-partitioned | -26.8% [-31%, -20%] | yes |
| q17 | change-484/default/unpartitioned | -26.6% [-31%, -13%] | yes |
| q03 | baseline-474/default/bloom-filters | -25.6% [-33%, -8%] | yes |
| q04 | change-484/default/unpartitioned | -25.0% [-39%, -4%] |  |
| q22 | change-484/default/date-partitioned | +32.3% [+0%, +52%] | yes |
| q33 | baseline-474/default/date-partitioned | +32.7% [+13%, +61%] | yes |
| q20 | change-484/default/bloom-filters | +44.7% [+24%, +81%] | yes |
| q20 | change-484/default/date-partitioned | +47.8% [+35%, +107%] | yes |
| q19 | change-484/default/date-partitioned | +74.8% [+24%, +94%] | yes |

62 significant changes in total (43 faster, 19 slower); the 15 largest are listed, all are in the report.

**Result sets differ between configurations:** q03, q10, q11, q17, q18, q22, q23, q24, q30, q31, q32, q35, q38, q39, q40

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-474/default/unpartitioned | baseline-474/default/sorted | baseline-474/default/date-partitioned | baseline-474/default/bloom-filters | change-484/default/unpartitioned | change-484/default/sorted | change-484/default/date-partitioned | change-484/default/bloom-filters |
|---|---|---|---|---|---|---|---|---|
| `catalog / iceberg / fs.native-s3.enabled` | true | true | true | true | – | – | – | – |
| `catalog / iceberg / fs.s3.enabled` | – | – | – | – | true | true | true | true |
| `config.properties / cache-manager.config-files` | – | – | – | – | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties |
| `config.properties / http-server.http.port` | 8080 | 8080 | 8080 | 8080 | – | – | – | – |
| `jvm.config / -Dfile.encoding` | UTF-8 | UTF-8 | UTF-8 | UTF-8 | – | – | – | – |
| `jvm.config / -XX:+EnableDynamicAgentLoading` | set | set | set | set | – | – | – | – |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
