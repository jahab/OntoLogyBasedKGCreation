FROM python:3.12 as builder
WORKDIR /app

ARG HF_TOKEN
ENV HF_TOKEN=$HF_TOKEN

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Hugging Face model
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('google/embeddinggemma-300M', cache_dir='/model-cache', token='$HF_TOKEN')"

# ----------------- runtime stage -----------------
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-downloaded model cache
# COPY --from=builder /model-cache /model-cache

# Environment vars
# ENV HF_HOME=/model-cache \
#     TRANSFORMERS_OFFLINE=1 \
#     HF_DATASETS_OFFLINE=1

# Copy application source
COPY src .

# Entry point
RUN chmod +x entry_point.sh
# ENTRYPOINT ["./entry_point.sh"]
CMD ["python"]
