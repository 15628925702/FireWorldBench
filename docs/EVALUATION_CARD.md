# Evaluation Card

## Primary Evaluation

- Main evidence: FDS Core v3.3.1 only.
- Overall: unweighted mean of all nine FDS task scores.
- External sources: separate report nodes, never FDS Overall.
- Primary scorer: deterministic exact/component accuracy.
- LLM judge: prohibited from the main leaderboard.

## Input and Output Controls

- Public test questions have redacted answers.
- Private gold is never passed to model runners.
- Predictions require QA ID, task ID, answer, confidence and evidence.
- Missing or malformed predictions score as failures, never inferred answers.

## Model Status

- Fixed intended model: `openai/gpt-4o-mini` via OpenAI-compatible API.
