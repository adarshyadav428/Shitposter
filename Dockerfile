FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md* ./
RUN pip install --upgrade pip && pip install -e .

# Pre-download spaCy transformer model at build time.
RUN python -m spacy download en_core_web_sm

COPY src ./src
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini ./alembic.ini

EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
