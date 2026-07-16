# ESL Academic Writing Coach

An AI writing coach that helps ESL college students revise their essays into clearer, more natural academic English — in their own voice. Built with a multi-agent `LangGraph` pipeline on `FastAPI`, with a `React + Vite` frontend.

This is a **writing coach, not an AI-detector bypass tool**. The product is scoped around academic integrity: it helps students understand *why* a passage reads as generic or robotic and gives them revision suggestions to fix it themselves, rather than generating a finished essay for them.

## Why this exists

International and ESL students often lose points not because their ideas are weak, but because their English doesn't yet sound natural in an academic register — and AI writing tools built for native speakers don't explain *why* a sentence feels off. This project is a focused coaching pipeline aimed at that gap: clarity feedback, voice preservation, and academic integrity guidance in one flow.

## Coaching Pipeline (LangGraph)

Each essay passes through a chain of specialized agents rather than a single prompt:

```
Policy Guard        → blocks cheat requests, redirects to ethical use
Writing Analyzer     → finds AI-like patterns, vague claims, robotic tone
ESL Voice Coach      → preserves the student's voice, suggests natural phrasing
Revision Suggestion  → sentence/paragraph-level fixes, not a full rewrite
Academic Integrity   → confirms the student's ideas remain central, drafts an optional AI-use disclosure
```

## Features

- **Coaching analysis** (`/api/coach`) — assignment-type- and level-aware feedback: generic/AI-like sections, unnatural phrasing, missing personal examples, clarity and structure issues, targeted revision suggestions
- **Sentence Rewriter** — an assistive rewrite pass for flagged sentences, gated behind credits so it stays a *supplement* to coaching feedback, not a replacement for it
- **Academic integrity guardrails** — policy guard blocks cheat-style prompts and redirects toward ethical revision; every session can generate an optional AI-use disclosure statement
- Assignment-type and writing-level aware: Discussion post / Reflection essay / Research essay / Personal statement / General academic paragraph, across ESL Beginner / Intermediate / Advanced
- Free tier: `2 runs/day/IP`, `300-word` cap — the 3rd attempt routes to upgrade/billing instead of failing silently
- `1200-word` input ceiling with a live counter in the UI
- Tiered billing (Starter / Student Plus / Pro) with credit costs that scale by feedback depth (`basic` → `deep` → `full review`)

## Project Structure

- `backend/app/main.py` — FastAPI entrypoint, routes, auth, SPA fallback
- `backend/app/graphs.py` — LangGraph orchestration for the coaching and rewriter flows
- `backend/app/services/coaching.py` — policy guard, writing analyzer, ESL voice coach, integrity checks (OpenAI-backed with a heuristic fallback when no API key is set)
- `backend/app/services/billing.py` — in-memory account and credit management
- `backend/app/services/rate_limits.py` — per-IP daily free-tier limiting
- `frontend/` — React + Vite client
- `tests/` — backend test suite (runs fully offline, no API key required)

## Run

1. Install Python dependencies from `pyproject.toml`
2. Install frontend dependencies in `frontend/`
3. Run the API server:

```bash
uvicorn main:app --reload
```

4. Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

If you build the frontend into `frontend/dist`, FastAPI also serves the compiled app.

## Tests

```bash
pytest
```

Runs fully offline — `OPENAI_API_KEY` is optional; coaching falls back to a heuristic analyzer when it's unset.

## Demo Billing States

Use the `X-User-Id` header to simulate different billing states during API testing.

- `demo-free` — free account, `0` credits
- `demo-starter` — `20,000` credits
- `demo-plus` — `60,000` credits
- `demo-pro` — `150,000` credits
