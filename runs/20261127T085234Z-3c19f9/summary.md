## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@ace427cd3b6ba4a2f8e13bb2655476735786fefb

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (unknown) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 52.74 s | baseline | 70.90 s | 99 | 0 | 0 | 97 |
| change-ace427cd3b6ba4a2f8e13bb2655476/default (unknown) | `github:shohamyamin/trino@ace427cd3b6ba4a2f8e13bb2655476735786fefb` | 52.09 s | -0.8% | 69.14 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q16 | change-ace427cd3b6ba4a2f8e13bb2655476/default | -13.3% [-24%, -0%] | yes |
| q60 | change-ace427cd3b6ba4a2f8e13bb2655476/default | -8.5% [-19%, -0%] | yes |
| q26 | change-ace427cd3b6ba4a2f8e13bb2655476/default | +8.2% [+3%, +17%] | yes |

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
