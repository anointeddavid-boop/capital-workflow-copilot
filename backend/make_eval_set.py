import json
import os
import re
import sys

import anthropic
import psycopg2
from dotenv import load_dotenv

load_dotenv()
MODEL = "claude-haiku-4-5-20251001"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

SYSTEM = (
    "You write test questions for a search system. You get one passage from a company "
    "annual report. Write one specific question that this passage answers and that makes "
    "sense on its own, so never say 'the passage' or 'this text'. Also copy one exact phrase "
    "of 3 to 6 words from the passage that is central to the answer, character for character. "
    'Reply with JSON only: {"question": "...", "phrase": "..."}'
)

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    dbname=os.getenv("POSTGRES_DB"),
)
cur = conn.cursor()
cur.execute(
    "SELECT chunk_id, content FROM doc_chunks WHERE chunk_size = 1000 "
    "AND length(content) > 700 ORDER BY random() LIMIT %s",
    (N * 4,),
)
rows = cur.fetchall()
conn.close()

norm = lambda s: " ".join(s.lower().split())
client = anthropic.Anthropic()
out = []
for chunk_id, content in rows:
    if len(out) >= N:
        break
    if len(re.findall(r"[A-Za-z]", content)) < 500:
        continue
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    text = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
    except Exception:
        continue
    q = data.get("question", "").strip()
    phrase = data.get("phrase", "").strip()
    if q and len(phrase.split()) >= 3 and norm(phrase) in norm(content):
        out.append({"question": q, "keywords": [phrase], "from_chunk": chunk_id})

json.dump(out, open("eval/questions_generated.json", "w"), indent=2)
print("Generated questions:", len(out))
for item in out[:10]:
    print("-", item["question"], "| phrase:", item["keywords"][0])
