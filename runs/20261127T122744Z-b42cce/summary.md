## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@d2481e6353bebdba9ab9048c25fc377462b6ba15 vs github:shohamyamin/trino@293db0e9fa092b021ac53923aff3710f7f8be845

TPC-DS (derived) SF1, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x Intel(R) Xeon(R) 6975P-C, 15.3 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 38.90 s | baseline | 48.32 s | 99 | 0 | 0 | 97 |
| change-d2481e6353bebdba9ab9048c25fc37/default (485-SNAPSHOT) | `github:shohamyamin/trino@d2481e6353bebdba9ab9048c25fc377462b6ba15` | 39.13 s | +0.9% | 48.71 s | 99 | 0 | 0 | 97 |
| target2-293db0e9fa092b021ac53923aff371/default (485-SNAPSHOT) | `github:shohamyamin/trino@293db0e9fa092b021ac53923aff3710f7f8be845` | 38.76 s | -1.0% | 48.35 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q98 | target2-293db0e9fa092b021ac53923aff371/default | -10.8% [-17%, -4%] |  |
| q99 | target2-293db0e9fa092b021ac53923aff371/default | -10.2% [-17%, -1%] |  |
| q44 | change-d2481e6353bebdba9ab9048c25fc37/default | +8.0% [+2%, +15%] | yes |

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
