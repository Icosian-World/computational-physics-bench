FROM ghcr.io/your-org/motion-benchmark-base@sha256:REPLACE_WITH_DIGEST

WORKDIR /tests

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY tests/requirements.lock /tmp/verifier-requirements.lock
RUN pip install --no-cache-dir -r /tmp/verifier-requirements.lock

COPY tests/ /tests/

RUN mkdir -p \
    /workspace/output \
    /tests/run \
    /tests/report \
    /tests/report/bvh \
    /tests/report/vrma \
    /tests/report/video

ENV PYTHONPATH="/tests:/opt/motion-benchmark/momask:/opt/motion-benchmark/runtime"
ENV TOKENIZERS_PARALLELISM=false

CMD ["/bin/bash", "/tests/test.sh"]
