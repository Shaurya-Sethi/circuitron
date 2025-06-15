FROM python:3.11-slim

# Install KiCad nightly PPA (placeholder)
RUN apt-get update && apt-get install -y \
    kicad \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY pyproject.toml README.md ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
