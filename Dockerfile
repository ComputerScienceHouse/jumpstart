FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY src /jumpstart
WORKDIR /jumpstart

RUN addgroup -g 2000 jumpgroup && adduser -S -u 1001 -G jumpgroup jumpstart

RUN uv pip install --no-cache-dir -r requirements.txt --system && rm requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "/jumpstart/logging_config.yaml"]
