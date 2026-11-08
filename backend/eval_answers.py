import json
import os
import random
import re

import anthropic
import psycopg2
from dotenv import load_dotenv

from agent import run_agent

load_dotenv()
JUDGE_MODEL = "claude-haiku-4-5-20251001"

DATA_TESTS = [
    ("Which fund had the highest 2024 return?", ["Summit Growth Equity III"]),
    ("Which fund is the largest by fund size?", ["Harbor Private Equity IX"]),
    ("How many funds are in the database?", ["6", "six"]),
    ("Which fund had the lowest 2023 return?", ["Atlas Real Estate Partners I"]),
    ("What was the NAV of Keystone Infrastructure Fund I in 2024?", ["5,700", "5700"]),
]

REFUSAL_TESTS = [
    "What is the best pizza restaurant in Chicago?",
    "What will the weather be in Paris tomorrow?",
    "Who won the 2022 World Cup?",
    "What was Apple's revenue last year?",
    "What is the home address of Blackstone's chief executive?",
    "Write me a poem about the ocean.",
]


def is_refusal(text):
    return "enough information" in text.lower()


def connect():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def judge(client, question, answer, source_text):
    msg = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=200,
        system=(
            "You check an answer against numbered sources. "
            'Reply with JSON only: {"supported": true or false, "reason": "one short sentence"}. '
            "supported is true only if every factual claim in the answer is backed by the sources."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Question: {question}\n\nAnswer: {answer}\n\nSources:\n{source_text}",
            }
        ],
    )
    text = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"supported": False, "reason": "judge reply could not be read"}


def main():
    client = anthropic.Anthropic()
    conn = connect()
    cur = conn.cursor()
    report = {"data": [], "refusal": [], "filing": []}

    print("--- Fund data questions ---")
    for q, keys in DATA_TESTS:
        text, sources, tools, t_in, t_out = run_agent(q)
        ok = any(k.lower() in text.lower() for k in keys)
        report["data"].append({"question": q, "ok": ok, "answer": text})
        print("PASS" if ok else "FAIL", "|", q)

    print("\n--- Refusal questions ---")
    for q in REFUSAL_TESTS:
        text, sources, tools, t_in, t_out = run_agent(q)
        ok = is_refusal(text)
        report["refusal"].append({"question": q, "ok": ok, "answer": text})
        print("PASS" if ok else "FAIL", "|", q)

    print("\n--- Filing questions ---")
    generated = json.load(open("eval/questions_generated.json"))
    random.seed(7)
    sample = random.sample(generated, min(15, len(generated)))
    for item in sample:
        q = item["question"]
        text, sources, tools, t_in, t_out = run_agent(q)
        if is_refusal(text):
            report["filing"].append({"question": q, "refused": True, "answer": text})
            print("REFUSED |", q)
            continue
        cited = bool(re.search(r"\[\d+\]", text))
        source_text = ""
        for i, (source, chunk_id, score) in enumerate(sources, 1):
            cur.execute(
                "SELECT content FROM doc_chunks WHERE source = %s AND chunk_size = 1000 AND chunk_id = %s",
                (source, chunk_id),
            )
            row = cur.fetchone()
            source_text += f"[{i}] {row[0] if row else ''}\n\n"
        verdict = judge(client, q, text, source_text)
        report["filing"].append(
            {
                "question": q,
                "refused": False,
                "cited": cited,
                "supported": bool(verdict.get("supported")),
                "reason": verdict.get("reason", ""),
                "answer": text,
            }
        )
        print("SUPPORTED" if verdict.get("supported") else "UNSUPPORTED", "| cited" if cited else "| no citation", "|", q)
    conn.close()

    d = sum(1 for x in report["data"] if x["ok"])
    r = sum(1 for x in report["refusal"] if x["ok"])
    answered = [x for x in report["filing"] if not x["refused"]]
    s = sum(1 for x in answered if x["supported"])
    c = sum(1 for x in answered if x["cited"])
    print("\n===== SUMMARY =====")
    print(f"Fund data answers correct: {d}/{len(report['data'])}")
    print(f"Off-topic questions refused: {r}/{len(report['refusal'])}")
    print(f"Filing questions answered: {len(answered)}/{len(report['filing'])}")
    if answered:
        print(f"Answers fully supported by sources: {s}/{len(answered)}")
        print(f"Answers with citations: {c}/{len(answered)}")
    json.dump(report, open("eval/results_answers.json", "w"), indent=2)
    print("Saved: eval/results_answers.json")


if __name__ == "__main__":
    main()
