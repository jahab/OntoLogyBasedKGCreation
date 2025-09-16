# FROM python:3.12 AS builder
# WORKDIR /app

# ARG HF_TOKEN
# ENV HF_TOKEN=${HF_TOKEN}

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Download Hugging Face model
# RUN python -c "from huggingface_hub import snapshot_download; \
#     snapshot_download('google/embeddinggemma-300M', cache_dir='/model-cache', token='$HF_TOKEN')"

# # ----------------- runtime stage -----------------
# FROM python:3.12-slim

# WORKDIR /app

# # Install runtime dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy pre-downloaded model cache
# COPY --from=builder /model-cache /model-cache

# # Environment vars
# ENV HF_HOME=/model-cache \
#     TRANSFORMERS_OFFLINE=1 \
#     HF_DATASETS_OFFLINE=1

# # Copy application src
# COPY src .

# # Entry point
# RUN chmod +x entry_point.sh
# ENTRYPOINT ["./entry_point.sh"]
# # CMD ["python"]



# syntax=docker/dockerfile:1
# FROM python:3.12-slim AS builder

# ARG HF_TOKEN
# ENV HF_TOKEN=${HF_TOKEN}

# # 1. system deps only needed for compiling wheels (if any)
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends git && \
#     rm -rf /var/lib/apt/lists/*

# WORKDIR /build

# # 2. install python deps once, using BuildKit cache mount
# COPY requirements.txt .
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --upgrade pip setuptools wheel && \
#     pip install --no-cache-dir -r requirements.txt

# # 3. pre-download gated model while we have network + token
# RUN python -c "\
# from huggingface_hub import snapshot_download; \
# snapshot_download('google/embeddinggemma-300M', cache_dir='/model-cache', token='$HF_TOKEN')"



# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 1. install uv (static binary, ~10 MB)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
export PATH=$PATH:/root/.cargo/bin
#  && ln -s "$(which uv)" /usr/local/bin/uv
# ENV PATH="/root/.cargo/bin:$PATH"
# RUN 
# ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /build

# 2. copy lock-file / requirements
COPY requirements.txt .

# 3. install packages (mount host cache for instant rebuilds)
RUN --mount=type=cache,target=/root/.cache/uv /root/.local/bin/uv pip install --python python3.12 --system --no-cache-dir -r requirements.txt
# RUN /root/.cargo/bin/uv pip install --python python3.12 --system --no-cache-dir -r requirements.txt
# 4. download gated model
RUN /root/.local/bin/uv run --no-project \
    python -c "from huggingface_hub import snapshot_download; \
               snapshot_download('google/embeddinggemma-300M', cache_dir='/model-cache', token='$HF_TOKEN')"



# ----------  runtime stage ----------
FROM python:3.12-slim

# 4. create non-root user
RUN groupadd -r app && useradd -r -g app app

# 5. copy only the installed packages (not the build cache)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /model-cache /model-cache

ENV HF_HOME=/model-cache \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1

WORKDIR /app

# 6. copy source last (max layer cache)
COPY src .
RUN chmod +x entry_point.sh && chown -R app:app /app

USER app
ENTRYPOINT ["./entry_point.sh"]
CMD ["bash"]