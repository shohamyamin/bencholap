# Prepares the official TPC inputs for the canonical query texts committed under
# src/bencholap/benchmarks/*/{queries,answers}. Not needed at benchmark run time.
FROM gcc:13

RUN apt-get update && apt-get install -y --no-install-recommends git poppler-utils && rm -rf /var/lib/apt/lists/*

# TPC-H dbgen/qgen 2.x. electrum/tpch-dbgen is the copy of the TPC-H tools used by the
# Trino/airlift TPC-H generator. Pinned to a commit for reproducibility.
ARG TPCH_DBGEN_REPO=https://github.com/electrum/tpch-dbgen.git
ARG TPCH_DBGEN_REF=32f1c1b92d1664dba542e927d23d86ffa57aa253
RUN git clone "$TPCH_DBGEN_REPO" /opt/tpch-dbgen \
    && cd /opt/tpch-dbgen && git checkout "$TPCH_DBGEN_REF" \
    && git rev-parse HEAD > /opt/tpch-dbgen.commit \
    && make -j"$(nproc)" qgen dbgen

# TPC-DS kit v2.10 (gregrahn/tpcds-kit): query templates, approved query variants,
# answer sets and the matching specification PDF (Appendix B holds the qualification
# substitution parameters). dsqgen itself is not used, see tpcds_qualification.py.
ARG TPCDS_KIT_REPO=https://github.com/gregrahn/tpcds-kit.git
ARG TPCDS_KIT_REF=5a3a81796992b725c2a8b216767e142609966752
RUN git clone "$TPCDS_KIT_REPO" /opt/tpcds-kit \
    && cd /opt/tpcds-kit && git checkout "$TPCDS_KIT_REF" \
    && git rev-parse HEAD > /opt/tpcds-kit.commit \
    && pdftotext -layout specification/TPC-DS_v2.10.0.pdf /opt/tpcds-spec.txt

COPY generate.sh /generate.sh
ENTRYPOINT ["/bin/bash", "/generate.sh"]
