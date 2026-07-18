FROM ghcr.io/your-org/motion-benchmark-base@sha256:REPLACE_WITH_DIGEST

WORKDIR /workspace

RUN mkdir -p \
    /workspace/data \
    /workspace/source \
    /workspace/model \
    /workspace/baseline \
    /workspace/tools \
    /workspace/examples \
    /workspace/output

COPY source/ /workspace/source/
COPY data/ /workspace/data/
COPY baseline/ /workspace/baseline/
COPY tools/ /workspace/tools/
COPY examples/ /workspace/examples/

RUN ln -s /opt/motion-benchmark/weights /workspace/model/frozen_weights \
    && ln -s /opt/motion-benchmark/skeleton /workspace/model/skeleton \
    && ln -s /opt/motion-benchmark/normalization /workspace/model/normalization

ENV PYTHONPATH="/workspace/source:/workspace/tools:/opt/motion-benchmark/momask:/opt/motion-benchmark/runtime"
ENV TOKENIZERS_PARALLELISM=false
ENV CUDA_DEVICE_ORDER=PCI_BUS_ID

CMD ["/bin/bash"]
