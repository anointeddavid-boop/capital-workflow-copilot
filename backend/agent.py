import sys

import anthropic
from dotenv import load_dotenv

from search import search
from sql_tool import ask_data

load_dotenv()
MODEL = "claude-haiku-4-5-20251001"
MAX_ROUNDS = 5

SYSTEM = (
    "You help analysts with questions about Blackstone's annual report and a small "
    "table of fund data. Pick the tool that fits the question, and use both if needed. "
    "Use only what the tools return. For text from the report, cite the source number "
    "in square brackets, like [2]. For numbers from the database, write (fund database). "
    "If the tools do not give you enough to answer, say you don't have enough information. "
    "Never answer from memory."
)

TOOLS = [
    {
        "name": "search_filings",
        "description": "Search Blackstone's annual report (10-K) for passages. Use it for questions about the company, its business, risks, strategy, or fees.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "query_fund_data",
        "description": "Ask a question about the fund table: fund names, strategy, vintage year, fund size, and yearly returns, NAV and distributions for 2022 to 2024. Use it for numbers and rankings about funds.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
]


def run_agent(question):
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    sources = []
    tools_used = []
    tokens_in = 0
    tokens_out = 0

    for _ in range(MAX_ROUNDS):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=700,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        tokens_in += resp.usage.input_tokens
        tokens_out += resp.usage.output_tokens

        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return text, sources, tools_used, tokens_in, tokens_out

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            tools_used.append(block.name)
            try:
                if block.name == "search_filings":
                    rows = search(block.input["query"], size=1000, top_k=4)
                    out = ""
                    for source, chunk_id, content, score in rows:
                        sources.append((source, chunk_id, score))
                        out += f"[{len(sources)}] ({source}, chunk {chunk_id})\n{content}\n\n"
                else:
                    res = ask_data(block.input["question"])
                    out = f"SQL used: {res['sql']}\nAnswer: {res['answer']}"
            except Exception as e:
                out = f"Tool error: {e}"
            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": out}
            )
        messages.append({"role": "user", "content": results})

    return "I could not finish this question.", sources, tools_used, tokens_in, tokens_out


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python backend/agent.py "your question"')
    q = sys.argv[1]
    text, sources, tools_used, t_in, t_out = run_agent(q)
    print("Question:", q)
    print("Tools used:", tools_used)
    print("\nAnswer:\n" + text)
    if sources:
        print("\nSources:")
        for i, (source, chunk_id, score) in enumerate(sources, 1):
            print(f"  [{i}] {source}, chunk {chunk_id}, score {score:.3f}")
    print(f"\nTokens: {t_in} in, {t_out} out")


if __name__ == "__main__":
    main()
