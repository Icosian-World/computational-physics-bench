FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy==1.26.4 scipy==1.13.1 torch==2.3.1 \
    einops==0.8.0 pyyaml==6.0.2 scikit-learn==1.5.2 \
    matplotlib==3.9.2 psutil==6.0.0

WORKDIR /workspace
RUN mkdir -p /workspace/{data,model,source,baseline,tools,examples,output}

# Small reviewable fixtures are committed. Production weights and licensed BVHs
# are injected by the task-build pipeline and must never be downloaded at runtime.
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY examples/ /workspace/examples/
COPY baseline/ /workspace/baseline/

ENV PYTHONPATH=/workspace/source:/workspace/tools:/opt/motion-benchmark/runtime
CMD ["/bin/bash"]
