# Frontend Architecture

## Overview

The frontend is a **React 19 + TypeScript** single-page application built with **Vite**. It lets users submit a raw git diff or a GitHub PR URL, streams the review progress via Server-Sent Events (SSE) from the backend, and progressively renders categorised findings, a suggested patch, and an overall summary.

```
User
  │
  └── Browser (React SPA)
        │  POST /api/review/stream  (SSE)
        └──────────────────────────────→  FastAPI backend
                                          (proxied via Vite dev server)
```

---

## Directory Layout

```
frontend/
├── index.html              # Single HTML entry point
├── vite.config.ts          # Vite config (React plugin + /api proxy)
├── tsconfig.json           # TypeScript compiler config
├── package.json            # Dependencies and scripts
├── nginx.conf              # Nginx config for production Docker image
├── Dockerfile              # Multi-stage build → Nginx static file server
└── src/
    ├── main.tsx            # React DOM root render
    ├── App.tsx             # Root component — layout and state wiring
    ├── index.css           # Global styles
    ├── vite-env.d.ts       # Vite env type declarations
    ├── types/
    │   └── index.ts        # Shared TypeScript interfaces
    ├── hooks/
    │   └── useReviewStream.ts   # Core data-fetching hook (SSE)
    └── components/
        ├── DiffInput.tsx        # Input form (paste diff or enter PR URL)
        ├── StatusLog.tsx        # Live agent-progress log
        ├── ReviewResults.tsx    # Full review output container
        └── ReviewCategory.tsx   # Single category card with issues list
```

---

## Component Tree

```
App
├── DiffInput          ← submit diff text or GitHub PR URL
├── StatusLog          ← live SSE status messages during processing
└── ReviewResults      ← shown once first data arrives
    ├── overall summary + stats banner
    ├── ReviewCategory (×5)   ← one per review category streamed in
    │   └── issue cards (severity badge, title, file:line, description, suggestion)
    ├── suggested patch  (preformatted code block)
    └── test suggestions (prose)
```

---

## Data Flow

```
User fills DiffInput
       │ onSubmit(diff, prUrl)
       ▼
useReviewStream.startReview()
       │ fetch POST /api/review/stream (SSE)
       │
       ├── event: status   → append to statuses[] → StatusLog re-renders
       ├── event: review   → push CategoryReview into categories[] → ReviewResults updates
       ├── event: patch    → set suggested_patch → ReviewResults updates
       ├── event: summary  → set overall_summary + test_suggestions → ReviewResults updates
       └── event: done / stream closed → setIsLoading(false)
```

State is held entirely in `useReviewStream`. Components receive data only through props; none manage their own async state.

---

## Types (`src/types/index.ts`)

Mirrors the backend Pydantic schemas exactly:

| Interface | Fields |
|---|---|
| `ReviewIssue` | `file`, `line`, `severity` (`"critical"│"warning"│"info"`), `title`, `description`, `suggestion` |
| `CategoryReview` | `category`, `issues: ReviewIssue[]`, `summary` |
| `ReviewResult` | `categories`, `suggested_patch`, `overall_summary`, `test_suggestions` |
| `ReviewRequest` | `diff`, `pr_url` |
| `StreamStatus` | `node`, `message` |

---

## Hook: `useReviewStream` (`src/hooks/useReviewStream.ts`)

The single source of truth for all review data.

**State managed:**

| State | Type | Purpose |
|---|---|---|
| `result` | `ReviewResult \| null` | Progressively filled review output |
| `statuses` | `StreamStatus[]` | Ordered list of agent-progress messages |
| `isLoading` | `boolean` | True while the SSE stream is open |
| `error` | `string \| null` | Any HTTP or parse error |

**Key implementation details:**

- Uses the native `fetch` API with `response.body.getReader()` for streaming (no EventSource, because the request is a POST with a JSON body).
- An `AbortController` ref (`abortRef`) lets `reset()` cancel an in-flight stream.
- The SSE line parser buffers incomplete chunks, splits on `\n`, and tracks the current `event:` name before processing `data:` lines.
- `CategoryReview` objects are accumulated in a local `categories` array (outside React state) so each `setResult` call yields a complete snapshot (`[...categories]`) rather than relying on the previous-state callback pattern.
- `reset()` is called at the start of every new `startReview()` call to clear stale data.

**SSE event handling:**

| `event:` value | Action |
|---|---|
| `status` | Append `StreamStatus` to `statuses` |
| `review` | Push `CategoryReview` to local `categories`; call `setResult` with full snapshot |
| `patch` | Update `patch` local var; call `setResult` with full snapshot |
| `summary` | Update `overallSummary` and `testSuggestions`; call `setResult` |
| `done` | Set `isLoading(false)` |

---

## Components

### `App` (`src/App.tsx`)
Root layout. Renders the page header, wires `useReviewStream` to child components, and shows an error banner (with a dismiss button that calls `reset()`) when the hook reports an error.

### `DiffInput` (`src/components/DiffInput.tsx`)
Controlled form component with two modes toggled by a tab bar:

- **Paste Diff** — `<textarea>` for raw unified diff.
- **PR URL** — `<input type="url">` for a GitHub PR link.

Calls `onSubmit(diff, prUrl)` on form submission. The submit button is disabled while `isLoading` is true or while the active input field is empty.

### `StatusLog` (`src/components/StatusLog.tsx`)
Renders a list of `StreamStatus` entries showing which graph node is currently running and its status message. Shows a spinner while `isLoading` is true. Hidden entirely when there are no statuses and loading has not started.

### `ReviewResults` (`src/components/ReviewResults.tsx`)
Top-level review output container. Shown as soon as `result` is non-null (i.e., the first `review` event is received). Contains:

- A summary banner with total issue count and critical-issue count.
- One `ReviewCategory` per category in `result.categories`.
- A `<pre><code>` block for the suggested patch (hidden if empty).
- A prose paragraph for test suggestions (hidden if empty).

### `ReviewCategory` (`src/components/ReviewCategory.tsx`)
Card for a single review category. Displays the category name, issue count, a one-sentence summary, and a list of `issue-card` elements. Each issue card shows a colour-coded severity badge (`#ef4444` critical / `#f59e0b` warning / `#3b82f6` info`), the issue title, the file and line number, a description, and a suggestion.

---

## API Communication

All requests are made to `/api/*` paths. In development, Vite proxies these to `http://localhost:8000` (configured in `vite.config.ts`). In production, Nginx serves the static build and proxies `/api` to the backend container (configured in `nginx.conf`).

### Streaming endpoint: `POST /api/review/stream`

```
Request body (JSON):
  { "diff": "...", "pr_url": "..." }

Response: text/event-stream
  event: status
  data: {"node":"parse_diff","message":"Parsed 3 file(s)"}

  event: review
  data: {"category":"Bugs & Logic Errors","issues":[...],"summary":"..."}

  event: patch
  data: {"patch":"--- a/file.py\n+++ b/file.py\n..."}

  event: summary
  data: {"overall_summary":"...","test_suggestions":"..."}

  event: done
  data: {}
```

### Non-streaming endpoint: `POST /api/review`

Used as a fallback. Returns a single `ReviewResult` JSON object after the full pipeline completes. Not currently used by the frontend (the hook always uses the streaming endpoint).

---

## Build & Runtime

| Command | Purpose |
|---|---|
| `npm run dev` | Start Vite dev server at `http://localhost:5173` with HMR and `/api` proxy |
| `npm run build` | TypeScript compile + Vite production bundle → `dist/` |
| `npm run preview` | Serve the production build locally |

**Production Docker image** (`frontend/Dockerfile`): multi-stage build — Node 20 build stage produces `dist/`, then Nginx Alpine serves the static files and proxies API calls.

---

## Key Design Decisions

- **No UI component library** — styled entirely with plain CSS in `index.css`. Keeps the bundle small and avoids versioning complexity.
- **No global state manager** — `useReviewStream` is the only stateful hook; all child components are pure (props-in, UI-out).
- **Progressive rendering** — `ReviewResults` updates on every SSE event so the user sees findings as they arrive rather than waiting for the full pipeline.
- **Fetch over EventSource** — native `EventSource` only supports GET requests; the streaming endpoint requires a POST body, so the hook uses `fetch` with a `ReadableStream` reader instead.
