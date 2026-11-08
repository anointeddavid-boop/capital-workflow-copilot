import os
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import run_agent

app = FastAPI(title="Capital Workflow Copilot")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: Question):
    q = body.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question is empty")
    start = time.time()
    text, sources, tools_used, t_in, t_out = run_agent(q)
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
        "seconds": round(time.time() - start, 2),
    }
