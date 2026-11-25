#!/usr/bin/env bash
# Regenerate canonical TPC-H / TPC-DS queries and answer sets from the official generators.
# Output goes to src/bencholap/benchmarks/{tpch,tpcds}/{queries,answers}.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
raw=$(mktemp -d)
trap 'rm -rf "$raw"' EXIT

docker build -q -t bencholap-querygen "$here" >/dev/null
docker run --rm --user "$(id -u):$(id -g)" -v "$raw:/out" bencholap-querygen
python3 "$here/normalize.py" "$raw" "$repo/src/bencholap/benchmarks"
echo "queries written to $repo/src/bencholap/benchmarks"
