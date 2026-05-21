# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Kanban board project management app. Single user (hardcoded `user` / `password`), one board per user, runs in Docker. Features: drag-and-drop cards, inline editing, AI chat sidebar that can create/update/move/delete cards.

## Architecture

**Frontend** (`frontend/`) — Next.js App Router, static export, Tailwind v4, `@dnd-kit` for drag-and-drop.
- Served as static files by FastAPI at `/` in production.
- In dev, proxies `/api/*` to `localhost:8000` via `next.config.ts` rewrites.
- `src/lib/api.ts` — thin fetch wrapper; strips `col-`/`card-` prefixes before sending IDs to backend (frontend namespaces IDs to avoid dnd-kit collisions since SQLite auto-increments columns and cards both from 1).
- Optimistic UI: mutations update local state immediately, then fire the API call with no rollback on failure.

**Backend** (`backend/`) — FastAPI + SQLite + httpx. Module root is `backend/app/main.py`.
- `database.py` — SQLite connection, `init_db()` seeds default user/board/columns on first run. DB lives at `backend/data/kanban.db`.
- `ai.py` — OpenRouter client (`openai/gpt-oss-120b`), reads `OPENROUTER_API_KEY` from `.env`.
- `ai_chat.py` — structured AI: loads board as JSON, sends to model, parses `{"reply": "...", "actions": [...]}` response, applies create/update/move/delete actions transactionally.

**Docker** — multi-stage: Node builds the Next.js static export, Python stage runs FastAPI. Frontend `out/` is copied to `backend/app/static/`.

## Commands

### Frontend (from `frontend/`)
```bash
npm install
npm run dev          # dev server at http://127.0.0.1:3000
npm run build        # static export to out/
npm run test:unit    # Vitest
npm run test:e2e     # Playwright (starts dev server automatically)
npm run test:all
npm run test:unit -- --coverage
```

### Backend (from project root)
```bash
source backend/.venv/bin/activate
PYTHONPATH=. pytest backend/tests/ -v
PYTHONPATH=. pytest backend/tests/ -v --cov
```

Backend unit tests mock `httpx.post`; e2e tests mock `/api/ai/chat` (no real OpenRouter key needed).

### Docker (Linux)
```bash
bash scripts/start-linux.sh   # build + run at http://127.0.0.1:8000
bash scripts/stop-linux.sh    # stop + remove
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/ai/test   # live OpenRouter smoke test
```

The start script passes `--env-file .env` so `OPENROUTER_API_KEY` reaches the container.

## Key constraints

- **No rollback on errors** (MVP simplicity).
- **Ephemeral DB**: data is lost on container rebuild. Delete `backend/data/kanban.db` to reset; it regenerates on next run.
- **ID namespacing**: frontend uses `col-<n>` / `card-<n>` strings; API layer strips prefixes to numeric IDs.
- **Static files**: production routing depends on the static mount at `/` in `main.py`; this must remain the last mount.
- See `docs/PLAN.md` "Design decisions" section for the full list of architectural choices and their rationale.

## Color scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`

## Coding standards

- No over-engineering. No unnecessary defensive programming. No extra features.
- No emojis.
- When hitting issues: identify root cause with evidence before fixing.
