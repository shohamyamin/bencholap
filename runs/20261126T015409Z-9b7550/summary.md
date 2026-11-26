## bencholap: Benchmark: auto-close check (TPC-H q01,q06)

TPC-H (derived) SF1, layout `unpartitioned`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-483/default (483) | `483` | 975 ms | baseline | 1.23 s | 2 | 0 | 0 | 2 |
| change-484/default (484) | `484` | 985 ms | +2.2% | 1.27 s | 2 | 0 | 0 | 2 |

No significant per-query timing changes.

<details><summary>Settings that differ between configurations</summary>

| setting | baseline-483/default | change-484/default |
|---|---|---|
| `config.properties / cache-manager.config-files` | – | etc/cache-manager-memory.properties |

</details>

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
