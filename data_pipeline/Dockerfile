FROM python:3.12-slim

WORKDIR /app

# psycopg (libpq)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# copiar código
COPY . .

# instalar deps
RUN pip install --upgrade pip
RUN pip install -e ".[dev]"

CMD ["sh", "-c", "ruff check . --fix && pytest tests"]