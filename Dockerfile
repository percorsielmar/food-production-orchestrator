# Orchestratore LLM (prototipo standalone) - FastAPI + WebSocket
# Python allineato a .python-version (3.10), dipendenze bloccate da uv.lock
FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.31 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Layer dipendenze (cache-friendly): solo pyproject + lock
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

# Codice applicativo
COPY src ./src
COPY dev ./dev
RUN uv sync --frozen --no-dev

ENV APP_HOST=0.0.0.0 \
    APP_PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=10s \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"APP_PORT\",\"5000\")}/health', timeout=4).status == 200 else 1)"

CMD ["sh", "-c", "uvicorn orchestratore_llm.main:app --host ${APP_HOST} --port ${APP_PORT}"]
