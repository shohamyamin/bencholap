#!/usr/bin/env bash
# Example `command` cluster deployer: installs the target build with the official Trino
# Helm chart (https://trinodb.github.io/charts). Not exercised in CI; adapt the values to
# your cluster (node sizes, namespace, ingress) before relying on it.
#
# bencholap provides:
#   BENCHOLAP_IMAGE        image to run (push custom builds to a registry the cluster can pull)
#   BENCHOLAP_VERSION      Trino version
#   BENCHOLAP_WORKERS      number of workers
#   BENCHOLAP_CONFIG_DIR   rendered config: catalog/*.properties (version profile + overrides)
#   BENCHOLAP_LABEL        configuration id (target/variant)
# Settings here: NAMESPACE, RELEASE, WORKER_MEMORY, WORKER_CPUS, HEAP.
#
# The values actually deployed are written to $BENCHOLAP_CONFIG_DIR/deployment.yaml, which
# bencholap stores in the results next to the rendered configuration.
set -euo pipefail

NAMESPACE=${NAMESPACE:-bencholap}
RELEASE=${RELEASE:-bencholap}
WORKER_MEMORY=${WORKER_MEMORY:-64Gi}
WORKER_CPUS=${WORKER_CPUS:-16}
HEAP=${HEAP:-48G}

repo=${BENCHOLAP_IMAGE%:*}
tag=${BENCHOLAP_IMAGE##*:}
values="$BENCHOLAP_CONFIG_DIR/deployment.yaml"

{
  echo "image: {repository: \"$repo\", tag: \"$tag\"}"
  echo "server: {workers: $BENCHOLAP_WORKERS}"
  echo "coordinator:"
  echo "  jvm: {maxHeapSize: \"$HEAP\"}"
  echo "  resources: {requests: {memory: \"$WORKER_MEMORY\", cpu: \"$WORKER_CPUS\"}, limits: {memory: \"$WORKER_MEMORY\", cpu: \"$WORKER_CPUS\"}}"
  echo "worker:"
  echo "  jvm: {maxHeapSize: \"$HEAP\"}"
  echo "  resources: {requests: {memory: \"$WORKER_MEMORY\", cpu: \"$WORKER_CPUS\"}, limits: {memory: \"$WORKER_MEMORY\", cpu: \"$WORKER_CPUS\"}}"
  echo "catalogs:"
  for f in "$BENCHOLAP_CONFIG_DIR"/catalog/*.properties; do
    echo "  $(basename "$f" .properties): |"
    sed 's/^/    /' "$f"
  done
} > "$values"

helm repo add trino https://trinodb.github.io/charts >/dev/null 2>&1 || true
helm upgrade --install "$RELEASE" trino/trino --namespace "$NAMESPACE" --create-namespace \
  -f "$values" --wait --timeout 15m
