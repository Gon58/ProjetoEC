FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip
RUN pip install -e .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
