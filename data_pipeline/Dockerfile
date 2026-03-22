FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY data_pipeline /app/data_pipeline
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN cd /app/data_pipeline && pip install -e ".[dev]"

CMD ["sh", "-c", "cd /app/data_pipeline && ruff check . && pytest tests"]