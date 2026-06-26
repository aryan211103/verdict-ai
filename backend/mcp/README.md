# MCP Tools — IBM Context Forge Wiring

## What this is

IBM Context Forge is the MCP gateway that exposes our FastAPI data functions
as MCP tools. This lets any MCP-compatible client (e.g. an IBM Granite agent)
call our endpoints as structured tools rather than raw HTTP.

## Tool definitions

`tools.py` in this directory defines the tool schemas that Context Forge reads.
Each tool maps 1-to-1 with a FastAPI endpoint:

| Tool name | Endpoint | Purpose |
|---|---|---|
| `list_shootouts` | `GET /shootouts` | All shootout matches in the data |
| `get_kick` | `GET /kicks/{kick_id}` | Single kick record |
| `get_taker_history` | `GET /takers/{taker_id}` | Taker's placement history + Wilson CI |
| `get_keeper_record` | `GET /keepers/{keeper_id}` | Keeper's save record |
| `get_pressure_stats` | `GET /stats/pressure` | Population pressure stats |

## Environment variables required

Copy `.env.example` from the repo root and fill in:
- `WATSONX_API_KEY` — IBM Cloud API key
- `WATSONX_PROJECT_ID` — watsonx.ai project ID
- `WATSONX_URL` — regional endpoint (default: us-south)

The Context Forge gateway is launched separately from the FastAPI server.
See Context Forge docs for the gateway startup command once tools.py is wired.

## Key constraint

The `get_taker_history` and `get_keeper_record` tools always return
sample size (`n`) and Wilson confidence intervals alongside any tendency.
Consumers must surface both; a tendency without its CI is not valid output.
