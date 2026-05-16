import os
from typing import List, Dict, Any

import httpx
import psycopg2
import psycopg2.extras
from pymongo import MongoClient
import subprocess
import sys

from prefect import flow, task, get_run_logger

# Environment / connection defaults (containers can reach each other by service name)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "ec-project-postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
MONGO_HOST = os.getenv("MONGO_HOST", "ec-project-mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ec_project")

DEFAULT_SOURCE = os.getenv("EXTERNAL_SOURCE_URL", "https://jsonplaceholder.typicode.com/posts")


@task(retries=3, retry_delay_seconds=60, log_prints=True)
def fetch_raw(url: str = DEFAULT_SOURCE) -> List[Dict[str, Any]]:
    logger = get_run_logger()
    logger.info(f"Fetching raw data from {url}")
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    logger.info(f"Fetched {len(data) if hasattr(data,'__len__') else 'unknown'} records")
    return data


@task(log_prints=True)
def transform(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger = get_run_logger()
    logger.info("Starting transform step")
    transformed = []
    for r in records:
        # Minimal cleaning example: keep only simple fields and coerce types
        item = {"source_id": r.get("id"), "title": r.get("title"), "body": r.get("body")}
        transformed.append(item)
    logger.info(f"Transformed {len(transformed)} records")
    return transformed


@task(log_prints=True)
def load_to_postgres(records: List[Dict[str, Any]]):
    logger = get_run_logger()
    logger.info("Loading to Postgres")
    conn = None
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=POSTGRES_DB,
        )
        cur = conn.cursor()
        # Simple table create if missing
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_raw (
                id SERIAL PRIMARY KEY,
                source_id TEXT,
                data JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
            """
        )
        insert_sql = "INSERT INTO ingestion_raw (source_id, data) VALUES (%s, %s)"
        for rec in records:
            cur.execute(insert_sql, (str(rec.get("source_id")), psycopg2.extras.Json(rec)))
        conn.commit()
        logger.info(f"Inserted {len(records)} rows into Postgres")
        cur.close()
    except Exception:
        logger.exception("Postgres load failed")
        raise
    finally:
        if conn:
            conn.close()


@task(log_prints=True)
def load_to_mongo(records: List[Dict[str, Any]]):
    logger = get_run_logger()
    logger.info("Loading to MongoDB")
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    db = client.get_database(os.getenv("MONGO_DB", "ec_project"))
    coll = db.get_collection("ingestion_raw")
    # Insert many (safe for small datasets); this is an example only
    if records:
        coll.insert_many(records)
        logger.info(f"Inserted {len(records)} documents into MongoDB")
    client.close()


@task(log_prints=True, retries=1, retry_delay_seconds=60)
def run_full_pipeline_task():
    logger = get_run_logger()
    runner = "/data_pipeline/scripts/run_full_pipeline.py"
    logger.info(f"Executing full pipeline runner at {runner}")
    try:
        subprocess.run([sys.executable, runner], check=True)
        logger.info("Full pipeline runner completed successfully")
    except subprocess.CalledProcessError:
        logger.exception("Full pipeline runner failed")
        raise


@flow(name="ingestion_flow", log_prints=True)
def ingestion_flow(source_url: str = DEFAULT_SOURCE, use_runner: bool = True):
    logger = get_run_logger()
    logger.info("Starting ingestion_flow")
    if use_runner:
        # Run the existing pipeline runner script mounted at /data_pipeline
        run_full_pipeline_task.submit()
        logger.info("Dispatched full pipeline runner task; ending flow")
        return
    raw = fetch_raw.submit(source_url)
    transformed = transform.submit(raw)
    # load into both Postgres and Mongo in parallel
    load_to_postgres.submit(transformed)
    load_to_mongo.submit(transformed)
    logger.info("ingestion_flow scheduled loads")


if __name__ == "__main__":
    # quick local run for testing convenience
    ingestion_flow()
