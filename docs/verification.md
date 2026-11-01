# Verification evidence

Verified locally on November 1, 2026, with Python 3.12.16, FastMCP 4.1.4,
and OpenAI Agents SDK 0.24.0.

## Completed checks

- `ruff check .` — passed.
- `pytest -q` — 46 tests passed, covering all tools, failure cases, structured
  schemas, workflow order and partial failure, idempotence, provider configuration,
  real MCP stdio communication through the Agents SDK client, and the full Runner
  execution loop with an explicitly scripted model test double.
- `python -m scripts.smoke_mcp` — passed. The transcript in
  `evidence/mcp-smoke.txt` records actual server/client calls and errors, without a model.
- The required summary contains 361 whitespace-delimited words, excluding headings
  and references; the reflection contains two paragraphs.
- No API key is required by the unit tests or smoke check.

## Live checks still required

No model API key was configured during the local verification. The OpenAI agent's
live tool selection, final model responses, and optional Gemini inference have
**not** been verified. The offline test transcript is explicitly not a live agent
demo and is not the screencast deliverable.

After configuring a key, run the following with a fresh database filename:

```bash
python -m campus_mcp.agent --demo --db runtime/live-check-01.sqlite3
python -m scripts.show_saved --db runtime/live-check-01.sqlite3
```

Success requires `[DEMO VERIFIED]`, all three tools selected in the correct
scenarios, `BOOK_NOT_FOUND` for B999, and only B001/B003 saved to `demo_agent`.
Then record the 5–7 minute walkthrough using `--step`, upload the video, and add
the real repository and video URLs to `SUBMISSION.md`.
