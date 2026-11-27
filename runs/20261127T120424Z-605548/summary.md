## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@d4c1d043429de0cc104a29e7a72cefc9cdbd1aaf vs github:shohamyamin/trino@d2481e6353bebdba9ab9048c25fc377462b6ba15

ClickBench (derived) SF10, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 9V45 96-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 27.67 s | baseline | 65.87 s | 43 | 0 | 0 | 0 |
| change-d4c1d043429de0cc104a29e7a72cef/default (485-SNAPSHOT) | `github:shohamyamin/trino@d4c1d043429de0cc104a29e7a72cefc9cdbd1aaf` | 28.14 s | +2.4% | 66.36 s | 43 | 0 | 0 | 0 |
| target2-d2481e6353bebdba9ab9048c25fc37/default (485-SNAPSHOT) | `github:shohamyamin/trino@d2481e6353bebdba9ab9048c25fc377462b6ba15` | 27.44 s | +1.0% | 65.17 s | 43 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q06 | change-d4c1d043429de0cc104a29e7a72cef/default | -17.0% [-24%, -2%] |  |
| q23 | target2-d2481e6353bebdba9ab9048c25fc37/default | -11.1% [-20%, -3%] | yes |
| q42 | target2-d2481e6353bebdba9ab9048c25fc37/default | -7.0% [-14%, -1%] | yes |
| q00 | change-d4c1d043429de0cc104a29e7a72cef/default | +9.9% [+3%, +19%] |  |
| q17 | target2-d2481e6353bebdba9ab9048c25fc37/default | +11.4% [+3%, +24%] |  |
| q24 | target2-d2481e6353bebdba9ab9048c25fc37/default | +12.5% [+3%, +28%] |  |
| q00 | target2-d2481e6353bebdba9ab9048c25fc37/default | +12.6% [+0%, +24%] |  |
| q19 | target2-d2481e6353bebdba9ab9048c25fc37/default | +13.6% [+3%, +25%] |  |

**Result sets differ between configurations:** q03, q17, q18, q21, q22, q24, q31, q32, q38, q39, q40

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
