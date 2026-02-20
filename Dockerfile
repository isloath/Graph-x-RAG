FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
# Install CPU-only PyTorch first (avoids ~1GB+ of NVIDIA CUDA packages)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY pyproject.toml ./pyproject.toml

EXPOSE 8000
# Long keep-alive so large ingest requests don't get closed while sending/processing
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
