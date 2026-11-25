#!/usr/bin/env bash
# Runs inside the generator image. Writes official inputs to /out.
#   /out/tpch/sf<N>/qNN.sql      qgen -d (validation substitution parameters, SF-dependent Q11)
#   /out/tpch/answers/qNN.out    official SF1 answer set
#   /out/tpcds/templates/*.tpl   kit query templates
#   /out/tpcds/variants/*.tpl    TPC-approved query variants
#   /out/tpcds/spec.txt          specification text (Appendix B qualification parameters)
#   /out/tpcds/answers/*.ans     official SF1 answer set
set -euo pipefail

TPCH_SCALES=${TPCH_SCALES:-"1 10 30 100 300 1000"}

mkdir -p /out/tpch /out/tpcds

# ---- TPC-H ----
cd /opt/tpch-dbgen
for sf in $TPCH_SCALES; do
  dir=/out/tpch/sf$sf
  mkdir -p "$dir"
  for q in $(seq 1 22); do
    DSS_QUERY=queries ./qgen -d -s "$sf" "$q" > "$dir/$(printf 'q%02d' "$q").sql"
  done
done
mkdir -p /out/tpch/answers
for q in $(seq 1 22); do
  cp "answers/q$q.out" "/out/tpch/answers/$(printf 'q%02d' "$q").out"
done
cp /opt/tpch-dbgen.commit /out/tpch/GENERATOR_COMMIT

# ---- TPC-DS ----
cd /opt/tpcds-kit
mkdir -p /out/tpcds/templates /out/tpcds/variants /out/tpcds/answers
cp query_templates/query*.tpl /out/tpcds/templates/
cp query_variants/*.tpl /out/tpcds/variants/
cp -r answer_sets/. /out/tpcds/answers/
cp /opt/tpcds-spec.txt /out/tpcds/spec.txt
cp /opt/tpcds-kit.commit /out/tpcds/GENERATOR_COMMIT
echo "done"
