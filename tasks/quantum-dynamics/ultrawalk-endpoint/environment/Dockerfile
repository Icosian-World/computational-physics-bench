FROM python:3.11-slim

# Install system dependencies if any
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Install Python dependencies
RUN pip install --no-cache-dir \
    numpy \
    scipy \
    pandas \
    matplotlib

# Create directories for data and output
RUN mkdir -p /workspace/data /workspace/output

# Bake the public observations into the task image. Agents and the verifier
# both expect these files at /workspace/data inside the Harbor container.
COPY data/ /workspace/data/

CMD ["/bin/bash"]
