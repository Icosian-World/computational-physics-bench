FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy==1.26.4 scipy==1.13.1 pytest==8.3.3 psutil==6.0.0

WORKDIR /tests
COPY tests/ /tests/
RUN mkdir -p /tests/run /tests/report /workspace/output

# Production hidden prompts, references, detector weights, thresholds, and
# BVH-to-VRMA assets are mounted into /tests/private after the agent run.
ENV PYTHONPATH=/tests
CMD ["bash", "/tests/test.sh"]
