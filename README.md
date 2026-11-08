# Capital Workflow Copilot

An assistant that answers questions about a company's annual report and a small table of fund data. Every answer from the report comes with the source passage it was based on. If the tools can't support an answer, it says so instead of guessing.

I built this to practice the kind of work an AI engineer does inside a finance firm: take a slow, manual workflow (digging through long filings and databases), build something that helps, and measure whether it actually works.

## What it does

- Searches Blackstone's latest 10-K (about 1 million characters, split into 1,397 chunks) by meaning, not just keywords
- Answers questions about fund performance by writing a SQL query and running it on a read-only database user
- Uses an agent to pick the right tool for each question, or both
- Refuses questions that have nothing to do with the report or the fund data

## Data

The annual report is a real public filing from the SEC. The fund table is made up. The six funds and their numbers are fictional, so no real or confidential data is used anywhere.

## How it works

1. download_filings.py pulls the 10-K from the SEC and turns it into plain text
2. chunk_filings.py cuts it into overlapping pieces
3. embed_chunks.py turns each piece into numbers and stores them in Postgres with pgvector
4. search.py finds the pieces closest in meaning to a question
5. sql_tool.py writes and runs a read-only SQL query for fund questions
6. agent.py lets the model choose between the two tools and write a cited answer
7. api.py serves it all with FastAPI

Stack: Python, SQL, Postgres with pgvector, FastAPI, Docker, GitHub Actions, Claude (Haiku) for answers, and a small local embedding model (bge-small).

## Results so far

Chunk size test, 51 questions (does the right passage show up in the top 4 results?):

| Chunk size | Hit rate | MRR |
|---|---|---|
| 500 | 82% | 0.696 |
| 1000 | 86% | 0.717 |
| 2000 | 88% | 0.686 |

The sizes landed close together, so I kept 1000. It had the best MRR and sends less text to the model than 2000.

Answer test, after tightening the agent's rules:

| Check | Result |
|---|---|
| Fund data answers correct | 5 of 5 |
| Off-topic questions refused | 6 of 6 (was 0 of 6 before the fix) |
| Filing questions answered | 14 of 15 |
| Answers fully supported by sources | 12 of 14 |
| Answers with citations | 13 of 14 |

The first run showed the agent adding a fact from its own memory on an off-topic question. I changed its instructions and ran the test again. Both result files are in the eval folder.

## Limits

- The keyword search test undercounts, because a correct answer found in a different chunk doesn't count as a hit
- The test questions were generated from the filing by a model, so they lean toward passages that are easy to find
- The answer checker is the same model family as the agent, so it can be too kind
- 15 filing questions is a small sample, and results shift a little from run to run
- There are no user accounts or permissions, so it isn't ready for confidential data

## Run it yourself

You need Docker, Python 3.10, and an Anthropic API key. Clone the repo, then create a .env file with your own values for these settings: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_RO_USER, POSTGRES_RO_PASSWORD, SEC_USER_AGENT (your name and email), and ANTHROPIC_API_KEY.

Start everything with "docker compose up -d --build". The API listens on port 8000, with a health check at /health and questions sent to /ask. A full setup script for the database is still on the to-do list.

## Still to do

- Run the evaluation inside the pipeline so a bad change gets blocked
- Deploy to AWS with Terraform
- A simple web interface
- Cost and speed tracking
- Try it with a few real users and write up what they say
