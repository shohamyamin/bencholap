## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@9daf6b668763df97cd9c5a2df93cf17958b2adc6 vs github:shohamyamin/trino@3915e3120945449704ff4e340005839bb3311f1f

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 7763 64-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 52.92 s | baseline | 69.08 s | 99 | 0 | 0 | 97 |
| change-9daf6b668763df97cd9c5a2df93cf1/default (485-SNAPSHOT) | `github:shohamyamin/trino@9daf6b668763df97cd9c5a2df93cf17958b2adc6` | 52.34 s | -0.5% | 67.75 s | 99 | 0 | 0 | 97 |
| target2-3915e3120945449704ff4e34000583/default (485-SNAPSHOT) | `github:shohamyamin/trino@3915e3120945449704ff4e340005839bb3311f1f` | 52.60 s | -0.5% | 68.76 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q23 | change-9daf6b668763df97cd9c5a2df93cf1/default | -22.0% [-34%, -3%] |  |
| q40 | target2-3915e3120945449704ff4e34000583/default | -10.7% [-16%, -0%] |  |
| q46 | change-9daf6b668763df97cd9c5a2df93cf1/default | -7.7% [-13%, -1%] |  |

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
