FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY src /jumpstart
WORKDIR /jumpstart

RUN uv pip install --no-cache-dir -r requirements.txt --system

CMD ["echo", ":)"]