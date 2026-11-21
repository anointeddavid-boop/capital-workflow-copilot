import os
import time

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import run_agent
from cost import estimate_cost

load_dotenv()
app = FastAPI(title="Capital Workflow Copilot")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

LOG_DDL = """
CREATE TABLE IF NOT EXISTS query_log (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    question TEXT NOT NULL,
    tools_used TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    seconds NUMERIC(8, 2) NOT NULL
)
"""


class Question(BaseModel):
    question: str


def db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def log_query(question, tools_used, t_in, t_out, cost, seconds):
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute(LOG_DDL)
        cur.execute(
            "INSERT INTO query_log (question, tools_used, tokens_in, tokens_out, cost_usd, seconds) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (question, ",".join(tools_used), t_in, t_out, cost, seconds),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Could not write the query log:", e)


@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    conn = db()
    cur = conn.cursor()
    cur.execute(LOG_DDL)
    cur.execute(
        "SELECT COUNT(*), COALESCE(AVG(seconds), 0), "
        "COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY seconds), 0), "
        "COALESCE(AVG(cost_usd), 0), COALESCE(SUM(cost_usd), 0), "
        "COALESCE(AVG(tokens_in + tokens_out), 0) FROM query_log"
    )
    n, avg_s, p95_s, avg_c, total_c, avg_tok = cur.fetchone()
    conn.commit()
    conn.close()
    return {
        "questions_logged": n,
        "avg_seconds": round(float(avg_s), 2),
        "p95_seconds": round(float(p95_s), 2),
        "avg_cost_usd": round(float(avg_c), 5),
        "total_cost_usd": round(float(total_c), 4),
        "avg_tokens_per_question": round(float(avg_tok)),
    }


@app.post("/ask")
def ask(body: Question):
    q = body.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question is empty")
    start = time.time()
    text, sources, tools_used, t_in, t_out = run_agent(q)
    seconds = round(time.time() - start, 2)
    cost = estimate_cost(t_in, t_out)
    log_query(q, tools_used, t_in, t_out, cost, seconds)
    return {
        "question": q,
        "answer": text,
        "tools_used": tools_used,
        "sources": [
            {"source": s, "chunk_id": c, "score": round(float(sc), 3)}
            for s, c, sc in sources
        ],
        "tokens_in": t_in,
        "tokens_out": t_out,
        "cost_usd": round(cost, 6),
        "seconds": seconds,
    }
