import os
import sys

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def connect():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def search(question, size=1000, top_k=3):
    model = SentenceTransformer(MODEL_NAME)
    vec = model.encode([QUERY_PREFIX + question], normalize_embeddings=True)[0]
    vec_text = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source, chunk_id, content, 1 - (embedding <=> %s::vector) AS score
        FROM doc_chunks
        WHERE chunk_size = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (vec_text, size, vec_text, top_k),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python backend/search.py "your question" [chunk_size]')
    question = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    print("Question:", question)
    for rank, (source, chunk_id, content, score) in enumerate(search(question, size), 1):
        print(f"\n=== Result {rank} | score {score:.3f} | {source} chunk {chunk_id} ===")
        print(content[:600])


if __name__ == "__main__":
    main()
