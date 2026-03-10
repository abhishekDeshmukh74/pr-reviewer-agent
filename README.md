# PR Reviewer Agent

A monorepo containing a **React frontend** and a **Python LangGraph/LangChain backend** that reviews pull request diffs using an AI agent pipeline.

## Architecture

```
┌─────────────┐        ┌──────────────────────────────────────────┐
│  React UI   │──POST──│  FastAPI Backend                         │
│  (Vite+TS)  │◄─SSE───│                                          │
│             │        │  LangGraph Agent Pipeline:                │
│ • Paste diff│        │  ┌───────┐   ┌────────┐   ┌───────────┐ │
│ • Paste URL │        │  │ Parse │──▶│Reviewer│──▶│ Formatter │ │
│ • View      │        │  │ Diff  │   │ Agents │   │  + Patch   │ │
│   grouped   │        │  └───────┘   └────────┘   └───────────┘ │
│   results   │        │               │                          │
└─────────────┘        │      ┌────────┴────────┐                 │
                       │      ▼        ▼        ▼                 │
                       │   Bugs    Security   Perf  Readability   │
                       │   Tests                                  │
                       └──────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key (set `OPENAI_API_KEY` env var)

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env     # then edit .env with your API key
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — paste a diff or GitHub PR URL and click **Review**.

## Project Structure

```
pr-reviewer-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── agent/
│   │   │   ├── graph.py         # LangGraph agent graph
│   │   │   ├── nodes.py         # Agent node functions
│   │   │   ├── state.py         # Agent state schema
│   │   │   ├── tools.py         # Agent tools
│   │   │   └── prompts.py       # System prompts
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   └── services/
│   │       ├── diff_parser.py   # Diff parsing utilities
│   │       └── github.py        # GitHub API integration
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls |
| `GITHUB_TOKEN` | (Optional) GitHub PAT for fetching PR diffs |

## License

MIT
