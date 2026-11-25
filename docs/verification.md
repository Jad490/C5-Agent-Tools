# Verification evidence

Verified locally on November 1 and November 25, 2026, with Python 3.12.16, FastMCP 4.1.4,
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
- Live Gemini 3.1 Flash-Lite demo — all four scenarios passed: Data, Action,
  Orchestration, and the expected unknown-book error. The model chose the correct
  tool in every scenario and produced final responses from the MCP replies.
  See [the observed results](../evidence/live-demo.md).

## Completed recording

The live run used the OpenAI Agents SDK with Gemini as the model provider. The
initial Gemini 3.8 Flash configuration timed out. Gemini 3.1 Flash-Lite completed
the full demo successfully on November 1. On November 25 that pinned model
returned a 503 high-demand error; gemini-flash-lite-latest passed a preflight and
all four scenarios in the final recording, and is now the configured default. The optional OpenAI provider
has configuration tests but has not been verified against the OpenAI API.

For a rehearsal or recording, use a fresh database filename:

```bash
python -m campus_mcp.agent --demo --db runtime/live-check-01.sqlite3
python -m scripts.show_saved --db runtime/live-check-01.sqlite3
```

Success requires `[DEMO VERIFIED]`, all three tools selected in the correct
scenarios, `BOOK_NOT_FOUND` for B999, and only B001/B003 saved to `demo_agent`.
The final MP4 is **6:40**, with H.264 video at 1600×900 and AAC narration. The
terminal session was captured at real wall-clock timings, and the synthetic
narration is explicitly identified. The agent exited successfully and printed
[DEMO VERIFIED]. The recorded persistence check found exactly B001 and B003;
the recorded test and lint runs passed. The video streams decode successfully,
and its audio is non-silent with a peak level below clipping. See
[evidence/recorded-demo.txt](../evidence/recorded-demo.txt) and
[evidence/video-verification.json](../evidence/video-verification.json).

The repository is public. The video and source links are in SUBMISSION.md.
