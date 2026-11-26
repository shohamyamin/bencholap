## bencholap: Trino releases every 10: 414..484

TPC-DS (derived) SF1, layout `unpartitioned`, 3 measured runs per query (1 warmup, 1 round(s)). Machine: gh-standard: 4x AMD EPYC 7763 64-Core Processor, 15.6 GB · docker, 0 worker(s), 10g / all cpus per node.

| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |
|---|---|---|---|---|---|---|---|---|
| trino-414/default (414) | `414` | 104.71 s | baseline | 135.61 s | 92 | 0 | 7 | 90 |
| trino-424/default (424) | `424` | 102.59 s | -1.8% | 137.44 s | 92 | 0 | 7 | 90 |
| trino-434/default (434) | `434` | 95.90 s | -7.6% | 122.16 s | 92 | 0 | 7 | 90 |
| trino-444/default (444) | `444` | 88.35 s | -13.8% | 125.11 s | 92 | 0 | 7 | 90 |
| trino-454/default (454) | `454` | 82.21 s | -18.8% | 115.01 s | 92 | 0 | 7 | 90 |
| trino-464/default (464) | `464` | 79.89 s | -22.8% | 111.11 s | 92 | 0 | 7 | 90 |
| trino-474/default (474) | `474` | 71.88 s | -30.1% | 74.38 s | 92 | 0 | 7 | 90 |
| trino-484/default (484) | `484` | 66.57 s | -35.7% | 78.81 s | 99 | 0 | 0 | 97 |

**Significant changes** (≥5%, 95% CI excludes no change; negative = faster):

| query | configuration | change [95% CI] | plan changed |
|---|---|---|---|
| q91 | trino-484/default | -74.0% [-78%, -49%] | yes |
| q85 | trino-484/default | -74.0% [-76%, -72%] | yes |
| q64 | trino-484/default | -72.9% [-74%, -71%] | yes |
| q37 | trino-474/default | -71.5% [-72%, -56%] | yes |
| q82 | trino-474/default | -71.3% [-74%, -63%] | yes |
| q82 | trino-484/default | -68.7% [-74%, -57%] | yes |
| q72 | trino-484/default | -65.7% [-68%, -64%] | yes |
| q84 | trino-484/default | -64.8% [-68%, -61%] | yes |
| q91 | trino-464/default | -63.4% [-68%, -44%] | yes |
| q91 | trino-474/default | -62.5% [-69%, -40%] | yes |
| q59 | trino-474/default | -61.7% [-70%, -48%] | yes |
| q85 | trino-474/default | -61.4% [-63%, -60%] | yes |
| q37 | trino-484/default | -60.4% [-70%, -48%] | yes |
| q59 | trino-484/default | -59.5% [-66%, -56%] | yes |
| q91 | trino-454/default | -58.6% [-65%, -26%] | yes |
| q64 | trino-464/default | -54.0% [-54%, -53%] | yes |
| q84 | trino-474/default | -53.1% [-59%, -46%] | yes |
| q02 | trino-474/default | -52.6% [-55%, -40%] | yes |
| q85 | trino-464/default | -52.5% [-55%, -51%] | yes |
| q80 | trino-484/default | -52.4% [-55%, -48%] | yes |
| q43 | trino-484/default | -52.1% [-54%, -33%] | yes |
| q41 | trino-484/default | -51.7% [-54%, -42%] | yes |
| q85 | trino-454/default | -51.6% [-53%, -50%] | yes |
| q64 | trino-454/default | -51.1% [-53%, -49%] | yes |
| q39 | trino-474/default | -50.8% [-53%, -48%] | yes |
| q71 | trino-484/default | -50.7% [-60%, -48%] | yes |
| q08 | trino-474/default | -50.6% [-59%, -36%] | yes |
| q99 | trino-484/default | -50.5% [-70%, -45%] | yes |
| q96 | trino-484/default | -50.3% [-54%, -45%] | yes |
| q08 | trino-464/default | -50.2% [-59%, -43%] | yes |
| q02 | trino-484/default | -50.1% [-53%, -38%] | yes |
| q08 | trino-454/default | -49.8% [-56%, -42%] | yes |
| q29 | trino-484/default | -49.8% [-52%, -39%] | yes |
| q54 | trino-484/default | -49.7% [-55%, -47%] | yes |
| q73 | trino-484/default | -48.9% [-57%, -30%] | yes |
| q42 | trino-474/default | -48.9% [-54%, -39%] | yes |
| q62 | trino-484/default | -48.5% [-56%, -40%] | yes |
| q71 | trino-474/default | -48.3% [-61%, -48%] | yes |
| q39 | trino-484/default | -48.1% [-52%, -46%] | yes |
| q25 | trino-484/default | -47.3% [-56%, -39%] | yes |
| q89 | trino-484/default | -47.2% [-50%, -41%] | yes |
| q64 | trino-444/default | -47.1% [-49%, -46%] | yes |
| q40 | trino-484/default | -46.8% [-53%, -31%] | yes |
| q43 | trino-474/default | -46.5% [-59%, -33%] | yes |
| q95 | trino-484/default | -46.4% [-50%, -40%] | yes |
| q64 | trino-474/default | -46.2% [-50%, -46%] | yes |
| q08 | trino-484/default | -46.2% [-57%, -26%] | yes |
| q24 | trino-484/default | -45.6% [-51%, -40%] | yes |
| q41 | trino-464/default | -45.4% [-56%, -23%] | yes |
| q91 | trino-444/default | -44.6% [-52%, -13%] | yes |
| q42 | trino-484/default | -44.5% [-55%, -27%] | yes |
| q05 | trino-454/default | -43.1% [-46%, -36%] | yes |
| q73 | trino-474/default | -43.1% [-51%, -6%] | yes |
| q32 | trino-484/default | -42.7% [-48%, -1%] | yes |
| q77 | trino-484/default | -42.2% [-49%, -22%] | yes |
| q90 | trino-484/default | -42.2% [-51%, -36%] | yes |
| q52 | trino-484/default | -41.9% [-59%, -31%] | yes |
| q27 | trino-484/default | -41.4% [-47%, -34%] | yes |
| q05 | trino-464/default | -41.3% [-46%, -38%] | yes |
| q75 | trino-484/default | -41.2% [-47%, -32%] | yes |
| q80 | trino-474/default | -41.2% [-50%, -38%] | yes |
| q40 | trino-474/default | -40.8% [-57%, -34%] | yes |
| q54 | trino-474/default | -40.3% [-46%, -37%] | yes |
| q42 | trino-464/default | -40.3% [-55%, -28%] | yes |
| q88 | trino-474/default | -40.2% [-43%, -32%] | yes |
| q69 | trino-474/default | -40.2% [-43%, -25%] | yes |
| q50 | trino-484/default | -39.8% [-47%, -31%] | yes |
| q75 | trino-474/default | -39.7% [-44%, -36%] | yes |
| q41 | trino-474/default | -39.6% [-43%, -21%] | yes |
| q08 | trino-444/default | -39.4% [-54%, -18%] | yes |
| q24 | trino-474/default | -39.0% [-46%, -34%] | yes |
| q52 | trino-474/default | -38.9% [-60%, -31%] | yes |
| q26 | trino-484/default | -38.7% [-45%, -22%] | yes |
| q85 | trino-444/default | -38.5% [-40%, -36%] | yes |
| q67 | trino-484/default | -38.5% [-47%, -37%] | yes |
| q96 | trino-474/default | -38.4% [-44%, -35%] | yes |
| q77 | trino-474/default | -38.3% [-46%, -37%] | yes |
| q10 | trino-474/default | -38.0% [-44%, -28%] | yes |
| q72 | trino-474/default | -37.9% [-43%, -35%] | yes |
| q41 | trino-444/default | -37.8% [-44%, -33%] | yes |
| q93 | trino-484/default | -37.7% [-48%, -35%] | yes |
| q69 | trino-484/default | -37.7% [-50%, -27%] | yes |
| q20 | trino-484/default | -37.5% [-43%, -26%] | yes |
| q63 | trino-484/default | -37.5% [-57%, -31%] | yes |
| q97 | trino-484/default | -37.3% [-45%, -25%] | yes |
| q88 | trino-454/default | -36.8% [-40%, -22%] | yes |
| q62 | trino-474/default | -36.7% [-46%, -29%] | yes |
| q44 | trino-464/default | -36.5% [-44%, -16%] | yes |
| q19 | trino-484/default | -36.4% [-53%, -28%] | yes |
| q92 | trino-464/default | -36.4% [-44%, -19%] | yes |
| q61 | trino-484/default | -36.4% [-40%, -27%] | yes |
| q92 | trino-484/default | -36.1% [-43%, -10%] | yes |
| q34 | trino-474/default | -35.3% [-47%, -9%] | yes |
| q19 | trino-474/default | -35.3% [-50%, -25%] | yes |
| q77 | trino-464/default | -35.3% [-47%, -20%] | yes |
| q89 | trino-474/default | -35.0% [-48%, -19%] | yes |
| q70 | trino-484/default | -35.0% [-37%, -27%] | yes |
| q50 | trino-474/default | -34.7% [-42%, -26%] | yes |
| q18 | trino-484/default | -34.7% [-44%, -25%] | yes |
| q23 | trino-474/default | -34.7% [-39%, -30%] | yes |
| q96 | trino-464/default | -34.6% [-37%, -12%] | yes |
| q78 | trino-484/default | -34.6% [-56%, -24%] | yes |
| q02 | trino-454/default | -34.5% [-39%, -19%] | yes |
| q14 | trino-474/default | -34.2% [-40%, -28%] | yes |
| q49 | trino-474/default | -34.1% [-40%, -24%] | yes |
| q22 | trino-484/default | -34.0% [-35%, -29%] | yes |
| q63 | trino-474/default | -33.8% [-57%, -23%] | yes |
| q71 | trino-464/default | -33.8% [-50%, -23%] | yes |
| q44 | trino-484/default | -33.8% [-43%, -14%] | yes |
| q27 | trino-474/default | -33.7% [-37%, -15%] | yes |
| q05 | trino-444/default | -33.6% [-39%, -29%] | yes |
| q27 | trino-454/default | -32.7% [-35%, -17%] | yes |
| q37 | trino-464/default | -32.7% [-34%, -8%] | yes |
| q82 | trino-454/default | -32.5% [-34%, -10%] | yes |
| q75 | trino-464/default | -32.4% [-34%, -28%] | yes |
| q97 | trino-474/default | -32.2% [-39%, -29%] | yes |
| q66 | trino-484/default | -32.2% [-38%, -22%] | yes |
| q88 | trino-464/default | -32.2% [-38%, -20%] | yes |
| q60 | trino-464/default | -32.1% [-41%, -9%] | yes |
| q02 | trino-464/default | -31.9% [-43%, -18%] | yes |
| q05 | trino-434/default | -31.8% [-36%, -23%] | yes |
| q05 | trino-474/default | -31.4% [-35%, -26%] | yes |
| q94 | trino-484/default | -31.0% [-44%, -12%] | yes |
| q10 | trino-484/default | -30.8% [-41%, -16%] | yes |
| q23 | trino-484/default | -30.7% [-34%, -20%] | yes |
| q61 | trino-464/default | -30.7% [-36%, -22%] | yes |
| q06 | trino-484/default | -30.7% [-32%, -11%] | yes |
| q37 | trino-454/default | -30.3% [-33%, -14%] | yes |
| q73 | trino-464/default | -30.3% [-41%, -11%] | yes |
| q15 | trino-454/default | -30.2% [-38%, -11%] | yes |
| q30 | trino-454/default | -30.1% [-41%, -17%] | yes |
| q84 | trino-464/default | -30.1% [-39%, -28%] | yes |
| q74 | trino-464/default | -30.1% [-37%, -18%] | yes |
| q98 | trino-484/default | -30.1% [-35%, -27%] | yes |
| q80 | trino-464/default | -30.0% [-46%, -20%] | yes |
| q32 | trino-474/default | -30.0% [-38%, -21%] | yes |
| q75 | trino-454/default | -30.0% [-35%, -26%] | yes |
| q77 | trino-454/default | -29.7% [-40%, -28%] | yes |
| q30 | trino-464/default | -29.5% [-39%, -10%] | yes |
| q93 | trino-474/default | -29.4% [-40%, -2%] | yes |
| q32 | trino-464/default | -29.4% [-39%, -13%] | yes |
| q04 | trino-474/default | -29.3% [-36%, -11%] | yes |
| q95 | trino-474/default | -28.9% [-38%, -18%] | yes |
| q88 | trino-484/default | -28.6% [-36%, -25%] | yes |
| q55 | trino-484/default | -28.5% [-48%, -7%] | yes |
| q66 | trino-474/default | -28.4% [-37%, -9%] | yes |
| q16 | trino-474/default | -28.3% [-48%, -19%] | yes |
| q14 | trino-484/default | -28.2% [-35%, -20%] | yes |
| q44 | trino-474/default | -27.9% [-36%, -14%] | yes |
| q66 | trino-464/default | -27.8% [-34%, -24%] | yes |
| q17 | trino-484/default | -27.8% [-44%, -19%] | yes |
| q15 | trino-464/default | -27.8% [-39%, -10%] | yes |
| q80 | trino-454/default | -27.3% [-37%, -6%] | yes |
| q55 | trino-474/default | -27.2% [-51%, -24%] | yes |
| q20 | trino-474/default | -27.2% [-45%, -25%] | yes |
| q90 | trino-474/default | -27.1% [-44%, -17%] | yes |
| q45 | trino-464/default | -27.1% [-35%, -16%] | yes |
| q12 | trino-474/default | -27.0% [-43%, -6%] | yes |
| q73 | trino-454/default | -27.0% [-37%, -8%] | yes |
| q09 | trino-474/default | -27.0% [-29%, -17%] | yes |
| q20 | trino-464/default | -26.9% [-30%, -11%] | yes |
| q96 | trino-454/default | -26.9% [-33%, -18%] | yes |
| q69 | trino-464/default | -26.7% [-32%, -18%] | yes |
| q07 | trino-454/default | -26.7% [-32%, -21%] | yes |
| q84 | trino-454/default | -26.7% [-35%, -24%] | yes |
| q43 | trino-454/default | -26.6% [-32%, -15%] | yes |
| q71 | trino-454/default | -26.6% [-52%, -21%] | yes |
| q65 | trino-464/default | -26.5% [-29%, -14%] | yes |
| q78 | trino-474/default | -26.3% [-49%, -9%] | yes |
| q49 | trino-484/default | -26.2% [-34%, -8%] | yes |
| q82 | trino-464/default | -26.2% [-31%, -3%] | yes |
| q32 | trino-444/default | -26.0% [-35%, -15%] | yes |
| q22 | trino-474/default | -26.0% [-28%, -19%] | yes |
| q26 | trino-474/default | -26.0% [-33%, -21%] | yes |
| q94 | trino-474/default | -25.8% [-36%, -22%] | yes |
| q70 | trino-444/default | -25.7% [-28%, -20%] | yes |
| q61 | trino-454/default | -25.7% [-30%, -15%] | yes |
| q89 | trino-454/default | -25.6% [-34%, -12%] | yes |
| q42 | trino-434/default | -25.4% [-36%, -11%] | yes |
| q70 | trino-474/default | -25.3% [-33%, -20%] | yes |
| q64 | trino-434/default | -25.3% [-26%, -24%] | yes |
| q44 | trino-444/default | -25.3% [-34%, -12%] | yes |
| q26 | trino-464/default | -25.2% [-38%, -19%] | yes |
| q07 | trino-474/default | -25.1% [-40%, -18%] | yes |
| q77 | trino-444/default | -24.8% [-33%, -21%] | yes |
| q07 | trino-464/default | -24.7% [-31%, -13%] | yes |
| q26 | trino-454/default | -24.7% [-37%, -23%] | yes |
| q03 | trino-474/default | -24.6% [-30%, -24%] | yes |
| q47 | trino-454/default | -24.6% [-28%, -4%] | yes |
| q72 | trino-464/default | -24.6% [-29%, -23%] | yes |
| q33 | trino-464/default | -24.6% [-35%, -12%] | yes |
| q13 | trino-474/default | -24.4% [-31%, -19%] | yes |
| q54 | trino-464/default | -24.4% [-33%, -21%] | yes |
| q47 | trino-484/default | -24.0% [-27%, -12%] | yes |
| q82 | trino-444/default | -24.0% [-29%, -0%] | yes |
| q74 | trino-454/default | -23.9% [-29%, -2%] | yes |
| q98 | trino-474/default | -23.9% [-33%, -16%] | yes |
| q48 | trino-474/default | -23.8% [-31%, -21%] | yes |
| q18 | trino-474/default | -23.7% [-33%, -15%] | yes |
| q74 | trino-444/default | -23.7% [-27%, -0%] | yes |
| q07 | trino-484/default | -23.6% [-44%, -5%] | yes |
| q87 | trino-464/default | -23.6% [-32%, -19%] | yes |
| q61 | trino-444/default | -23.6% [-34%, -15%] | yes |
| q13 | trino-484/default | -23.6% [-25%, -20%] | yes |
| q47 | trino-464/default | -23.4% [-26%, -16%] | yes |
| q02 | trino-444/default | -23.4% [-32%, -10%] | yes |
| q06 | trino-474/default | -23.3% [-30%, -8%] | yes |
| q39 | trino-454/default | -23.3% [-27%, -21%] | yes |
| q34 | trino-484/default | -23.3% [-38%, -20%] | yes |
| q95 | trino-444/default | -23.0% [-28%, -8%] | yes |
| q70 | trino-434/default | -23.0% [-27%, -17%] | yes |
| q10 | trino-444/default | -23.0% [-28%, -21%] | yes |
| q75 | trino-444/default | -22.9% [-26%, -14%] | yes |
| q29 | trino-474/default | -22.8% [-26%, -8%] | yes |
| q86 | trino-484/default | -22.7% [-30%, -15%] | yes |
| q44 | trino-454/default | -22.7% [-35%, -7%] | yes |
| q46 | trino-464/default | -22.6% [-34%, -14%] | yes |
| q70 | trino-464/default | -22.6% [-25%, -15%] | yes |
| q10 | trino-454/default | -22.5% [-27%, -13%] | yes |
| q33 | trino-484/default | -22.4% [-30%, -22%] | yes |
| q60 | trino-444/default | -22.3% [-28%, -7%] | yes |
| q74 | trino-434/default | -22.3% [-24%, -13%] | yes |
| q56 | trino-484/default | -22.3% [-36%, -10%] | yes |
| q56 | trino-474/default | -22.1% [-31%, -9%] | yes |
| q41 | trino-424/default | -22.0% [-37%, -5%] |  |
| q86 | trino-454/default | -21.9% [-30%, -21%] | yes |
| q86 | trino-464/default | -21.9% [-31%, -22%] | yes |
| q62 | trino-464/default | -21.7% [-31%, -21%] | yes |
| q44 | trino-434/default | -21.6% [-28%, -3%] | yes |
| q27 | trino-464/default | -21.5% [-32%, -4%] | yes |
| q32 | trino-454/default | -21.5% [-30%, -15%] | yes |
| q59 | trino-444/default | -21.4% [-30%, -20%] | yes |
| q87 | trino-444/default | -21.3% [-28%, -8%] | yes |
| q43 | trino-444/default | -21.1% [-29%, -11%] | yes |
| q59 | trino-464/default | -21.1% [-30%, -19%] | yes |
| q78 | trino-464/default | -20.8% [-48%, -10%] | yes |
| q60 | trino-474/default | -20.8% [-30%, -12%] | yes |
| q84 | trino-434/default | -20.8% [-26%, -3%] | yes |
| q59 | trino-454/default | -20.7% [-31%, -16%] | yes |
| q74 | trino-484/default | -20.5% [-22%, -11%] | yes |
| q67 | trino-474/default | -20.5% [-32%, -18%] | yes |
| q22 | trino-454/default | -20.4% [-22%, -16%] | yes |
| q46 | trino-454/default | -20.3% [-30%, -5%] | yes |
| q69 | trino-444/default | -20.2% [-28%, -7%] | yes |
| q16 | trino-484/default | -20.2% [-50%, -10%] | yes |
| q35 | trino-464/default | -20.1% [-35%, -9%] | yes |
| q43 | trino-434/default | -20.0% [-22%, -1%] | yes |
| q65 | trino-434/default | -20.0% [-24%, -13%] | yes |
| q45 | trino-454/default | -19.9% [-26%, -4%] | yes |
| q03 | trino-484/default | -19.8% [-24%, -7%] | yes |
| q81 | trino-464/default | -19.7% [-43%, -3%] | yes |
| q04 | trino-484/default | -19.7% [-30%, -10%] | yes |
| q87 | trino-434/default | -19.6% [-24%, -11%] | yes |
| q56 | trino-464/default | -19.6% [-34%, -3%] | yes |
| q64 | trino-424/default | -19.5% [-22%, -19%] |  |
| q99 | trino-454/default | -19.5% [-46%, -8%] | yes |
| q25 | trino-474/default | -19.4% [-32%, -5%] | yes |
| q05 | trino-424/default | -19.4% [-29%, -9%] | yes |
| q54 | trino-444/default | -19.3% [-30%, -17%] | yes |
| q61 | trino-474/default | -19.3% [-25%, -7%] | yes |
| q55 | trino-464/default | -19.3% [-26%, -2%] | yes |
| q04 | trino-464/default | -19.2% [-33%, -10%] | yes |
| q57 | trino-454/default | -19.2% [-23%, -2%] | yes |
| q63 | trino-464/default | -19.1% [-45%, -14%] | yes |
| q14 | trino-454/default | -19.0% [-31%, -12%] | yes |
| q72 | trino-454/default | -19.0% [-24%, -17%] | yes |
| q49 | trino-454/default | -19.0% [-24%, -15%] | yes |
| q99 | trino-464/default | -18.9% [-45%, -10%] | yes |
| q49 | trino-464/default | -18.9% [-25%, -6%] | yes |
| q69 | trino-434/default | -18.8% [-28%, -13%] | yes |
| q65 | trino-484/default | -18.5% [-26%, -3%] | yes |
| q12 | trino-484/default | -18.3% [-37%, -7%] | yes |
| q20 | trino-434/default | -18.3% [-25%, -14%] | yes |
| q14 | trino-464/default | -18.2% [-26%, -15%] | yes |
| q54 | trino-434/default | -18.2% [-24%, -9%] | yes |
| q48 | trino-454/default | -18.1% [-27%, -15%] | yes |
| q22 | trino-464/default | -18.1% [-22%, -17%] | yes |
| q66 | trino-454/default | -17.9% [-29%, -14%] | yes |
| q20 | trino-454/default | -17.9% [-22%, -9%] | yes |
| q51 | trino-484/default | -17.8% [-28%, -14%] | yes |
| q95 | trino-464/default | -17.8% [-20%, -13%] | yes |
| q87 | trino-454/default | -17.6% [-28%, -5%] | yes |
| q54 | trino-454/default | -17.6% [-24%, -9%] | yes |
| q78 | trino-444/default | -17.6% [-45%, -9%] | yes |
| q96 | trino-444/default | -17.5% [-21%, -12%] | yes |
| q48 | trino-484/default | -17.4% [-34%, -3%] | yes |
| q88 | trino-444/default | -17.3% [-22%, -14%] | yes |
| q66 | trino-444/default | -17.2% [-22%, -9%] | yes |
| q09 | trino-464/default | -17.2% [-23%, -14%] | yes |
| q63 | trino-454/default | -17.2% [-47%, -5%] | yes |
| q47 | trino-444/default | -17.2% [-24%, -10%] | yes |
| q35 | trino-474/default | -17.1% [-30%, -4%] | yes |
| q86 | trino-434/default | -17.0% [-28%, -15%] | yes |
| q09 | trino-444/default | -16.9% [-24%, -13%] | yes |
| q20 | trino-444/default | -16.9% [-23%, -12%] | yes |
| q68 | trino-464/default | -16.9% [-23%, -5%] | yes |
| q22 | trino-444/default | -16.8% [-21%, -16%] | yes |
| q75 | trino-434/default | -16.8% [-25%, -11%] | yes |
| q35 | trino-484/default | -16.7% [-31%, -13%] | yes |
| q32 | trino-424/default | -16.6% [-26%, -5%] |  |
| q51 | trino-474/default | -16.4% [-25%, -13%] | yes |
| q89 | trino-464/default | -16.4% [-30%, -9%] | yes |
| q38 | trino-464/default | -16.3% [-31%, -5%] | yes |
| q32 | trino-434/default | -16.0% [-29%, -8%] | yes |
| q86 | trino-474/default | -16.0% [-25%, -15%] | yes |
| q87 | trino-484/default | -16.0% [-22%, -3%] | yes |
| q07 | trino-434/default | -15.9% [-21%, -6%] | yes |
| q47 | trino-474/default | -15.8% [-21%, -5%] | yes |
| q39 | trino-464/default | -15.8% [-22%, -14%] | yes |
| q02 | trino-434/default | -15.7% [-30%, -2%] | yes |
| q84 | trino-444/default | -15.6% [-28%, -12%] | yes |
| q68 | trino-434/default | -15.6% [-17%, -1%] | yes |
| q77 | trino-434/default | -15.5% [-25%, -11%] | yes |
| q52 | trino-464/default | -15.4% [-40%, -4%] | yes |
| q46 | trino-444/default | -15.4% [-25%, -4%] | yes |
| q74 | trino-474/default | -14.8% [-18%, -0%] | yes |
| q71 | trino-444/default | -14.7% [-38%, -2%] | yes |
| q71 | trino-434/default | -14.3% [-38%, -11%] | yes |
| q13 | trino-454/default | -14.3% [-17%, -11%] | yes |
| q61 | trino-434/default | -14.2% [-26%, -3%] | yes |
| q39 | trino-434/default | -14.2% [-18%, -7%] | yes |
| q62 | trino-454/default | -14.2% [-29%, -13%] | yes |
| q33 | trino-454/default | -14.0% [-38%, -7%] | yes |
| q51 | trino-434/default | -13.8% [-23%, -9%] | yes |
| q04 | trino-444/default | -13.6% [-23%, -4%] | yes |
| q86 | trino-444/default | -13.6% [-27%, -12%] | yes |
| q59 | trino-434/default | -13.6% [-27%, -12%] | yes |
| q72 | trino-444/default | -13.5% [-21%, -11%] | yes |
| q13 | trino-464/default | -13.5% [-16%, -9%] | yes |
| q33 | trino-474/default | -13.5% [-24%, -0%] | yes |
| q39 | trino-444/default | -13.3% [-17%, -9%] | yes |
| q97 | trino-454/default | -13.2% [-24%, -9%] | yes |
| q18 | trino-464/default | -12.8% [-21%, -10%] | yes |
| q76 | trino-464/default | -12.6% [-30%, -3%] | yes |
| q34 | trino-464/default | -12.3% [-26%, -1%] | yes |
| q24 | trino-464/default | -12.3% [-25%, -4%] | yes |
| q76 | trino-454/default | -12.2% [-26%, -4%] | yes |
| q56 | trino-444/default | -11.9% [-18%, -5%] | yes |
| q09 | trino-454/default | -11.8% [-16%, -4%] | yes |
| q07 | trino-444/default | -11.5% [-15%, -5%] | yes |
| q79 | trino-454/default | -11.3% [-15%, -4%] | yes |
| q51 | trino-454/default | -11.3% [-18%, -10%] | yes |
| q55 | trino-434/default | -11.3% [-19%, -10%] | yes |
| q33 | trino-444/default | -11.2% [-17%, -3%] | yes |
| q03 | trino-434/default | -10.7% [-11%, -0%] | yes |
| q99 | trino-444/default | -10.6% [-37%, -2%] | yes |
| q10 | trino-464/default | -10.3% [-24%, -7%] | yes |
| q54 | trino-424/default | -10.2% [-22%, -6%] | yes |
| q72 | trino-424/default | -10.2% [-18%, -9%] |  |
| q10 | trino-434/default | -9.9% [-18%, -2%] | yes |
| q90 | trino-444/default | -9.6% [-29%, -1%] | yes |
| q65 | trino-424/default | -9.4% [-12%, -3%] |  |
| q22 | trino-434/default | -9.4% [-15%, -7%] | yes |
| q24 | trino-454/default | -9.2% [-21%, -5%] | yes |
| q51 | trino-444/default | -9.0% [-17%, -4%] | yes |
| q28 | trino-444/default | -8.7% [-25%, -1%] | yes |
| q19 | trino-464/default | -8.6% [-29%, -1%] | yes |
| q23 | trino-464/default | -8.4% [-10%, -2%] | yes |
| q26 | trino-444/default | -8.3% [-19%, -5%] | yes |
| q62 | trino-444/default | -8.0% [-21%, -6%] | yes |
| q19 | trino-454/default | -7.6% [-28%, -2%] | yes |
| q51 | trino-464/default | -6.9% [-14%, -6%] | yes |
| q67 | trino-464/default | -6.9% [-16%, -1%] | yes |
| q71 | trino-424/default | -6.9% [-22%, -2%] | yes |
| q97 | trino-444/default | -6.9% [-16%, -3%] | yes |
| q14 | trino-444/default | -6.8% [-20%, -2%] | yes |
| q49 | trino-434/default | -6.8% [-13%, -4%] | yes |
| q97 | trino-434/default | -6.2% [-17%, -3%] | yes |
| q18 | trino-444/default | -5.1% [-13%, -3%] | yes |
| q79 | trino-484/default | +8.3% [+8%, +20%] | yes |
| q85 | trino-434/default | +8.5% [+4%, +11%] | yes |
| q56 | trino-424/default | +8.6% [+1%, +14%] |  |
| q50 | trino-434/default | +10.9% [+1%, +27%] | yes |
| q79 | trino-474/default | +12.5% [+11%, +29%] | yes |
| q62 | trino-424/default | +13.2% [+1%, +34%] |  |
| q50 | trino-444/default | +13.8% [+2%, +23%] | yes |
| q93 | trino-434/default | +21.1% [+5%, +33%] | yes |
| q76 | trino-474/default | +22.8% [+0%, +43%] | yes |
| q13 | trino-434/default | +23.5% [+13%, +30%] | yes |
| q22 | trino-424/default | +24.0% [+24%, +28%] | yes |
| q50 | trino-454/default | +24.9% [+2%, +58%] | yes |
| q57 | trino-484/default | +26.2% [+19%, +33%] | yes |
| q79 | trino-424/default | +32.0% [+8%, +54%] |  |
| q57 | trino-474/default | +35.9% [+28%, +39%] | yes |
| q15 | trino-474/default | +57.0% [+44%, +73%] | yes |
| q15 | trino-484/default | +58.3% [+41%, +76%] | yes |

**Failures:**

- q11 on trino-414/default: wrong_result 
- q11 on trino-424/default: wrong_result 
- q11 on trino-434/default: wrong_result 
- q11 on trino-444/default: wrong_result 
- q11 on trino-454/default: wrong_result 
- q11 on trino-464/default: wrong_result 
- q11 on trino-474/default: wrong_result 
- q21 on trino-414/default: wrong_result 
- q21 on trino-424/default: wrong_result 
- q21 on trino-434/default: wrong_result 
- q21 on trino-444/default: wrong_result 
- q21 on trino-454/default: wrong_result 
- q21 on trino-464/default: wrong_result 
- q21 on trino-474/default: wrong_result 
- q31 on trino-414/default: wrong_result 
- q31 on trino-424/default: wrong_result 
- q31 on trino-434/default: wrong_result 
- q31 on trino-444/default: wrong_result 
- q31 on trino-454/default: wrong_result 
- q31 on trino-464/default: wrong_result 
- q31 on trino-474/default: wrong_result 
- q36 on trino-414/default: wrong_result 
- q36 on trino-424/default: wrong_result 
- q36 on trino-434/default: wrong_result 
- q36 on trino-444/default: wrong_result 
- q36 on trino-454/default: wrong_result 
- q36 on trino-464/default: wrong_result 
- q36 on trino-474/default: wrong_result 
- q53 on trino-414/default: wrong_result 
- q53 on trino-424/default: wrong_result 
- q53 on trino-434/default: wrong_result 
- q53 on trino-444/default: wrong_result 
- q53 on trino-454/default: wrong_result 
- q53 on trino-464/default: wrong_result 
- q53 on trino-474/default: wrong_result 
- q58 on trino-414/default: wrong_result 
- q58 on trino-424/default: wrong_result 
- q58 on trino-434/default: wrong_result 
- q58 on trino-444/default: wrong_result 
- q58 on trino-454/default: wrong_result 
- q58 on trino-464/default: wrong_result 
- q58 on trino-474/default: wrong_result 
- q83 on trino-414/default: wrong_result 
- q83 on trino-424/default: wrong_result 
- q83 on trino-434/default: wrong_result 
- q83 on trino-444/default: wrong_result 
- q83 on trino-454/default: wrong_result 
- q83 on trino-464/default: wrong_result 
- q83 on trino-474/default: wrong_result 

**Result sets differ between configurations:** q66

<details><summary>Settings that differ between configurations</summary>

| setting | trino-414/default | trino-424/default | trino-434/default | trino-444/default | trino-454/default | trino-464/default | trino-474/default | trino-484/default |
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
