## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@9daf6b668763df97cd9c5a2df93cf17958b2adc6 vs github:shohamyamin/trino@3915e3120945449704ff4e340005839bb3311f1f

TPC-H (derived) SF1, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 9.72 s | baseline | 11.25 s | 22 | 0 | 0 | 22 |
| change-9daf6b668763df97cd9c5a2df93cf1/default (485-SNAPSHOT) | `github:shohamyamin/trino@9daf6b668763df97cd9c5a2df93cf17958b2adc6` | 9.97 s | +1.8% | 11.51 s | 22 | 0 | 0 | 22 |
| target2-3915e3120945449704ff4e34000583/default (485-SNAPSHOT) | `github:shohamyamin/trino@3915e3120945449704ff4e340005839bb3311f1f` | 9.52 s | -1.5% | 11.00 s | 22 | 0 | 0 | 22 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q13 | target2-3915e3120945449704ff4e34000583/default | -27.1% [-30%, -23%] |  |
| q20 | target2-3915e3120945449704ff4e34000583/default | -6.6% [-13%, -2%] |  |
| q13 | change-9daf6b668763df97cd9c5a2df93cf1/default | +13.2% [+7%, +17%] |  |

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
