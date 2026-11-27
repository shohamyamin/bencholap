## bencholap: github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43 vs github:shohamyamin/trino@bfc7a1ba9166e6c89f121587de9b757b4ef0d20f

ClickBench (derived) SF10, layout `unpartitioned, sorted`, 5 measured runs per query (2 warmup, 4 round(s)). Machine: gh-standard: 4x AMD EPYC 7763 64-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| baseline-d546d85675b9fe322e6d40bb9a1e70/default/unpartitioned (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 4.15 s | baseline | 7.96 s | 4 | 0 | 0 | 0 |
| baseline-d546d85675b9fe322e6d40bb9a1e70/default/sorted (485-SNAPSHOT) | `github:trinodb/trino@d546d85675b9fe322e6d40bb9a1e70ee0549fa43` | 6.51 s | +111.0% | 12.77 s | 4 | 0 | 0 | 0 |
| change-bfc7a1ba9166e6c89f121587de9b75/default/unpartitioned (485-SNAPSHOT) | `github:shohamyamin/trino@bfc7a1ba9166e6c89f121587de9b757b4ef0d20f` | 4.18 s | -0.4% | 7.95 s | 4 | 0 | 0 | 0 |
| change-bfc7a1ba9166e6c89f121587de9b75/default/sorted (485-SNAPSHOT) | `github:shohamyamin/trino@bfc7a1ba9166e6c89f121587de9b757b4ef0d20f` | 6.62 s | +113.8% | 12.99 s | 4 | 0 | 0 | 0 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q23 | baseline-d546d85675b9fe322e6d40bb9a1e70/default/sorted | +10.9% [+2%, +20%] | yes |
| q23 | change-bfc7a1ba9166e6c89f121587de9b75/default/sorted | +13.2% [+2%, +23%] | yes |
| q24 | baseline-d546d85675b9fe322e6d40bb9a1e70/default/sorted | +143.1% [+133%, +151%] | yes |
| q24 | change-bfc7a1ba9166e6c89f121587de9b75/default/sorted | +149.6% [+138%, +161%] | yes |
| q26 | baseline-d546d85675b9fe322e6d40bb9a1e70/default/sorted | +152.8% [+147%, +176%] | yes |
| q26 | change-bfc7a1ba9166e6c89f121587de9b75/default/sorted | +155.6% [+146%, +181%] | yes |
| q25 | change-bfc7a1ba9166e6c89f121587de9b75/default/sorted | +189.5% [+155%, +220%] | yes |
| q25 | baseline-d546d85675b9fe322e6d40bb9a1e70/default/sorted | +190.8% [+155%, +218%] | yes |

**Result sets differ between configurations:** q24

_Results are derived from TPC benchmarks and are not comparable to published TPC results._
