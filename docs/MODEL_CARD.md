# Model Card

## Fixed Interface

- Model identifier: `openai/gpt-4o-mini`.
- Endpoint contract: OpenAI-compatible `chat/completions`.
- Temperature: 0; seed, timeout, retry count and prompt hash are recorded.
- Raw responses and parse failures are retained outside result summaries.

## Result Status

No paid-model result is reported. The authorized API smoke request returned HTTP 403.
This is a runner authorization failure, not a model score. Any future run must retain
the run manifest, raw responses, predictions, failures and scorer output.

