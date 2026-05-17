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
    pandas

# Create directories for data and output
RUN mkdir -p /workspace/data /workspace/output

# Copy task files (if any are baked into the image)
# Usually Harbor mounts these, but we can ensure they exist
# COPY data/ /workspace/data/

CMD ["/bin/bash"]
