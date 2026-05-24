
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --group docs --frozen

FROM base AS docbuilder

WORKDIR /appdocs

COPY mkdocs.yml .
COPY docs ./docs
COPY src ./src

WORKDIR /app

RUN uv run zensical build --config-file /appdocs/mkdocs.yml

FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY --from=base /app/.venv /app/.venv
COPY src /app
COPY --from=docbuilder /appdocs/site /app/docs

WORKDIR /app

RUN addgroup -g 2000 jumpgroup && \ 
    adduser -S -u 1001 -G jumpgroup jumpstart

USER jumpstart

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "/jumpstart/logging_config.yaml", "--proxy-headers", "--forwarded-allow-ips", "*"]
