FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY agents ./agents
COPY api ./api
COPY artifacts ./artifacts
COPY context ./context
COPY core ./core
COPY hardware ./hardware
COPY kernel ./kernel
COPY memory ./memory
COPY models ./models
COPY orchestrator ./orchestrator
COPY policies ./policies
COPY providers ./providers
COPY routing ./routing
COPY scripts ./scripts
COPY services ./services
COPY tasks ./tasks
COPY tests ./tests
COPY verification ./verification
COPY workers ./workers
COPY main.py xyntra_cli.py ./

RUN pip install --upgrade pip \
    && pip install ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
