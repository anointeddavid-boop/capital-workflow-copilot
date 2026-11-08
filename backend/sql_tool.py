import os
import re
import sys

import anthropic
import psycopg2
from dotenv import load_dotenv

load_dotenv()
MODEL = "claude-haiku-4-5-20251001"

SCHEMA = """
Table funds(fund_id, fund_name, strategy, vintage_year, fund_size_usd_millions)
Table fund_performance(perf_id, fund_id, report_year, net_irr_percent, nav_usd_millions, distributions_usd_millions)
fund_performance.fund_id points to funds.fund_id.
Years in fund_performance: 2022, 2023, 2024. All amounts in USD millions.
"""

WRITE_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do)\b"
)


def connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        user=os.getenv("POSTGRES_RO_USER"),
        password=os.getenv("POSTGRES_RO_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
        options="-c statement_timeout=5000",
    )


def write_query(client, question):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=(
            "You write one PostgreSQL SELECT query for the schema below. "
            "Reply with the SQL only, no explanation, no code fences. "
            "If the question cannot be answered with a SELECT on this schema, reply exactly: NO_QUERY\n"
            + SCHEMA
        ),
        messages=[{"role": "user", "content": question}],
    )
    sql = msg.content[0].text.strip()
    return sql.replace("```sql", "").replace("```", "").strip()


def check_query(sql):
    clean = sql.strip().rstrip(";").strip()
    low = clean.lower()
    if low == "no_query":
        return None, "The question can't be answered from the fund tables."
    if ";" in clean:
        return None, "Blocked: more than one statement."
    if not low.startswith("select"):
        return None, "Blocked: only SELECT queries are allowed."
    if WRITE_WORDS.search(low):
        return None, "Blocked: the query contains a write keyword."
    return clean, None


def run_query(sql):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM ({sql}) AS t LIMIT 50")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return cols, rows


def ask_data(question):
    client = anthropic.Anthropic()
    sql = write_query(client, question)
    clean, problem = check_query(sql)
    if problem:
        return {"sql": sql, "answer": problem, "rows": []}
    cols, rows = run_query(clean)
    table = [dict(zip(cols, r)) for r in rows]
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system="Answer the question in plain English using only the query result given. Keep it short.",
        messages=[
            {"role": "user", "content": f"Question: {question}\nQuery result: {table}"}
        ],
    )
    return {"sql": clean, "answer": msg.content[0].text, "rows": table}


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python backend/sql_tool.py "your question"')
    result = ask_data(sys.argv[1])
    print("SQL:", result["sql"])
    print("Rows:", len(result["rows"]))
    print("\nAnswer:\n" + result["answer"])


if __name__ == "__main__":
    main()
