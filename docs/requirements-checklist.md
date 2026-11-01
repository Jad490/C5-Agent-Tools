# PDF requirement mapping

Source: `C5 - Agent Tools.pdf`, supplied by the student, pages 1–3.
The PDF specifies deliverables and rules; it does not provide a numerical grading
rubric. This mapping covers the supplied requirements, without promising a grade.

| Requirement | Implementation / evidence | State |
|---|---|---|
| Read the specified Hugging Face MCP article | `docs/summary.md`, references 1–2; excerpt and linked full article read | Complete |
| Explore an existing MCP server | Reference Fetch README and Python source; inspected commit linked in summary | Complete |
| 300–400 word summary | `docs/summary.md`, 361 whitespace-delimited words in the four paragraphs, including citation markers | Complete |
| Explain Host, Client, Server relationships | Summary paragraph 2 and README architecture diagram | Complete |
| Critique existing server using tool design principles | Summary paragraphs 3–4: scope, schemas, defaults, output modes, description and repeatability | Complete |
| Choose a coherent theme | Campus reading-list assistant | Complete |
| Exactly three tools: one Data, one Action, one Orchestration | Only three `@mcp.tool` registrations in `campus_mcp/server.py`; discovery asserted by tests and host | Complete |
| Data retrieves without changing state | `LibraryService.search_catalog`; tests assert unchanged catalog and absent database | Complete |
| Action changes something | `LibraryService.save_book`; SQLite insert; restart persistence integration test | Complete |
| Orchestration coordinates the other two | `LibraryService.build_reading_list` calls shared Data and Action implementations; order tested | Complete |
| Clear descriptions, typed inputs, typed/documented outputs | Tool docstrings, annotated constraints and `models.py`; schema discovery test | Complete |
| Single-purpose tools | Read catalog / persist one entry / coordinate topic workflow | Complete |
| Predictable failures with clear errors | Invalid query, unknown ID, no workflow matches, catalog/storage failure; MCP error tests | Complete |
| FastMCP server using `@mcp.tool` | `campus_mcp/server.py` | Complete |
| `@mcp.resource` for any lookups exposed as resources | No resources exposed; lookup is the required callable Data tool; tests assert empty resource list | Applicable condition addressed |
| OpenAI Agents SDK agent and MCP Host/Client | `Agent`, `Runner`, `MCPServerStdio` in `agent.py`; live Gemini 3.1 Flash-Lite demo verified | Complete |
| Tests or interactive scripts including failures | `tests/`, `scripts/smoke_mcp.py`, offline transcript in `evidence/` | Complete |
| Latest FastMCP and Agents SDK | Installed latest stable resolved versions: 4.1.4 and 0.24.0; frozen dependencies in `requirements.lock` | Complete at setup date |
| Configuration and setup instructions | README and `.env.example` | Complete |
| Reflection: one or two paragraphs | `docs/reflection.md`, exactly two paragraphs | Complete |
| 5–7 minute screencast introducing categories | `docs/screencast.md` targets 6:15 | Recording pending |
| Live agent → client → server → agent round trip for all tools | Full four-scenario live demo passed; see `evidence/live-demo.md` | Live run complete; recording pending |
| Discuss challenges and how addressed | Screencast narration: side-effect boundary, duplicate saves, partial workflow failure | Prepared; recording pending |
| Share code repository and video in submission | Repository linked in `SUBMISSION.md` | Code published privately; grader access and video URL pending |

The working code, local tests, and live Gemini verification are complete. The
recording, grader access to the private repository, student name/ID, and a video
link are still required before the entire assignment is ready to submit.
