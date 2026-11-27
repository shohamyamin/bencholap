## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@293db0e9fa092b021ac53923aff3710f7f8be845 vs github:shohamyamin/trino@372ee8c8004c25bc6f157a553933feee454440fd

ClickBench (derived) SF10, layout `unpartitioned`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 9V74 80-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 44.60 s | baseline | 108.30 s | 43 | 0 | 0 | 0 |
| change-293db0e9fa092b021ac53923aff371/default (485-SNAPSHOT) | `github:shohamyamin/trino@293db0e9fa092b021ac53923aff3710f7f8be845` | 43.75 s | -1.4% | 106.52 s | 43 | 0 | 0 | 0 |
| target2-372ee8c8004c25bc6f157a553933fe/default (485-SNAPSHOT) | `github:shohamyamin/trino@372ee8c8004c25bc6f157a553933feee454440fd` | 43.53 s | -2.1% | 106.74 s | 43 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q20 | change-293db0e9fa092b021ac53923aff371/default | -27.4% [-30%, -19%] |  |
| q18 | target2-372ee8c8004c25bc6f157a553933fe/default | -8.9% [-13%, -2%] |  |
| q24 | target2-372ee8c8004c25bc6f157a553933fe/default | -7.8% [-14%, -0%] |  |
| q27 | change-293db0e9fa092b021ac53923aff371/default | -7.5% [-10%, -2%] |  |
| q24 | change-293db0e9fa092b021ac53923aff371/default | -7.5% [-15%, -1%] |  |
| q00 | target2-372ee8c8004c25bc6f157a553933fe/default | -6.3% [-12%, -2%] |  |
| q23 | change-293db0e9fa092b021ac53923aff371/default | -5.1% [-10%, -0%] |  |
| q37 | target2-372ee8c8004c25bc6f157a553933fe/default | +8.5% [+2%, +19%] |  |
| q37 | change-293db0e9fa092b021ac53923aff371/default | +15.3% [+3%, +26%] |  |

**Result sets differ between configurations:** q17, q18, q21, q22, q24, q30, q31, q32, q38, q39, q40

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
