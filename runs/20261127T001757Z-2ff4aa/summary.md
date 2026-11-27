## bencholap: 474 vs 484

TPC-H (derived) SF1, layout `unpartitioned, date-sorted, date-partitioned, key-bloom-filters`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x INTEL(R) XEON(R) PLATINUM 8573C, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-474/default/unpartitioned (474) | `474` | 14.86 s | baseline | 15.75 s | 22 | 0 | 0 | 22 |
| baseline-474/default/date-sorted (474) | `474` | 17.39 s | +11.8% | 20.55 s | 22 | 0 | 0 | 22 |
| baseline-474/default/date-partitioned (474) | `474` | 14.95 s | -6.9% | 18.04 s | 22 | 0 | 0 | 22 |
| baseline-474/default/key-bloom-filters (474) | `474` | 20.17 s | +36.4% | 25.48 s | 22 | 0 | 0 | 22 |
| change-484/default/unpartitioned (484) | `484` | 14.26 s | -4.6% | 14.96 s | 22 | 0 | 0 | 22 |
| change-484/default/date-sorted (484) | `484` | 16.87 s | +8.9% | 20.03 s | 22 | 0 | 0 | 22 |
| change-484/default/date-partitioned (484) | `484` | 14.51 s | -9.9% | 17.29 s | 22 | 0 | 0 | 22 |
| change-484/default/key-bloom-filters (484) | `484` | 19.13 s | +29.7% | 24.32 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q06 | baseline-474/default/date-partitioned | -59.9% [-68%, -47%] | yes |
| q15 | change-484/default/date-partitioned | -59.0% [-63%, -53%] | yes |
| q14 | baseline-474/default/key-bloom-filters | +58.3% [+25%, +68%] | yes |
| q15 | baseline-474/default/key-bloom-filters | +67.3% [+54%, +83%] | yes |
| q20 | baseline-474/default/key-bloom-filters | +70.7% [+43%, +103%] | yes |
| q17 | baseline-474/default/date-partitioned | +73.1% [+37%, +84%] | yes |
| q15 | change-484/default/key-bloom-filters | +79.9% [+57%, +92%] | yes |
| q12 | baseline-474/default/key-bloom-filters | +81.7% [+32%, +94%] | yes |
| q12 | change-484/default/key-bloom-filters | +91.1% [+38%, +97%] | yes |
| q17 | change-484/default/key-bloom-filters | +100.8% [+70%, +132%] | yes |
| q17 | change-484/default/date-sorted | +110.4% [+72%, +156%] | yes |
| q06 | baseline-474/default/key-bloom-filters | +115.9% [+88%, +122%] | yes |
| q06 | change-484/default/key-bloom-filters | +118.8% [+95%, +151%] | yes |
| q17 | baseline-474/default/key-bloom-filters | +122.7% [+80%, +142%] | yes |
| q17 | baseline-474/default/date-sorted | +128.1% [+90%, +171%] | yes |

73 significant changes in total (26 faster, 47 slower); the 15 largest are listed, all are in the report.

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
