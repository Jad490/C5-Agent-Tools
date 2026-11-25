# Live agent verification

Verified on November 1, 2026 using the OpenAI Agents SDK, the FastMCP stdio server,
and **Gemini 3.1 Flash-Lite** through Google's OpenAI-compatible endpoint.

Command executed:

```bash
python -u -m campus_mcp.agent --demo --db runtime/gemini-flash-lite-01.sqlite3
```

The agent discovered exactly `search_catalog`, `save_book`, and `build_reading_list`.
It selected tools from their schemas in response to the four natural-language
requests. Each result returned through the MCP client to the model, which then
produced its final response.

| Scenario | Observed MCP call | Observed result |
|---|---|---|
| Data | `search_catalog(query="agents", limit=2)` | B001 and B003; total_matches=2; isError=False |
| Action | `save_book(book_id="B001", list_name="demo_agent")` | status=saved; isError=False |
| Orchestration | `build_reading_list(query="agents", list_name="demo_agent", limit=2)` | Data lookup followed by saves; B001 already_saved, B003 saved; newly_saved=1, already_saved=1; isError=False |
| Predictable failure | `save_book(book_id="B999", list_name="demo_agent")` | isError=True; BOOK_NOT_FOUND: B999 is not in the demo catalog |

The final assistant response for the failure was:

> The request to save book B999 to `demo_agent` failed with the error: **BOOK_NOT_FOUND**. The system reported that B999 is not in the demo catalog.

The agent printed:

```text
[DEMO VERIFIED] All three tools routed correctly; failure surfaced as an error.
```

The originally configured Gemini 3.8 Flash timed out on generation requests.
Gemini 3.1 Flash-Lite answered a simple diagnostic prompt successfully, then
completed all four live agent scenarios. It was the Gemini model used for that run. The November 25 recording uses the
currently responsive gemini-flash-lite-latest alias; see recorded-demo.txt.
This record contains no API key. The completed 6:40 screencast is linked in SUBMISSION.md.
