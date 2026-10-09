import os
import psycopg


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "bucks_r_us"),
        user=os.getenv("POSTGRES_USER", "bru_user"),
        password=os.environ["POSTGRES_PASSWORD"]
    )