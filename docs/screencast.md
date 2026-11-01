# Screencast guide — target 6 minutes 15 seconds

The PDF requires a **5–7 minute recording of the real agent using all three tools**.
Record the working terminal/editor with your narration. This guide is preparation;
neither this document nor the offline smoke transcript is the video deliverable.

## Before recording

1. Use the configured `.env` with `MODEL_PROVIDER=gemini`, your `GEMINI_API_KEY`,
   and `GEMINI_MODEL=gemini-3.1-flash-lite`. All four live demo scenarios have
   passed with this model; see `evidence/live-demo.md`. If you rehearse again, use
   `python -m campus_mcp.agent --demo --db runtime/rehearsal.sqlite3`. Each full
   demo normally makes eight model requests, so save requests for the recording.
2. Publish the repository and have its URL ready to show. Open the README,
   `campus_mcp/server.py`, `campus_mcp/service.py`, and `campus_mcp/agent.py` in an editor.
3. Open a terminal at the project root and activate `.venv`. Increase the font size
   so the call logs are legible. Keep `.env`, shell history containing secrets, and
   unrelated private windows out of view.
4. Choose an unused database filename, such as `runtime/recording-01.sqlite3`.
   Reusing a database gives `already_saved`, which is valid but changes the first-save
   demonstration. Use another filename for a retake instead of deleting data.
5. On macOS, press **Shift–Command–5**, select the recording area and microphone,
   and begin recording. Use your preferred recording tool on another OS.

## 0:00–0:40 — Introduce the project

Show the README and name all categories explicitly.

Suggested narration:

> This is my Campus Reading MCP Toolkit for C5. It uses FastMCP for the server and
> the OpenAI Agents SDK for the agent host. There are exactly three tools.
> Search catalog is the Data tool: it only retrieves information. Save book is the
> Action tool: it writes one reading-list entry to SQLite. Build reading list is
> the Orchestration tool: it coordinates lookup and saving for a topic. The catalog
> is a reproducible demonstration dataset, and its shelf labels are illustrative.

## 0:40–1:20 — Explain Host, Client, and Server

Show the README diagram, then `agent.py` and `server.py`.

> The Python agent application is the MCP Host. Inside it, MCPServerStdio manages
> the Client connection to a separate FastMCP Server process. The client discovers
> the tools and passes their schemas to the agent. The model selects a tool, the
> client sends the call over stdio, and the server returns a result or an error.
> The Agents SDK then gives that result back to the model to produce the final
> answer. The API key stays with the host.

## 1:20–2:00 — Show focused interfaces

Point to the three `@mcp.tool` registrations, input annotations, return types,
and `LibraryService.build_reading_list`.

> Each endpoint has a description, typed arguments, and a Pydantic output model.
> The lookup and save operations have separate implementations. The workflow
> calls those same implementations in order, so there is no second copy of their
> logic. It returns ordered steps and save outcomes. A unique database key prevents
> duplicate saves. An empty search is valid, but a workflow with no matches returns
> NO_MATCHES because it cannot build the requested list.

## 2:00–4:30 — Live round trips

Run:

```bash
python -m campus_mcp.agent --demo --step --db runtime/recording-01.sqlite3
```

For each scenario, read the printed request, press Enter, and let the real model
respond. Point out the **actual** selected tool, server logs, returned output, and
assistant answer. Do not describe a result before it appears.

| Approximate time | Scenario | What to highlight |
|---|---|---|
| 2:00–2:40 | Find books about agents, no save | `search_catalog`; B001 and B003; no Action log |
| 2:40–3:10 | Save B001 to `demo_agent` | `save_book`; real persistent write; `saved` on a fresh database |
| 3:10–4:00 | Find and save two books about agents | `build_reading_list`; Data log then Action logs; B001 already saved, B003 newly saved |
| 4:00–4:30 | Save unknown B999 | `save_book`; `isError=True`; `BOOK_NOT_FOUND`; assistant explains the failure |

Suggested explanations while results are on screen:

> The tool choice came from the model. The host did not hardcode a tool for this
> prompt. These arrows show the actual client call and server response.

> For the workflow, there is one MCP call. Inside the server, the orchestration
> implementation calls search and then save. B001 is already present, so it is
> reported as already saved rather than duplicated.

> B999 has the correct ID format but is absent from the catalog. The server returns
> a tool error, and the agent reports it instead of inventing success.

Wait for `[DEMO VERIFIED]`. If routing is wrong or the API fails, fix it and record
a new take; the transcript must show an actual successful round trip.

## 4:30–5:10 — Verify persistence and tests

After the demo process exits, run:

```bash
python -m scripts.show_saved --db runtime/recording-01.sqlite3
pytest -q
```

> The server process has exited, but the saved entries still exist in SQLite.
> B999 is absent, and B001 appears only once in this list. The tests cover each
> tool's success and failure cases, schemas, deterministic lookup, duplicate
> prevention, workflow call order, partial failure, and real stdio communication
> through the Agents SDK client. These local tests do not require a model key.

## 5:10–6:15 — Challenges, reflection, and repository

Show `docs/reflection.md` and your repository URL.

> The main design challenge was separating lookup from a side effect. Saving on
> every search would violate the Data tool's contract, so persistence happens only
> after an explicit save request. Another issue is a workflow failing after one
> successful save. Each save is its own transaction, so I report the completed IDs
> and make retries idempotent rather than pretending everything rolled back.
>
> Three tools suit this small use case. A fuller library application would also
> need authenticated users, list viewing and removal, and a live catalog. I kept
> those outside the MCP interface to respect the exact tool count. Next steps
> would preserve the current contracts while adding a real catalog and atomic
> batch writes. This repository contains the server, Agents SDK host, setup
> instructions, tests, reading summary, and reflection.

Keep your own wording and explain what the code actually does. Aim to finish near
6:15. Upload the recording to the platform you choose, verify it plays without
requesting access, and put the repository and video links in `SUBMISSION.md`.
