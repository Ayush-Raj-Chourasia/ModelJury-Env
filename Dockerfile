FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the environment code
COPY server/ ./server/
COPY models.py ./models.py
COPY openenv.yaml ./openenv.yaml
COPY README.md ./README.md

# Set PYTHONPATH so that both 'server.app.main' and direct 'models' imports work
ENV PYTHONPATH="/app:/app/server/app:${PYTHONPATH}"

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
