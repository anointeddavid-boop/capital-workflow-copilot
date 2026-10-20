import glob
import json
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

load_dotenv()
MODEL_NAME = "BAAI/bge-small-en-v1.5"
CHUNK_DIR = "data/chunks"

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS doc_chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384) NOT NULL
);
"""


def connect():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def main():
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    files = sorted(glob.glob(f"{CHUNK_DIR}/*_size{size}.json"))
    if not files:
        sys.exit(f"No chunk files found for size {size}")

    print("Loading model (first time downloads about 130 MB)...")
    model = SentenceTransformer(MODEL_NAME)
    model.max_seq_length = 512

    conn = connect()
    cur = conn.cursor()
    cur.execute(DDL)
    conn.commit()

    for path in files:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
        source = records[0]["source"]
        texts = [r["text"].replace("\x00", "") for r in records]
        print(f"Embedding {len(texts)} chunks from {source} (size {size})...")
        vectors = model.encode(
            texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True
        )
        cur.execute(
            "DELETE FROM doc_chunks WHERE source = %s AND chunk_size = %s",
            (source, size),
        )
        rows = [
            (source, size, r["chunk_id"], t, "[" + ",".join(f"{x:.6f}" for x in v) + "]")
            for r, t, v in zip(records, texts, vectors)
        ]
        execute_values(
            cur,
            "INSERT INTO doc_chunks (source, chunk_size, chunk_id, content, embedding) VALUES %s",
            rows,
            template="(%s,%s,%s,%s,%s::vector)",
            page_size=200,
        )
        conn.commit()
        print("Stored", len(rows), "chunks")

    cur.execute(
        "SELECT chunk_size, COUNT(*) FROM doc_chunks GROUP BY chunk_size ORDER BY chunk_size"
    )
    print("Rows in doc_chunks:", cur.fetchall())
    conn.close()


if __name__ == "__main__":
    main()
