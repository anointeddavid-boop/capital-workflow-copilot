import sys

import anthropic
from dotenv import load_dotenv

from search import search

load_dotenv()
MODEL = "claude-haiku-4-5-20251001"

SYSTEM = (
    "You answer questions about company filings. "
    "Use only the numbered sources you are given. "
    "After each claim, add the source number in square brackets, like [1]. "
    "If the sources do not contain the answer, reply exactly: "
    "I don't have enough information in the filings to answer that. "
    "Do not use outside knowledge."
)


def ask(question, size=1000, top_k=4):
    rows = search(question, size=size, top_k=top_k)
    sources = ""
    for i, (source, chunk_id, content, score) in enumerate(rows, 1):
        sources += f"[{i}] ({source}, chunk {chunk_id})\n{content}\n\n"
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM,
        messages=[
            {"role": "user", "content": f"Sources:\n{sources}\nQuestion: {question}"}
        ],
    )
    return msg.content[0].text, rows, msg.usage


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python backend/ask.py "your question"')
    question = sys.argv[1]
    answer, rows, usage = ask(question)
    print("Question:", question)
    print("\nAnswer:\n" + answer)
    print("\nSources used:")
    for i, (source, chunk_id, content, score) in enumerate(rows, 1):
        print(f"  [{i}] {source}, chunk {chunk_id}, match score {score:.3f}")
    print(f"\nTokens: {usage.input_tokens} in, {usage.output_tokens} out")


if __name__ == "__main__":
    main()
