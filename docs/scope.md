# Scope Document

## Problem
Analysts and business teams spend too much time finding and verifying facts in long financial documents and in databases.

## What we are building (in scope)
- Answer questions over public filings, with citations to the source
- Answer data questions using a read-only SQL tool
- Say "I don't have enough information" when the sources don't support an answer
- Automated evaluation that scores answers on every code change
- Docker, CI/CD, Terraform, and deployment on AWS
- Logging and cost tracking
- A simple, clean web interface
- A runbook and prompt library for non-technical users

## What we are NOT building (out of scope, for now)
- Real client or confidential data
- User accounts and permissions
- Model fine-tuning
- Mobile app

## Success measures
- Evaluation score: [target to be set in Phase 4]
- Pilot users: at least 3
- Cost per question: [measured in Phase 8]

## Scope change log
| Date | Change | Reason |
|------|--------|--------|
