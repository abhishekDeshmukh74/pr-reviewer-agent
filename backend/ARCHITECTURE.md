# Backend Architecture

## Overview

The backend is a **FastAPI** application that drives an AI-powered pull-request review pipeline built with **LangGraph** and **LangChain**. It exposes a REST/SSE API consumed by the React frontend, fetches PR diffs from GitHub when given a URL, and runs a deterministic multi-node agent graph that produces categorised review findings, a suggested patch, and an overall summary.

```
Client
  │
  ├── POST /api/review          → full result (JSON)
  └── POST /api/review/stream   → streaming result (SSE)
           │
      FastAPI app  (app/main.py)
           │
      review_graph  (LangGraph StateGraph)
           │
      ┌────┴────────────────────────────────────────────────┐
      │  guardrail_check → parse_diff → review_bugs          │
      │    → review_security → review_performance             │
      │    → review_readability → review_tests                │
      │    → generate_patch → generate_summary → END          │
      └─────────────────────────────────────────────────────┘
           │
      Groq LLM  (llama-3.3-70b-versatile via OpenAI-compat API)
```

---

## Directory Layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS, /health, /api/review, /api/review/stream
│   ├── config.py        # Pydantic-settings config (env vars, .env)
│   ├── agent/
│   │   ├── graph.py     # LangGraph StateGraph definition & compilation
│   │   ├── nodes.py     # All graph node functions
│   │   ├── prompts.py   # LLM prompt templates and per-category configs
│   │   ├── state.py     # AgentState TypedDict
│   │   └── tools.py     # LangChain @tool utilities (not yet wired into graph)
│   ├── models/
│   │   └── schemas.py   # Pydantic request/response schemas
│   └── services/
│       ├── diff_parser.py  # Raw unified-diff → structured file list
│       └── github.py       # GitHub API: parse PR URL, fetch diff over httpx
├── tests/
│   ├── test_api.py
│   ├── test_diff_parser.py
│   └── test_github.py
├── requirements.txt
└── Dockerfile
```

---

## Configuration (`app/config.py`)

| Setting | Env Var | Default | Purpose |
|---|---|---|---|
| `groq_api_key` | `GROQ_API_KEY` | `""` | Groq API key |
| `github_token` | `GITHUB_TOKEN` | `""` | Optional GitHub PAT for private repos / higher rate limits |
| `groq_model` | `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model name |
| `max_diff_lines` | `MAX_DIFF_LINES` | `3000` | Guardrail threshold |

Settings are loaded once via `@lru_cache` and read from a `.env` file or real environment variables using **pydantic-settings**.

---

## API Endpoints (`app/main.py`)

### `GET /health`
Health-check used by Docker / load-balancer probes. Returns `{"status": "ok"}`.

### `POST /api/review`
Accepts a `ReviewRequest` body, runs the full agent graph with `ainvoke`, and returns a complete `ReviewResult` JSON object when the pipeline finishes.

### `POST /api/review/stream`
Same inputs as `/api/review` but uses `astream` and returns a **Server-Sent Events** stream. Each SSE event has a named `event:` field:

| Event | Payload | When emitted |
|---|---|---|
| `status` | `{node, message}` | After each graph node completes |
| `review` | `CategoryReview` | When a reviewer node produces findings |
| `patch` | `{patch}` | When `generate_patch` finishes |
| `summary` | `{overall_summary, test_suggestions}` | When `generate_summary` finishes |
| `done` | `{}` | Pipeline complete |

---

## Agent Graph (`app/agent/`)

### State (`state.py`)

`AgentState` is a `TypedDict` that flows through every node:

| Field | Type | Description |
|---|---|---|
| `raw_diff` | `str` | Original unified diff from the client |
| `parsed_files` | `list[dict]` | Structured file-change list from `parse_diff` |
| `reviews` | `list[CategoryReview]` | Accumulated per-category findings (append-only via `operator.add`) |
| `suggested_patch` | `str` | Unified diff patch proposed by `generate_patch` |
| `overall_summary` | `str` | 2–3 sentence summary from `generate_summary` |
| `test_suggestions` | `str` | Test recommendations from `generate_summary` |
| `status` | `str` | Latest human-readable status message (used for SSE) |

### Graph (`graph.py`)

The graph is a **sequential pipeline** (not parallel) to stay within Groq free-tier TPM limits:

```
guardrail_check
      │
  parse_diff
      │
  review_bugs
      │
 review_security
      │
review_performance
      │
review_readability
      │
  review_tests
      │
generate_patch
      │
generate_summary
      │
     END
```

### Nodes (`nodes.py`)

| Node | Function | What it does |
|---|---|---|
| `guardrail_check` | `guardrail_check` | Validates diff is non-empty and ≤ 3 000 lines |
| `parse_diff` | `parse_diff_node` | Calls `diff_parser.parse_diff`, stores structured file list |
| `review_bugs` | `_make_category_reviewer("bugs")` | LLM review for logic errors & incorrect API usage |
| `review_security` | `_make_category_reviewer("security")` | LLM review for injection, auth flaws, secrets, SSRF |
| `review_performance` | `_make_category_reviewer("performance")` | LLM review for N+1 queries, memory leaks, blocking calls |
| `review_readability` | `_make_category_reviewer("readability")` | LLM review for naming, duplication, documentation |
| `review_tests` | `_make_category_reviewer("tests")` | LLM review for test coverage gaps |
| `generate_patch` | `generate_patch` | LLM produces a unified diff fixing critical/warning issues |
| `generate_summary` | `generate_summary` | LLM writes overall summary + test suggestions as JSON |

`_make_category_reviewer` is a factory that creates the five reviewer nodes from `CATEGORY_CONFIGS` in `prompts.py`, keeping per-category prompt logic centralised.

All LLM calls go through `_invoke_with_retry`, which handles Groq `429 rate_limit_exceeded` responses by reading the `retry-after` hint from the error message and sleeping accordingly (up to 6 retries).

### Prompts (`prompts.py`)

| Constant | Used by |
|---|---|
| `CATEGORY_REVIEW_PROMPT_TEMPLATE` | All five reviewer nodes |
| `CATEGORY_CONFIGS` | Factory to configure each reviewer |
| `PATCH_PROMPT` | `generate_patch` node |
| `SUMMARY_PROMPT` | `generate_summary` node |
| `DIFF_PARSER_PROMPT` | Reserved (not currently used; diff parsing is rule-based) |

### Tools (`tools.py`)

Utility `@tool` functions defined for potential use with a tool-calling agent:

| Tool | Purpose |
|---|---|
| `count_lines` | Count `+`/`-` lines in a diff |
| `detect_languages` | Map file extensions to language names |
| `extract_function_names` | Regex-extract function names from a diff |
| `validate_json` | Check whether a string is valid JSON |

These are not wired into the current graph nodes (nodes call the LLM directly).

---

## Services (`app/services/`)

### `diff_parser.py`

`parse_diff(raw_diff: str) -> list[dict]`

Iterates over lines of a unified diff, tracking `diff --git` headers to build per-file records with keys: `filename`, `language`, `additions`, `deletions`, `patch`. Language is inferred from file extension. No third-party library dependency.

### `github.py`

`fetch_pr_diff(pr_url: str) -> str`

1. `parse_pr_url` extracts `owner`, `repo`, `pr_number` from the URL via regex.
2. Makes an async `httpx` GET to `https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}` with `Accept: application/vnd.github.v3.diff`.
3. Attaches a `Bearer` token from settings if `GITHUB_TOKEN` is set.

---

## Data Models (`app/models/schemas.py`)

```
ReviewRequest          → input body for /api/review and /api/review/stream
  diff: str            ← raw git diff (mutually exclusive with pr_url)
  pr_url: str          ← GitHub PR URL

ReviewResult           → full response body
  categories: list[CategoryReview]
  suggested_patch: str
  overall_summary: str
  test_suggestions: str

CategoryReview
  category: str
  issues: list[ReviewIssue]
  summary: str

ReviewIssue
  file: str
  line: int | None
  severity: "critical" | "warning" | "info"
  title: str
  description: str
  suggestion: str

FileChange             → internal diff parse result (not in API response)
  filename, language, additions, deletions, patch
```

---

## LLM Integration

The backend uses **Groq** as its LLM provider via the OpenAI-compatible REST API (`https://api.groq.com/openai/v1`). The `ChatOpenAI` client from `langchain-openai` is pointed at Groq's base URL. The model defaults to `llama-3.3-70b-versatile` (configurable).

All LLM calls expect responses in **raw JSON** (no markdown fences). `_safe_parse_json` strips any accidental fences before parsing.

---

## Error Handling

| Scenario | Handling |
|---|---|
| Empty diff | `guardrail_check` raises `ValueError` → HTTP 422 |
| Diff > 3 000 lines | `guardrail_check` raises `ValueError` → HTTP 422 |
| Invalid GitHub PR URL | `parse_pr_url` raises `ValueError` → HTTP 400 |
| GitHub API failure | `httpx` raises → HTTP 400 |
| LLM JSON parse error | `_safe_parse_json` returns `None`; node emits empty `CategoryReview` with error summary |
| Groq 429 rate limit | `_invoke_with_retry` sleeps & retries up to 6 times |
| Uncaught agent error | HTTP 500 with detail string |

---

## Runtime

- **Entry point**: `uvicorn app.main:app --reload --port 8000`
- **Docker**: `backend/Dockerfile` — Python 3.12 slim image
- **Virtual env**: `.venv/` at `backend/.venv/`
- **Dependencies**: `backend/requirements.txt`
