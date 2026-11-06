import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import run_agent

app = FastAPI(title="Capital Workflow Copilot")


class Question(BaseModel):
    question: str


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
