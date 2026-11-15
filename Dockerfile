FROM node:20-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.12-slim-bookworm AS runtime
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PORT=8080 STATIC_DIR=/app/static DATABASE_PATH=/app/data/kestrel.db DOCUMENT_DIR=/app/data/documents
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend ./backend
COPY --from=frontend /build/frontend/dist ./static
RUN groupadd --gid 10001 kestrel && useradd --uid 10001 --gid kestrel --no-create-home kestrel && mkdir -p /app/data && chown -R kestrel:kestrel /app/data
USER kestrel
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/health')"]
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --proxy-headers"]
