## bencholap: 474 vs 484

TPC-H (derived) SF1, layout `unpartitioned, date-sorted, date-partitioned, key-bloom-filters`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x AMD EPYC 9V45 96-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-474/default/unpartitioned (474) | `474` | 9.46 s | baseline | 9.14 s | 22 | 0 | 0 | 22 |
| baseline-474/default/date-sorted (474) | `474` | 9.34 s | -1.5% | 9.18 s | 22 | 0 | 0 | 22 |
| baseline-474/default/date-partitioned (474) | `474` | 9.63 s | -4.2% | 10.46 s | 22 | 0 | 0 | 22 |
| baseline-474/default/key-bloom-filters (474) | `474` | 9.58 s | +2.6% | 9.46 s | 22 | 0 | 0 | 22 |
| change-484/default/unpartitioned (484) | `484` | 9.26 s | -1.2% | 8.91 s | 22 | 0 | 0 | 22 |
| change-484/default/date-sorted (484) | `484` | 9.32 s | -3.1% | 8.71 s | 22 | 0 | 0 | 22 |
| change-484/default/date-partitioned (484) | `484` | 9.40 s | -4.9% | 10.51 s | 22 | 0 | 0 | 22 |
| change-484/default/key-bloom-filters (484) | `484` | 9.24 s | -1.3% | 9.31 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q06 | baseline-474/default/date-partitioned | -53.3% [-63%, -46%] | yes |
| q15 | baseline-474/default/date-partitioned | -50.2% [-68%, -46%] | yes |
| q15 | change-484/default/date-partitioned | -47.4% [-56%, -41%] | yes |
| q14 | change-484/default/date-partitioned | -39.0% [-39%, -18%] | yes |
| q06 | change-484/default/date-partitioned | -34.5% [-59%, -8%] | yes |
| q07 | change-484/default/date-partitioned | -34.0% [-46%, -10%] | yes |
| q08 | change-484/default/key-bloom-filters | -33.1% [-43%, -3%] | yes |
| q07 | baseline-474/default/date-partitioned | -31.8% [-41%, -13%] | yes |
| q21 | change-484/default/date-partitioned | +30.9% [+1%, +49%] | yes |
| q09 | change-484/default/unpartitioned | +31.7% [+11%, +48%] | yes |
| q09 | baseline-474/default/key-bloom-filters | +32.9% [+2%, +44%] | yes |
| q09 | change-484/default/date-partitioned | +33.3% [+11%, +44%] | yes |
| q21 | baseline-474/default/date-partitioned | +38.8% [+12%, +58%] | yes |
| q18 | baseline-474/default/date-partitioned | +51.0% [+18%, +73%] | yes |
| q22 | baseline-474/default/date-partitioned | +60.9% [+11%, +137%] | yes |

37 significant changes in total (22 faster, 15 slower); the 15 largest are listed, all are in the report.

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-474/default/unpartitioned | baseline-474/default/date-sorted | baseline-474/default/date-partitioned | baseline-474/default/key-bloom-filters | change-484/default/unpartitioned | change-484/default/date-sorted | change-484/default/date-partitioned | change-484/default/key-bloom-filters |
|---|---|---|---|---|---|---|---|---|
| `catalog / iceberg / fs.native-s3.enabled` | true | true | true | true | – | – | – | – |
| `catalog / iceberg / fs.s3.enabled` | – | – | – | – | true | true | true | true |
| `config.properties / cache-manager.config-files` | – | – | – | – | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties |
| `config.properties / http-server.http.port` | 8080 | 8080 | 8080 | 8080 | – | – | – | – |
| `jvm.config / -Dfile.encoding` | UTF-8 | UTF-8 | UTF-8 | UTF-8 | – | – | – | – |
| `jvm.config / -XX:+EnableDynamicAgentLoading` | set | set | set | set | – | – | – | – |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
