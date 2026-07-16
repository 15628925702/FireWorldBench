# P5 Formal Run Approval Request S072

Current state: `BLOCKED_FORMAL_PREFLIGHT`.

## Evidence already available

- Real D01/D02/D03 canonical pipeline outputs exist for research/planning.
- A balanced 18-sample train/dev quasi-experiment pack exists.
- `deepseek-chat` and `deepseek-v4-pro` with thinking disabled passed guarded
  probes on all nine task slots.
- Runner guards, raw-response hashing, schema validation and budget prechecks
  are implemented.

## Decisions still requiring the project owner

1. **Formal data scope**: obtain/approve authoritative permission for the core
   D01/D02 data, or explicitly redefine the formal paper dataset to a source set
   with sufficient rights and evidence.
2. **Formal model matrix**: approve exact models. The current two validated
   DeepSeek slots are engineering-ready but same-provider-only and therefore a
   weak A-conference comparison by themselves.
3. **Credentials/runtime**: provide credentials through environment variables
   only, or approve/download exact local checkpoints and runtime dependencies.
4. **Cost ceiling**: approve a numeric pilot and main-run cap after formal sample
   count and current provider pricing are frozen.
5. **Expert calibration**: provide two qualified raters or approve a reduced
   task scope that removes unsupported expert gold.

## Explicit authorization format

```text
I approve the following formal-run preparation only:
- data sources: [...]
- model IDs and exact versions: [...]
- credential mechanism: environment variables only
- pilot cost ceiling: USD [...]
- main cost ceiling: USD [...]
- repetitions: [...]
- expert raters / reduced scope: [...]

Do not start the main run until the regenerated preflight status is READY.
```

No formal run should start from this document alone; all machine gates must also
pass.
