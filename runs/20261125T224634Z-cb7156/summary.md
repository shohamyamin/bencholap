## bencholap: Trino releases every 10: 414..484

TPC-H (derived) SF1, layout `unpartitioned`, 2 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-414/default (414) | `414` | 17.82 s | baseline | 19.40 s | 22 | 0 | 0 | 22 |
| change-424/default (424) | `424` | 17.44 s | -1.2% | 19.60 s | 22 | 0 | 0 | 22 |
| target2-434/default (434) | `434` | 16.17 s | -9.3% | 18.57 s | 22 | 0 | 0 | 22 |
| target3-444/default (444) | `444` | 16.59 s | -10.3% | 19.44 s | 21 | 1 | 0 | 21 |
| target4-454/default (454) | `454` | 15.89 s | -13.6% | 18.31 s | 21 | 1 | 0 | 21 |
| target5-464/default (464) | `464` | 14.34 s | -21.4% | 16.22 s | 22 | 0 | 0 | 22 |
| target6-474/default (474) | `474` | 13.51 s | -26.7% | 13.19 s | 22 | 0 | 0 | 22 |
| target7-484/default (484) | `484` | 13.14 s | -28.7% | 12.45 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q20 | target7-484/default | -53.6% [-57%, -50%] | yes |
| q20 | target6-474/default | -52.0% [-59%, -44%] | yes |
| q19 | target6-474/default | -47.8% [-52%, -43%] | yes |
| q19 | target7-484/default | -45.7% [-47%, -44%] | yes |
| q19 | target5-464/default | -44.0% [-51%, -36%] | yes |
| q17 | target7-484/default | -42.8% [-49%, -36%] | yes |
| q11 | target7-484/default | -42.1% [-47%, -36%] | yes |
| q12 | target7-484/default | -41.3% [-48%, -35%] | yes |
| q11 | target6-474/default | -40.1% [-51%, -28%] | yes |
| q06 | target6-474/default | -39.9% [-44%, -35%] | yes |
| q07 | target7-484/default | -37.7% [-42%, -33%] | yes |
| q08 | target7-484/default | -37.6% [-41%, -35%] | yes |
| q02 | target6-474/default | -36.3% [-46%, -25%] | yes |
| q07 | target6-474/default | -36.0% [-51%, -19%] | yes |
| q12 | target6-474/default | -35.7% [-46%, -25%] | yes |
| q11 | target5-464/default | -35.5% [-44%, -25%] | yes |
| q19 | target4-454/default | -35.2% [-39%, -31%] | yes |
| q02 | target5-464/default | -35.1% [-41%, -28%] | yes |
| q17 | target6-474/default | -34.9% [-43%, -26%] | yes |
| q11 | target4-454/default | -33.8% [-45%, -20%] | yes |
| q01 | target7-484/default | -33.7% [-41%, -25%] | yes |
| q11 | target3-444/default | -33.0% [-41%, -23%] | yes |
| q14 | target5-464/default | -31.3% [-33%, -29%] | yes |
| q06 | target5-464/default | -31.0% [-35%, -26%] | yes |
| q06 | target7-484/default | -30.9% [-38%, -24%] | yes |
| q05 | target5-464/default | -29.9% [-32%, -28%] | yes |
| q09 | target5-464/default | -28.5% [-36%, -19%] | yes |
| q17 | target5-464/default | -28.4% [-35%, -21%] | yes |
| q02 | target2-434/default | -28.0% [-36%, -18%] | yes |
| q22 | target7-484/default | -27.9% [-29%, -27%] | yes |
| q18 | target7-484/default | -27.5% [-34%, -21%] | yes |
| q12 | target5-464/default | -27.2% [-32%, -22%] | yes |
| q01 | target5-464/default | -26.8% [-35%, -18%] | yes |
| q09 | target6-474/default | -26.7% [-36%, -16%] | yes |
| q05 | target6-474/default | -26.6% [-32%, -21%] | yes |
| q12 | target4-454/default | -26.4% [-38%, -15%] | yes |
| q06 | target4-454/default | -25.9% [-33%, -18%] | yes |
| q15 | target7-484/default | -25.5% [-32%, -19%] | yes |
| q16 | target7-484/default | -25.2% [-29%, -21%] | yes |
| q08 | target5-464/default | -25.2% [-31%, -20%] | yes |
| q02 | target7-484/default | -25.1% [-35%, -14%] | yes |
| q05 | target7-484/default | -25.0% [-25%, -25%] | yes |
| q14 | target2-434/default | -24.5% [-31%, -18%] | yes |
| q19 | target2-434/default | -24.3% [-27%, -21%] | yes |
| q13 | target7-484/default | -24.3% [-25%, -23%] | yes |
| q13 | target6-474/default | -23.9% [-28%, -20%] | yes |
| q10 | target6-474/default | -23.1% [-33%, -13%] | yes |
| q13 | target5-464/default | -22.9% [-28%, -18%] | yes |
| q01 | target6-474/default | -22.4% [-30%, -13%] | yes |
| q15 | target6-474/default | -21.6% [-25%, -18%] | yes |
| q15 | target3-444/default | -21.5% [-28%, -15%] | yes |
| q02 | change-424/default | -21.2% [-33%, -7%] |  |
| q16 | target5-464/default | -20.8% [-31%, -9%] | yes |
| q22 | target3-444/default | -20.5% [-22%, -19%] | yes |
| q07 | target2-434/default | -20.3% [-26%, -14%] | yes |
| q09 | target4-454/default | -20.3% [-30%, -8%] | yes |
| q13 | target3-444/default | -20.2% [-22%, -19%] | yes |
| q07 | target5-464/default | -19.9% [-27%, -12%] | yes |
| q17 | target4-454/default | -19.9% [-26%, -13%] | yes |
| q16 | target3-444/default | -19.2% [-28%, -10%] | yes |
| q14 | target4-454/default | -19.0% [-23%, -15%] | yes |
| q22 | target5-464/default | -18.9% [-23%, -15%] | yes |
| q15 | target4-454/default | -18.8% [-27%, -10%] | yes |
| q11 | change-424/default | -18.7% [-30%, -5%] |  |
| q15 | target5-464/default | -18.5% [-30%, -6%] | yes |
| q21 | target7-484/default | -18.4% [-27%, -10%] | yes |
| q03 | target5-464/default | -18.3% [-28%, -7%] | yes |
| q19 | target3-444/default | -18.2% [-24%, -12%] | yes |
| q18 | target6-474/default | -18.1% [-23%, -13%] | yes |
| q16 | target6-474/default | -18.0% [-26%, -9%] | yes |
| q07 | target3-444/default | -18.0% [-24%, -11%] | yes |
| q10 | target2-434/default | -17.9% [-21%, -14%] | yes |
| q22 | target6-474/default | -17.9% [-25%, -10%] | yes |
| q12 | target3-444/default | -17.7% [-22%, -13%] | yes |
| q05 | target4-454/default | -17.6% [-22%, -13%] | yes |
| q14 | target6-474/default | -17.4% [-23%, -11%] | yes |
| q10 | target7-484/default | -17.0% [-25%, -9%] | yes |
| q17 | target3-444/default | -16.9% [-26%, -6%] | yes |
| q13 | target2-434/default | -16.3% [-19%, -14%] | yes |
| q07 | target4-454/default | -15.9% [-22%, -10%] | yes |
| q13 | target4-454/default | -15.8% [-18%, -14%] | yes |
| q13 | change-424/default | -15.5% [-18%, -13%] |  |
| q03 | target2-434/default | -15.4% [-21%, -10%] | yes |
| q05 | target3-444/default | -14.7% [-19%, -11%] | yes |
| q17 | target2-434/default | -14.5% [-19%, -9%] | yes |
| q14 | target3-444/default | -13.5% [-16%, -11%] | yes |
| q14 | change-424/default | -13.4% [-17%, -9%] |  |
| q04 | target7-484/default | -12.4% [-23%, -1%] | yes |
| q08 | target6-474/default | -11.0% [-21%, -1%] | yes |
| q18 | target2-434/default | -10.3% [-14%, -6%] | yes |
| q15 | target2-434/default | -9.8% [-18%, -1%] | yes |
| q14 | target7-484/default | -9.6% [-14%, -5%] | yes |
| q22 | target2-434/default | -9.0% [-14%, -4%] | yes |
| q19 | change-424/default | -8.6% [-11%, -6%] |  |
| q18 | target3-444/default | -7.9% [-12%, -3%] | yes |
| q21 | target6-474/default | -6.2% [-9%, -3%] | yes |
| q21 | target3-444/default | +10.6% [+6%, +16%] | yes |
| q04 | target2-434/default | +12.4% [+5%, +20%] | yes |
| q22 | change-424/default | +12.9% [+1%, +25%] |  |
| q08 | target3-444/default | +14.2% [+11%, +18%] | yes |
| q04 | target4-454/default | +17.3% [+2%, +34%] | yes |
| q20 | target5-464/default | +18.8% [+0%, +40%] | yes |
| q10 | target4-454/default | +20.2% [+16%, +25%] | yes |
| q06 | target2-434/default | +20.8% [+9%, +34%] |  |
| q04 | change-424/default | +30.9% [+26%, +36%] |  |

**Failures:**

- q01 on target3-444/default: error TrinoQueryError(type=INTERNAL_ERROR, name=NO_NODES_AVAILABLE, message="No nodes available to run query", query_id=20261125_225342_00006_6xu2s)
- q01 on target4-454/default: error TrinoQueryError(type=INTERNAL_ERROR, name=NO_NODES_AVAILABLE, message="No nodes available to run query", query_id=20261125_225458_00006_938vr)

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-414/default | change-424/default | target2-434/default | target3-444/default | target4-454/default | target5-464/default | target6-474/default | target7-484/default |
|---|---|---|---|---|---|---|---|---|
| `catalog / iceberg / fs.native-s3.enabled` | – | – | – | true | true | true | true | – |
| `catalog / iceberg / fs.s3.enabled` | – | – | – | – | – | – | – | true |
| `catalog / iceberg / hive.s3.aws-access-key` | *** | *** | *** | – | – | – | – | – |
| `catalog / iceberg / hive.s3.aws-secret-key` | *** | *** | *** | – | – | – | – | – |
| `catalog / iceberg / hive.s3.endpoint` | http://storage:8333 | http://storage:8333 | http://storage:8333 | – | – | – | – | – |
| `catalog / iceberg / hive.s3.path-style-access` | true | true | true | – | – | – | – | – |
| `catalog / iceberg / hive.s3.ssl.enabled` | false | false | false | – | – | – | – | – |
| `catalog / iceberg / s3.aws-access-key` | – | – | – | *** | *** | *** | *** | *** |
| `catalog / iceberg / s3.aws-secret-key` | – | – | – | *** | *** | *** | *** | *** |
| `catalog / iceberg / s3.endpoint` | – | – | – | http://storage:8333 | http://storage:8333 | http://storage:8333 | http://storage:8333 | http://storage:8333 |
| `catalog / iceberg / s3.path-style-access` | – | – | – | true | true | true | true | true |
| `catalog / iceberg / s3.region` | – | – | – | us-east-1 | us-east-1 | us-east-1 | us-east-1 | us-east-1 |
| `config.properties / cache-manager.config-files` | – | – | – | – | – | – | – | etc/cache-manager-memory.properties |
| `config.properties / catalog.management` | – | – | – | ${ENV:CATALOG_MANAGEMENT} | ${ENV:CATALOG_MANAGEMENT} | ${ENV:CATALOG_MANAGEMENT} | ${ENV:CATALOG_MANAGEMENT} | ${ENV:CATALOG_MANAGEMENT} |
| `config.properties / http-server.http.port` | 8080 | 8080 | 8080 | 8080 | 8080 | 8080 | 8080 | – |
| `jvm.config / -Dfile.encoding` | – | – | – | – | – | – | UTF-8 | – |
| `jvm.config / -Djava.security.manager` | – | – | – | – | – | allow | – | – |
| `jvm.config / -XX:+EnableDynamicAgentLoading` | – | – | – | set | set | set | set | – |
| `jvm.config / -XX:+UnlockDiagnosticVMOptions` | set | set | set | set | – | – | – | – |
| `jvm.config / -XX:+UseAESCTRIntrinsics` | set | set | – | – | – | – | – | – |
| `jvm.config / -XX:-G1UsePreventiveGC` | set | set | – | – | – | – | – | – |
| `jvm.config / -XX:GCLockerRetryAllocationCount` | – | – | 32 | 32 | – | – | – | – |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
