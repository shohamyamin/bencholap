## bencholap: 474 vs 484

ClickBench (derived) SF10, layout `unpartitioned, small-row-groups, sorted, date-partitioned, bloom-filters`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-474/default/unpartitioned (474) | `474` | 36.17 s | baseline | 89.05 s | 43 | 0 | 0 | 0 |
| baseline-474/default/small-row-groups (474) | `474` | 46.98 s | +64.8% | 112.89 s | 43 | 0 | 0 | 0 |
| baseline-474/default/sorted (474) | `474` | 45.90 s | +55.2% | 110.28 s | 43 | 0 | 0 | 0 |
| baseline-474/default/date-partitioned (474) | `474` | 35.97 s | -4.1% | 85.93 s | 43 | 0 | 0 | 0 |
| baseline-474/default/bloom-filters (474) | `474` | 48.79 s | +69.6% | 114.62 s | 43 | 0 | 0 | 0 |
| change-484/default/unpartitioned (484) | `484` | 34.06 s | -2.5% | 83.86 s | 43 | 0 | 0 | 0 |
| change-484/default/small-row-groups (484) | `484` | 46.11 s | +61.1% | 108.63 s | 43 | 0 | 0 | 0 |
| change-484/default/sorted (484) | `484` | 44.24 s | +49.5% | 105.34 s | 43 | 0 | 0 | 0 |
| change-484/default/date-partitioned (484) | `484` | 33.66 s | -10.8% | 79.79 s | 43 | 0 | 0 | 0 |
| change-484/default/bloom-filters (484) | `484` | 46.41 s | +62.4% | 108.43 s | 43 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q03 | baseline-474/default/sorted | +229.6% [+188%, +259%] | yes |
| q03 | change-484/default/sorted | +231.3% [+194%, +245%] | yes |
| q06 | change-484/default/sorted | +234.0% [+223%, +314%] | yes |
| q06 | change-484/default/small-row-groups | +240.9% [+222%, +272%] | yes |
| q06 | baseline-474/default/sorted | +241.1% [+232%, +304%] | yes |
| q01 | change-484/default/small-row-groups | +250.6% [+238%, +316%] | yes |
| q06 | baseline-474/default/small-row-groups | +251.8% [+223%, +297%] | yes |
| q06 | baseline-474/default/bloom-filters | +262.4% [+248%, +292%] | yes |
| q19 | change-484/default/small-row-groups | +267.4% [+197%, +419%] | yes |
| q01 | change-484/default/sorted | +282.4% [+247%, +333%] | yes |
| q01 | baseline-474/default/sorted | +282.8% [+260%, +360%] | yes |
| q06 | change-484/default/bloom-filters | +285.5% [+264%, +310%] | yes |
| q01 | change-484/default/bloom-filters | +287.9% [+258%, +344%] | yes |
| q01 | baseline-474/default/small-row-groups | +289.8% [+253%, +374%] | yes |
| q01 | baseline-474/default/bloom-filters | +292.0% [+272%, +339%] | yes |

247 significant changes in total (41 faster, 206 slower); the 15 largest are listed, all are in the report.

**Result sets differ between configurations:** q03, q17, q18, q21, q22, q24, q30, q31, q32, q38, q39, q40

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-474/default/unpartitioned | baseline-474/default/small-row-groups | baseline-474/default/sorted | baseline-474/default/date-partitioned | baseline-474/default/bloom-filters | change-484/default/unpartitioned | change-484/default/small-row-groups | change-484/default/sorted | change-484/default/date-partitioned | change-484/default/bloom-filters |
|---|---|---|---|---|---|---|---|---|---|---|
| `catalog / iceberg / fs.native-s3.enabled` | true | true | true | true | true | – | – | – | – | – |
| `catalog / iceberg / fs.s3.enabled` | – | – | – | – | – | true | true | true | true | true |
| `config.properties / cache-manager.config-files` | – | – | – | – | – | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties | etc/cache-manager-memory.properties |
| `config.properties / http-server.http.port` | 8080 | 8080 | 8080 | 8080 | 8080 | – | – | – | – | – |
| `jvm.config / -Dfile.encoding` | UTF-8 | UTF-8 | UTF-8 | UTF-8 | UTF-8 | – | – | – | – | – |
| `jvm.config / -XX:+EnableDynamicAgentLoading` | set | set | set | set | set | – | – | – | – | – |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
